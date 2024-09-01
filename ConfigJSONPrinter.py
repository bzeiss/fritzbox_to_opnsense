import json
import re
from antlr4 import *
from ConfigParser import ConfigParser
from ConfigParserVisitor import ConfigParserVisitor

class ConfigJSONPrinter(ConfigParserVisitor):
    def __init__(self):
        self.result = {}
        self.current_context = [self.result]
        self.current_section_name = None

    def visitConfig(self, ctx:ConfigParser.ConfigContext):
        self.visitChildren(ctx)
        return json.dumps(self.result, indent=2)

    def visitSection(self, ctx:ConfigParser.SectionContext):
        section_name = ctx.IDENTIFIER().getText()
        self.current_section_name = section_name
        new_section = {}
        if isinstance(self.current_context[-1], list):
            self.current_context[-1].append(new_section)
        else:
            self.current_context[-1][section_name] = new_section
        self.current_context.append(new_section)
        self.visitChildren(ctx)
        self.current_context.pop()
        self.current_section_name = None

    def visitSectionContent(self, ctx:ConfigParser.SectionContentContext):
        return self.visitChildren(ctx)

    def visitSectionList(self, ctx:ConfigParser.SectionListContext):
        if self.current_section_name is None:
            raise ValueError("SectionList encountered without a current section name")
        section_list = []
        current_dict = self.current_context[-1]
        if self.current_section_name in current_dict:
            if isinstance(current_dict[self.current_section_name], list):
                section_list = current_dict[self.current_section_name]
            else:
                section_list = [current_dict[self.current_section_name]]
                current_dict[self.current_section_name] = section_list
        else:
            current_dict[self.current_section_name] = section_list
        self.current_context.append(section_list)
        self.visitChildren(ctx)
        self.current_context.pop()

    def visitSectionSingle(self, ctx:ConfigParser.SectionSingleContext):
        if isinstance(self.current_context[-1], list):
            new_section = {}
            self.current_context[-1].append(new_section)
            self.current_context.append(new_section)
            self.visitChildren(ctx)
            self.current_context.pop()
        else:
            self.visitChildren(ctx)

    def visitContent(self, ctx:ConfigParser.ContentContext):
        return self.visitChildren(ctx)

    def visitVariable(self, ctx:ConfigParser.VariableContext):
        name = ctx.IDENTIFIER().getText()
        value = self.visit(ctx.value())
        self.current_context[-1][name] = value

    def visitVariableList(self, ctx:ConfigParser.VariableListContext):
        name = ctx.IDENTIFIER().getText()
        values = [self.visit(value) for value in ctx.value()]
        self.current_context[-1][name] = values

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

