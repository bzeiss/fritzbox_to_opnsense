#!/bin/python3

import json
import argparse
import requests
import sys
import re
import warnings
import secrets
import base64
import ipaddress
import jmespath
from requests.auth import HTTPBasicAuth
from antlr4 import *
from ConfigLexer import ConfigLexer
from ConfigParser import ConfigParser
from ConfigJSONPrinter import ConfigJSONPrinter

tunnel_network = "10.10.10.1/24"

def next_ip(ip_network):
    ip = ipaddress.ip_interface(ip_network)
    next_ip = ip.ip + 1
    if next_ip not in ip.network:
        next_ip = ip.network.network_address + 1
    
    return f"{next_ip}/32"

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
    product = data["product"]
    return product.get('product_version', 'Unknown')

def generate_keypair():
    private_key = base64.b64encode(secrets.token_bytes(32)).decode('utf-8')
    # In a real-world scenario, you'd use the Wireguard tools to generate the public key from the private key
    # This is a placeholder and won't generate a valid public key
    public_key = base64.b64encode(secrets.token_bytes(32)).decode('utf-8')
    return private_key, public_key

def create_wireguard_server(config, vpn_config, global_vpn_config):
    server_data = {
        "server": {
            "enabled": "1" if vpn_config["enabled"] == "yes" else "0",
            "name": vpn_config["name"],
            "pubkey": global_vpn_config["wg_public_key"],  
            "privkey": global_vpn_config["wg_private_key"],  
            "port": global_vpn_config["wg_listen_port"],
            "tunneladdress": tunnel_network,
            "dns": vpn_config["wg_dnsserver"],
            "mtu": "1412", # setup for dsl/vdsl, should be 1420 otherwise
            "peers": "",  # This will be set when we add the client
            "disableroutes": "0",
            "gateway": "",  # Set this if needed for routing
        }
    }

    response = make_request(config, 'POST', 'wireguard/server/addServer', server_data)
    return response

def create_wireguard_client(config, vpn_config, global_vpn_config, server_uuid, address):
    client_data = {
        "client": {
            "enabled": "1" if vpn_config["enabled"] == "yes" else "0",
            "name": f"{vpn_config['name']}_peer",
            "pubkey": vpn_config["wg_public_key"],
            "psk": vpn_config["wg_preshared_key"],
#            "mtu": "1412", # setup for dsl/vdsl, should be 1420 otherwise
            "tunneladdress": address,
#            "tunneladdress": vpn_config["wg_allowed_ips"],
            "serveraddress": vpn_config["wg_dyndns"],
            "serverport": global_vpn_config["wg_listen_port"],
            "keepalive": str(vpn_config["wg_persistent_keepalive"]),
            "servers": server_uuid
        }
    }
    response = make_request(config, 'POST', 'wireguard/client/addClient', client_data)
    return response

def enable_wireguard_service(config):
    service_data = {
        "general": {
            "enabled": "1"
        }
    }
    response = make_request(config, 'POST', 'wireguard/general/set', service_data)

    # Reconfigure the service to apply changes
    make_request(config, 'POST', 'wireguard/service/reconfigure')

    return response

def remove_all_wireguard_configs(config):
    # Remove all server instances
    servers_removed = remove_all_servers(config)
    
    # Remove all clients
    clients_removed = remove_all_clients(config)    
   
    return {
        "servers_removed": servers_removed,
        "clients_removed": clients_removed,
    }

def remove_all_servers(config):
    # Fetch all server instances
    servers_response = make_request(config, 'GET', 'wireguard/server/searchServer')
    servers = servers_response.get('rows', [])
    
    removed_servers = []
    for server in servers:
        uuid = server.get('uuid')
        if uuid:
            response = make_request(config, 'POST', f'wireguard/server/delServer/{uuid}')
            removed_servers.append({
                "uuid": uuid,
                "name": server.get('name'),
                "response": response
            })
    
    return removed_servers

def remove_all_clients(config):
    # Fetch all clients
    clients_response = make_request(config, 'GET', 'wireguard/client/searchClient')
    clients = clients_response.get('rows', [])
    
    removed_clients = []
    for client in clients:
        uuid = client.get('uuid')
        if uuid:
            response = make_request(config, 'POST', f'wireguard/client/delClient/{uuid}')
            removed_clients.append({
                "uuid": uuid,
                "name": client.get('name'),
                "response": response
            })
    
    return removed_clients

def cleanup_wireguard_configs(config):
    result = remove_all_wireguard_configs(config)
    print("Wireguard configurations removal summary:")
    print(f"Servers removed: {len(result['servers_removed'])}")
    print(f"Clients removed: {len(result['clients_removed'])}")
    print("")
    return result

def add_firewall_rule(config, rule_data):
    response = make_request(config, 'POST', 'firewall/filter/addRule', rule_data)

    return response

