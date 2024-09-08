#!/bin/python3

import json
import argparse
import requests
import sys
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

def search_dhcpv4_subnets(config):
    return make_request(config, 'GET', 'kea/dhcpv4/searchSubnet')

def search_kea_dhcpv4_reservations(config):
    return make_request(config, 'GET', 'kea/dhcpv4/searchReservation')

def delete_dhcpv4_reservation(config, reservation_uuid):
    endpoint = f'kea/dhcpv4/delReservation/{reservation_uuid}'
    return make_request(config, 'POST', endpoint)

def delete_dhcpv4_subnet(config, subnet_uuid):
    endpoint = f'kea/dhcpv4/delSubnet/{subnet_uuid}'
    return make_request(config, 'POST', endpoint)

def main():
    parser = argparse.ArgumentParser(description="OPNsense DHCPv4 KEA cleanup tool")
    parser.add_argument("--config", default="config.json", help="Path to the config file")
    args = parser.parse_args()

    warnings.filterwarnings('ignore', message='Unverified HTTPS request')

    config = load_config(args.config)

    version = get_opnsense_version(config)
    print(f"OPNsense Version: {version}")

#    dhcp_config = get_kea_dhcpv4_config(config)
#    print(json.dumps(dhcp_config, indent=2))

#     subnet_uuids = {}

#     print("Migrating subnets")
#     for match in ethinterfaces_matches:
#         for interface in match.value:
#             subnet_info = map_ar7_ethinterface_to_kea_subnet_info(interface)
# #            print(json.dumps(interface, indent=2))
#             result = add_dhcpv4_subnet(config, subnet_info)
#             print(result)
#             subnet_uuids[interface["name"]] = result["uuid"]

#    print(subnet_uuids)



    # Search for DHCP reservations and delete each reservation
    reservations = search_kea_dhcpv4_reservations(config)
    for reservation in reservations["rows"]:
        result = delete_dhcpv4_reservation(config, reservation["uuid"])
#        print(json.dumps(reservation, indent=2))
        print(result)
        
    # Search for DHCP subnets and delete each subnet
    subnets = search_dhcpv4_subnets(config)
    for subnet in subnets["rows"]:       
        result = delete_dhcpv4_subnet(config, subnet["uuid"])
#        print(json.dumps(subnet, indent=2))
        print(result)

if __name__ == "__main__":
    main()