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

def add_wan_vlan(config, vlan_config):
    endpoint = 'interfaces/vlan_settings/addItem'
    return make_request(config, 'POST', endpoint, data=vlan_config)

def reconfigure_vlan_settings(config):
    endpoint = 'interfaces/vlan_settings/reconfigure'
    return make_request(config, 'POST', endpoint, data="")

def find_interface_by_name(config, interface_name):
    # Endpoint to get interfaces info
    endpoint = 'interfaces/overview/interfacesInfo'

    try:
        # Make API request to get all interfaces
        response = make_request(config, 'GET', endpoint)

        # Check if the request was successful
        if not isinstance(response, dict):
            print("Error: Unable to fetch interface list")
            return None

        # Iterate through interfaces
        for interface in response["rows"]:
            if interface["description"] == interface_name:
                return interface

        # If interface not found
        print(f"Interface '{interface_name}' not found")
        return None

    except Exception as e:
        print(f"Error occurred while fetching interface details: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description="OPNsense Telekom PPPOE login migration tool")
    parser.add_argument("--config", default="config.json", help="Path to the config file")
    parser.add_argument("ar7cfg", metavar="ar7.cfg", help="Path to the ar7.cfg file")
    parser.add_argument("wan_interface_name", help="OPNsense interface name of the WAN interface (usually 'WAN')")

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

    targets_jsonpath_expr = jsonpath_ng.parse('$.ar7cfg.targets[?name == "internet"]')
    targets_matches = targets_jsonpath_expr.find(ar7cfg)

    if (len(targets_matches)) != 1:
        print("Unerwartete Anzahl an internet targets in ar7.cfg")
        sys.exit()

    pppoe_username = targets_matches[0].value['local']['username']
    pppoe_password = targets_matches[0].value['local']['passwd']

    version = get_opnsense_version(config)
    print(f"OPNsense Version: {version}")

    ## Step 1: add vlan 7 to WAN interface
    print("Adding VLAN 7 to the WAN interface...")
    interface = find_interface_by_name(config, args.wan_interface_name)
    device = interface["device"]
    print("WAN interface [" + args.wan_interface_name + "] is " + device)

    vlan_config = {
        "vlan": {
            "descr": "vlan_07_telekom",
            "if": device,
            "pcp": "0",
            "proto": "",
            "tag": "7",
            "vlanif": ""            
        }
    }
    print(vlan_config)
    result = add_wan_vlan(config, vlan_config)
    print(result)
    result = reconfigure_vlan_settings(config)
    print(result)

    # # Step 2: configure WAN interface
    # print("Configuring WAN interface for Telekom PPPOE...")
    # interface = find_interface_by_name(config, args.wan_interface_name)
    # interface_identifier = interface["identifier"]
    # print(json.dumps(interface, indent=2))
    
    # interface["mtu"]=1500
    # interface["link_type"]="pppoe"
    # #interface["pppoe_username"] = pppoe_username
    # #interface["pppoe_password"] = pppoe_password
    # update_interface(config, interface_identifier, interface)
    # reload_interface(config, interface_identifier)

    print("-----")
    print("PPPoE Username: " + pppoe_username)
    print("PPPoE Passwort: " + pppoe_password)

if __name__ == "__main__":
    main()
