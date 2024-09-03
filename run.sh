#!/bin/bash
#/bin/python3 ar7_to_json.py ../tests/fb/ar7.cfg 2>&1

#/bin/python3 ar7_static_landevices_to_json.py ../tests/fb/ar7.cfg 2>&1
/bin/python3 ar7_static_landevices_to_json.py ../tests/fb/ar7.cfg 2>&1 | tee /dev/tty | jq 'length'


