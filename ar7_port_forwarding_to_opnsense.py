#!/bin/python3

import sys
import json
import jmespath
from antlr4 import *
from ConfigLexer import ConfigLexer
from ConfigParser import ConfigParser
from ConfigJSONPrinter import ConfigJSONPrinter

def parse_port_forwarding_rule(rule_string):
    # Split the rule into main components and comment
    main_rule, _, comment = rule_string.partition('#')
    
    # Split the main rule into its components
    components = main_rule.split()
    
    # Extract the components
    protocol = components[0]
    external = components[1]
    internal = components[2]
    unknown_value = components[3]
    mark = ' '.join(components[4:6])  # Join 'mark' and its value
    
    # Split IP and port for external and internal
    external_ip, external_port = external.split(':')
    internal_ip, internal_port = internal.split(':')
    
    # Create and return the structured dictionary
    return {
        'protocol': protocol,
        'external': {
            'ip': external_ip,
            'port': int(external_port)
        },
        'internal': {
            'ip': internal_ip,
            'port': int(internal_port)
        },
        'unknown_value': int(unknown_value),
        'mark': mark,
        'comment': comment.strip() if comment else None
    }

def main(argv):
    if len(argv) != 2:
        print("Usage: python ar7_port_forwarding_to_opnsense.py <input_file>")
        return

    input_file = argv[1]
    
    try:
        input_stream = FileStream(input_file, encoding='utf-8')
        lexer = ConfigLexer(input_stream)
        token_stream = CommonTokenStream(lexer)
        parser = ConfigParser(token_stream)
        tree = parser.config()
        printer = ConfigJSONPrinter()
        ar7cfg = json.loads(printer.visitConfig(tree))

        jsonpath_expr = jmespath.search("landevices.landevices[?staticlease == 'yes' && ipv4forwardrules != null && type(ipv4forwardrules)  == 'array' && length(ipv4forwardrules) > `0`].ipv4forwardrules", ar7cfg)

        for match in jsonpath_expr:            
#            print(json.dumps(match, indent=2))
            for rulestr in match:
                rule = parse_port_forwarding_rule(rulestr)
                print(rule)
#            print(match)
            print("---------")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    main(sys.argv)


