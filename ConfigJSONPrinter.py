import json
import re
from antlr4 import *
from ConfigParser import ConfigParser
from ConfigParserVisitor import ConfigParserVisitor

class ConfigJSONPrinter(ConfigParserVisitor):
    def __init__(self):
        self.result = {}
        self.context_stack = [self.result]
        self.current_section_name = None

    def visitConfig(self, ctx:ConfigParser.ConfigContext):
        self.visitChildren(ctx)
        return json.dumps(self.result, indent=2)

    def visitSection(self, ctx:ConfigParser.SectionContext):
        self.current_section_name = ctx.IDENTIFIER().getText()
        self.visitChildren(ctx)
        self.current_section_name = None

    def visitSectionContent(self, ctx:ConfigParser.SectionContentContext):
        return self.visitChildren(ctx)

    def visitSectionList(self, ctx:ConfigParser.SectionListContext):
        current_context = self.context_stack[-1]
        if self.current_section_name not in current_context:
            current_context[self.current_section_name] = []
        self.context_stack.append(current_context[self.current_section_name])
        self.visitChildren(ctx)
        self.context_stack.pop()

    def visitSectionSingle(self, ctx:ConfigParser.SectionSingleContext):
        new_section = {}
        if isinstance(self.context_stack[-1], list):
            self.context_stack[-1].append(new_section)
        else:
            self.context_stack[-1][self.current_section_name] = new_section
        self.context_stack.append(new_section)
        self.visitChildren(ctx)
        self.context_stack.pop()

    def visitContent(self, ctx:ConfigParser.ContentContext):
        return self.visitChildren(ctx)

    def visitVariable(self, ctx:ConfigParser.VariableContext):
        name = ctx.IDENTIFIER().getText()
        value = self.visit(ctx.value())
        self.context_stack[-1][name] = value

    def visitVariableList(self, ctx:ConfigParser.VariableListContext):
        name = ctx.IDENTIFIER().getText()
        values = [self.visit(value) for value in ctx.value()]
        self.context_stack[-1][name] = values

    def visitValue(self, ctx:ConfigParser.ValueContext):
        text = ctx.getText()
        if ctx.NUMBER():
            return float(text) if '.' in text else int(text)
        elif ctx.BOOLEAN():
            return text.lower() == 'yes'
        elif ctx.TIME_WEEKS() or ctx.TIME_DAYS() or ctx.TIME_HOURS() or ctx.TIME_MINUTES() or ctx.TIME_SECONDS():
            return text
        elif ctx.STRING():
            text = text[1:-1]  # Remove outer quotes
            text = re.sub(r'\\(.)', r'\1', text)  # Unescape all escaped characters
            return text
        else:
            return text