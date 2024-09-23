#!/bin/bash
clear

#/bin/python3 ar7_to_json.py ../tests/fb/ar7.cfg 2>&1 >ar7.json

#/bin/python3 ar7_static_landevices_to_json.py ../tests/fb/ar7.cfg 2>&1
#/bin/python3 ar7_static_landevices_to_json.py ../tests/fb/ar7.cfg 2>&1 | tee /dev/tty | jq 'length'
#/bin/python3 ar7_static_landevices_to_json.py ../tests/fb/ar7.cfg 2>&1 >landevices.json
#/bin/python3 ar7_dhcp4_to_opnsense_kea.py ../tests/fb/ar7.cfg 2>&1
#/bin/python3 clean_opnsense_kea_dhcpv4.py 2>&1
#/bin/python3 ar7_telekom_to_opnsense_pppoe.py ../tests/fb/ar7.cfg WAN
/bin/python3 vpn_wireguard_to_opnsense.py --clean --addrules ../tests/fb/vpn.cfg
