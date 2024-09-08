#!/bin/python3

import json
import argparse
import requests
import sys
import re
import warnings
from requests.auth import HTTPBasicAuth
import jsonpath_ng.ext as jsonpath_ng
from antlr4 import *
from ConfigLexer import ConfigLexer
from ConfigParser import ConfigParser
from ConfigJSONPrinter import ConfigJSONPrinter

def load_config(config_file):
    if config_file is None:
        config_file="config.json"
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Config file '{config_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in config file '{config_file}'.")
        sys.exit(1)

def make_request(config, method, endpoint, data=None):
    url = f"{config['url']}/api/{endpoint}"
    try:
        if method == 'GET':
            response = requests.get(
                url,
                auth=HTTPBasicAuth(config['api_key'], config['api_secret']),
                verify=config.get('verify_ssl', True)
            )
        elif method in ['POST', 'PUT']:
            response = requests.post(
                url,
                auth=HTTPBasicAuth(config['api_key'], config['api_secret']),
                verify=config.get('verify_ssl', True),
                json=data
            )
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error making request to OPNsense: {e}")
        sys.exit(1)

def get_opnsense_version(config):
    data = make_request(config, 'GET', 'core/firmware/status')
    return data.get('product_version', 'Unknown')

def get_kea_dhcpv4_config(config):
    return make_request(config, 'GET', 'kea/dhcpv4/get')

def set_kea_dhcpv4_config(config, dhcp_config):
    return make_request(config, 'POST', 'kea/dhcpv4/set', data=dhcp_config)

def search_dhcpv4_subnets(config):
    return make_request(config, 'GET', 'kea/dhcpv4/searchSubnet')

def search_kea_dhcpv4_reservations(config):
    return make_request(config, 'GET', 'kea/dhcpv4/searchReservation')

def add_kea_dhcpv4_reservation(config, reservation):
    return make_request(config, 'POST', 'kea/dhcpv4/addReservation', data=reservation)

def add_dhcpv4_subnet(config, subnet_info):
    endpoint = 'kea/dhcpv4/addSubnet'
    return make_request(config, 'POST', endpoint, data=subnet_info)

def sanitize_hostname(hostname):
    """
    Converts the hostname to lowercase and sanitizes it to ensure it contains
    only valid characters for a DNS name.

    Valid characters are:
    - Lowercase letters (a-z)
    - Digits (0-9)
    - Hyphens (-)
    
    The hostname cannot start or end with a hyphen, and cannot be longer than 63 characters.
    If the sanitized hostname is empty, it returns 'host'.

    :param hostname: The original hostname string
    :return: Sanitized lowercase hostname
    """
    # Convert to lowercase
    hostname = hostname.lower()

    # Replace invalid characters with hyphens
    sanitized = re.sub(r'[^a-z0-9-]', '-', hostname)

    # Remove leading and trailing hyphens
    sanitized = sanitized.strip('-')

    # Replace multiple consecutive hyphens with a single hyphen
    sanitized = re.sub(r'-+', '-', sanitized)

    # Truncate to 63 characters if necessary
    sanitized = sanitized[:63]

    # If the sanitized hostname is empty, use 'host'
    if not sanitized:
        sanitized = 'host'

    return sanitized

def map_ar7_ethinterface_to_kea_subnet_info(input_data):
    # Calculate network address and CIDR notation
    ip_parts = input_data['ipaddr'].split('.')
    netmask_parts = input_data['netmask'].split('.')
    network_parts = [str(int(ip_parts[i]) & int(netmask_parts[i])) for i in range(4)]
    network_address = '.'.join(network_parts)
    cidr = sum([bin(int(x)).count('1') for x in netmask_parts])
    
    description = ""
    if input_data['name'] == "eth0":
        description = "LAN interface migrated from fritzbox"
    elif input_data['name'] == "eth0:0":
        description = "Fallback interface migrated from fritzbox"
    elif input_data['name'] == "wlan":
        description = "Wifi interface migrated from fritzbox"
    else:
        description = f"Interface {input_data['name']} migrated from fritzbox"
    
    subnet_info = {
        "subnet4": {
            "subnet": f"{network_address}/{cidr}",
            "option_data_autocollect": "1",
            "next_server": "",
            "option_data": {
                "domain_name_servers": input_data.get('dns_servers', ''),
                "boot_file_name": "",
                "domain_name": "",
                "domain_search": "",
                "ntp_server": "",
                "routers": "",
                "static_routes": "",
                "tftp_server_name": "",
                "time_servers": ""
#                "routers": input_data['ipaddr']
            },
            "pools":f"{input_data['dhcpstart']}-{input_data['dhcpend']}",
            "description": description
        }
    }

    # Add optional fields if they exist in the input data
    if 'domain_name' in input_data:
        subnet_info["subnet"]["option_data"]["domain_name"] = input_data['domain_name']
    
    if 'ntp_servers' in input_data:
        subnet_info["subnet"]["option_data"]["ntp_servers"] = input_data['ntp_servers']

    return subnet_info

