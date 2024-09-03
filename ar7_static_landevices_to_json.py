#!/bin/python3

import sys
import json
import jsonpath_ng.ext as jsonpath_ng
from antlr4 import *
from ConfigLexer import ConfigLexer
from ConfigParser import ConfigParser
from ConfigJSONPrinter import ConfigJSONPrinter

def main(argv):
    if len(argv) != 2:
        print("Usage: python ar_to_json.py <input_file>")
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

#        jsonpath_expr = jsonpath_ng.parse('$.landevices.landevices[?staticlease = "yes" & url_status ="eLUrlStatusNotAvailable"]')
        jsonpath_expr = jsonpath_ng.parse('$.landevices.landevices[?staticlease = "yes"]')
        matches = jsonpath_expr.find(ar7cfg)

        json_list = []
        for match in matches:
            json_list.append(match.value)

        print(json.dumps(json_list, indent=4))

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    main(sys.argv)


