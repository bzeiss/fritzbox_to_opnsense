#!/bin/python3

import sys
import json
from antlr4 import *
from ConfigLexer import ConfigLexer
from ConfigParser import ConfigParser
from ConfigJSONPrinter import ConfigJSONPrinter

def print_tokenstream(token_stream, lexer):
    token_stream.fill()

    for token in token_stream.tokens:
        if token.type != Token.EOF:
            print(f"Token Type: {lexer.symbolicNames[token.type]}, Text: '{token.text}'")

def print_nodestream(tree, parser, indent=""):
    if isinstance(tree, TerminalNode):
        print(f"{indent}Terminal: {tree.getText()}")
    else:
        rule_name = parser.ruleNames[tree.getRuleIndex()]
        print(f"{indent}Rule: {rule_name}")
        for child in tree.getChildren():
            print_nodestream(child, parser, indent + "  ")

def main(argv):
    if len(argv) != 2:
        print("Usage: python ar_to_json.py <input_file>")
        return

    input_file = argv[1]
    
    try:
        input_stream = FileStream(input_file, encoding='utf-8')
        lexer = ConfigLexer(input_stream)
        token_stream = CommonTokenStream(lexer)
#        print_tokenstream(token_stream, lexer)
        parser = ConfigParser(token_stream)
        tree = parser.config()
#        print_nodestream(tree, parser)
        printer = ConfigJSONPrinter()
        print(printer.visitConfig(tree))

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    main(sys.argv)