def convert_to_opnsense_reservation(input_data, subnet_uuid):
    """
    Converts the input JSON object to the format required by OPNsense for adding a DHCP reservation.

    :param input_data: Dictionary containing the input DHCP reservation information
    :param subnet_uuid: UUID of the subnet to which this reservation belongs
    :return: Dictionary formatted for OPNsense DHCP reservation
    """
    opnsense_reservation = {
        "reservation": {
            "subnet": subnet_uuid,
            "ip_address": input_data["ip"],
            "hw_address": input_data["mac"],
            "hostname": sanitize_hostname(input_data["neighbour_name"]),
            "description": f"Reservation for {sanitize_hostname(input_data['neighbour_name'])}"
        }
    }

    return opnsense_reservation

def main():
    parser = argparse.ArgumentParser(description="OPNsense DHCP migration tool")
    parser.add_argument("--config", default="config.json", help="Path to the config file")
    parser.add_argument("ar7cfg", metavar="ar7.cfg", help="Path to the ar7.cfg file")
    args = parser.parse_args()

    warnings.filterwarnings('ignore', message='Unverified HTTPS request')

    config = load_config(args.config)

    input_stream = FileStream(args.ar7cfg, encoding='utf-8')
    lexer = ConfigLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = ConfigParser(token_stream)
    tree = parser.config()
    printer = ConfigJSONPrinter()
    ar7cfg = json.loads(printer.visitConfig(tree))

    landevices_jsonpath_expr = jsonpath_ng.parse('$.landevices.landevices[?staticlease = "yes"]')
    landevices_matches = landevices_jsonpath_expr.find(ar7cfg)

    ethinterfaces_jsonpath_expr = jsonpath_ng.parse('$.ar7cfg[ethinterfaces]')
    ethinterfaces_matches = ethinterfaces_jsonpath_expr.find(ar7cfg)
    
#    print(json.dumps(ar7cfg, indent=2))

    version = get_opnsense_version(config)
    print(f"OPNsense Version: {version}")

#    dhcp_config = get_kea_dhcpv4_config(config)
#    print(json.dumps(dhcp_config, indent=2))

    subnet_uuids = {}

    print("Migrating subnets")
    for match in ethinterfaces_matches:
        for interface in match.value:
            subnet_info = map_ar7_ethinterface_to_kea_subnet_info(interface)
#            print(json.dumps(interface, indent=2))
            result = add_dhcpv4_subnet(config, subnet_info)
            print(result)
            subnet_uuids[interface["name"]] = result["uuid"]

#    print(subnet_uuids)

    # # Search for DHCP subnets
    # subnets = search_dhcpv4_subnets(config)
    # print("\nCurrent DHCP Subnets:")
    # print(json.dumps(subnets, indent=2))

    print("Migrating reservations")
    for match in landevices_matches:
        landevice = match.value
#        print(json.dumps(landevice, indent=2))
        reservation = convert_to_opnsense_reservation(landevice, subnet_uuids["eth0"])
        result = add_kea_dhcpv4_reservation(config, reservation)
        #print(json.dumps(reservation, indent=2))
        print(result)

    # Search for DHCP reservations
    # reservations = search_kea_dhcpv4_reservations(config)
    # print("\nCurrent DHCP Reservations:")
    # print(json.dumps(reservations, indent=2))

if __name__ == "__main__":
    main()