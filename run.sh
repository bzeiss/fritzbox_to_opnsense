#!/bin/bash
clear

#/bin/python3 ar7_to_json.py ../tests/fb/ar7.cfg 2>&1 >ar7.json

#/bin/python3 ar7_static_landevices_to_json.py ../tests/fb/ar7.cfg 2>&1
#/bin/python3 ar7_static_landevices_to_json.py ../tests/fb/ar7.cfg 2>&1 | tee /dev/tty | jq 'length'
#/bin/python3 ar7_static_landevices_to_json.py ../tests/fb/ar7.cfg 2>&1 >landevices.json
/bin/python3 ar7_dhcp4_to_opnsense_kea.py ../tests/fb/ar7.cfg 2>&1


