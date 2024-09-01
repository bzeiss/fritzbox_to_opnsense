#!/bin/bash
antlr4 -Dlanguage=Python3 ConfigLexer.g4 2>&1
antlr4 -Dlanguage=Python3 -visitor ConfigParser.g4 2>&1
/bin/python3 ar7_to_json.py ../tests/fb/ar7.cfg 2>&1


