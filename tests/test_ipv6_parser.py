import unittest
import ipaddress
import pytest
import sys
import json

from datetime import datetime
from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener
from fritzbox_to_opnsense.ConfigLexer import ConfigLexer
from fritzbox_to_opnsense.ConfigParser import ConfigParser

class CustomErrorListener(ErrorListener):
    def __init__(self):
        super(CustomErrorListener, self).__init__()
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        error = f"line {line}:{column} {msg}"
        self.errors.append(error)


def load_test_data(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

# Load test data before class definition
test_addresses = load_test_data('tests/testdata_ipv6/ipv6_addresses.txt')
test_networks = load_test_data('tests/testdata_ipv6/ipv6_networks.txt')

def generate_config_string(ipv6_address):
    current_time = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
    return f"""/*
                * /var/tmp.cfg
                * {current_time}
                */

                meta {{ encoding = "utf-8"; }}

                ar7cfg {{
                    ipv6 = {ipv6_address};
                }}
            """

@pytest.mark.parametrize("address", test_addresses, ids=lambda x: f"IPv6 Address: {x}")
def test_ipv6_addresses(address):
    try:
        # Attempt to parse the address
        # parsed_address = ipaddress.IPv6Address(address)

        print(f"\nTesting IPv6 address: {address}")
        config_string = generate_config_string(address)

        # print(config_string)

        input_stream = InputStream(config_string)
        lexer = ConfigLexer(input_stream)
        lexer_error_listener = CustomErrorListener()
        lexer.removeErrorListeners()
        lexer.addErrorListener(lexer_error_listener)

        token_stream = CommonTokenStream(lexer)
        parser = ConfigParser(token_stream)
        parser_error_listener = CustomErrorListener()
        parser.removeErrorListeners()
        parser.addErrorListener(parser_error_listener)
        tree = parser.config()

        assert not lexer_error_listener.errors, f"Lexer errors occurred: {lexer_error_listener.errors}"
        assert not parser_error_listener.errors, f"Parser errors occurred: {parser_error_listener.errors}"
        assert tree is not None, "Parse tree is None"

    except Exception as e:
        # If we get here, the address was invalid
        pytest.fail(f"Invalid IPv6 address: {address}")