def apply_firewall_rules(config):
    response = make_request(config, 'POST', 'firewall/filter/apply')

    return response

def main(argv):
    parser = argparse.ArgumentParser(description="OPNsense wireguard migration tool")
    parser.add_argument("--clean", help="clean up all instances and peer entries before adding new ones", action='store_true')
    parser.add_argument("--addrules", help="add a firewall rule to allow wireguard on the WAN port and a rule to allow vpn users to access the internal network", action='store_true')
    parser.add_argument("--config", default="config.json", help="Path to the config file")
    parser.add_argument("vpncfg", metavar="vpn.cfg", help="Path to the vpn.cfg file")
    args = parser.parse_args()

    warnings.filterwarnings('ignore', message='Unverified HTTPS request')

    config = load_config(args.config)

    version = get_opnsense_version(config)
    print(f"OPNsense Version: {version}")

    if args.clean is not None:
        cleanup_wireguard_configs(config)

    input_stream = FileStream(args.vpncfg, encoding='utf-8')
    lexer = ConfigLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = ConfigParser(token_stream)
    tree = parser.config()
    printer = ConfigJSONPrinter()
    vpncfg = json.loads(printer.visitConfig(tree))

    global_vpn_config = jmespath.search('vpncfg.global', vpncfg)
    site_to_site_matches = jmespath.search('vpncfg.connections[?conn_type == `conntype_wg` && wg_hide_network == `no`]', vpncfg)
    client_matches = jmespath.search('vpncfg.connections[?conn_type == `conntype_wg` && wg_hide_network == `yes`]', vpncfg)

    peers = []

    # create instance and client configurations from the site to site fritzbox vpn configs

    print(str(len(site_to_site_matches)) + " site to site vpn configs found")
    next_address = tunnel_network
    for site_to_site_config in site_to_site_matches:
#        print(json.dumps(match, indent=2))

        result = create_wireguard_server(config, site_to_site_config, global_vpn_config)
        print(result)
        server_uuid = result['uuid']
        result = create_wireguard_client(config, site_to_site_config, global_vpn_config, server_uuid, site_to_site_config["wg_allowed_ips"])
        print(result)
        client_uuid = result['uuid']
        peers.append(client_uuid)

    # create peer configurations from the client fritzbox configs

    print("")
    print(str(len(client_matches)) + " client vpn configs found")
    for client_config in client_matches:
#        print(json.dumps(client_config, indent=2))
        next_address = next_ip(next_address)
        result = create_wireguard_client(config, client_config, global_vpn_config, server_uuid, next_address)
        print(result)
        client_uuid = result['uuid']
        peers.append(client_uuid)

    print("")

    if args.addrules is not None:
        print("Allowing WAN access to wireguard port on firewall")
        wan_rule_data = {
            "rule": {
                "enabled": "1",
                "action": "pass",
                "quick": "1",
                "interface": "wan",
                "direction": "in",
                "ipprotocol": "inet",
                "protocol": "UDP",
                "source_net": "any",
#                "destination_net": "(self)", ## this firewall
                "destination_net": "wanip", ## this firewall
                "destination_port": str(global_vpn_config["wg_listen_port"]),
                "description": "Allow IPv4 UDP, Port " + str(global_vpn_config["wg_listen_port"]) + " (Wireguard) to firewall"
            }
        }

        response = add_firewall_rule(config, wan_rule_data)
        print(response)
        wan_rule_data['rule']['ipprotocol'] = "inet6"
        wan_rule_data['rule']['description'] = "Allow IPv6 UDP, Port " + str(global_vpn_config["wg_listen_port"]) + " (Wireguard) to firewall"
        response = add_firewall_rule(config, wan_rule_data)
        print(response)

        print("")
        print("Allowing Wireguard VPN access to all internal networks (Adjust if necessary!!!)")

        wireguard_rule_data = {
            "rule": {
                "enabled": "1",
                "action": "pass",
                "quick": "1",
                "interface": "wireguard",
                "direction": "in",
                "ipprotocol": "inet",
                "protocol": "UDP",
                "source_net": "any",
                "destination_net": "any",
                "destination_port": "",
                "description": "Allow IPv4 access to all internal networks from VPN"
            }
        }

        response = add_firewall_rule(config, wireguard_rule_data)
        print(response)

        wireguard_rule_data['rule']['ipprotocol'] = "inet6"
        wireguard_rule_data['rule']['description'] = "Allow IPv6 access to all internal networks from VPN"
        response = add_firewall_rule(config, wireguard_rule_data)
        print(response)

        print("")
        print("Applying firewall rules")
        apply_firewall_rules(config)

    enable_wireguard_service(config)

if __name__ == '__main__':
    main(sys.argv)
