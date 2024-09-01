import json
import re
from antlr4 import *
from ConfigParser import ConfigParser
from ConfigParserVisitor import ConfigParserVisitor

class ConfigJSONPrinter(ConfigParserVisitor):
    def __init__(self):
        self.result = {}
        self.current_section = self.result

    def visitConfig(self, ctx:ConfigParser.ConfigContext):
        self.visitChildren(ctx)
        return json.dumps(self.result, indent=2)

    def visitSection(self, ctx:ConfigParser.SectionContext):
        section_name = ctx.IDENTIFIER().getText()
        new_section = {}
        self.current_section[section_name] = new_section
        previous_section = self.current_section
        self.current_section = new_section
        self.visitChildren(ctx)
        self.current_section = previous_section

    def visitSectionContent(self, ctx:ConfigParser.SectionContentContext):
        return self.visitChildren(ctx)

    def visitSectionList(self, ctx:ConfigParser.SectionListContext):
        return self.visitChildren(ctx)

    def visitSectionSingle(self, ctx:ConfigParser.SectionSingleContext):
        return self.visitChildren(ctx)

    def visitContent(self, ctx:ConfigParser.ContentContext):
        return self.visitChildren(ctx)

    def visitVariable(self, ctx:ConfigParser.VariableContext):
        name = ctx.IDENTIFIER().getText()
        value = self.visit(ctx.value())
        self.current_section[name] = value

    def visitVariableList(self, ctx:ConfigParser.VariableListContext):
        name = ctx.IDENTIFIER().getText()
        values = [self.visit(value) for value in ctx.value()]
        self.current_section[name] = values

    def visitValue(self, ctx:ConfigParser.ValueContext):
        text = ctx.getText()
        # Try to convert to appropriate type
        if ctx.NUMBER():
            return float(text) if '.' in text else int(text)
        elif ctx.BOOLEAN():
            return text.lower() == 'yes'
        elif ctx.TIME_WEEKS() or ctx.TIME_DAYS() or ctx.TIME_HOURS() or ctx.TIME_MINUTES() or ctx.TIME_SECONDS():
            # Return as string for time values
            return text
        elif ctx.STRING():
            text = text[1:-1]  # Remove outer quotes
            text = re.sub(r'\\(.)', r'\1', text)  # Unescape all escaped characters
            return text
        else:
            # For other types (IP addresses, MAC addresses, identifiers), return as is
            return text

