parser grammar ConfigParser;

options { tokenVocab = ConfigLexer; }

config: section*;

section: IDENTIFIER sectionContent;
sectionContent: sectionSingle | sectionList;
sectionList: sectionSingle (sectionSingle)+;
sectionSingle: LCURLY content RCURLY;

content: (variable | variableList | section)*;

variable: IDENTIFIER EQUALS value SEMICOLON;
variableList: IDENTIFIER EQUALS value (COMMA value)+ SEMICOLON;

value: STRING
     | NUMBER
     | BOOLEAN
     | IPV6_ADDRESS
     | IPV4_ADDRESS
     | MAC_ADDRESS
     | TIME_WEEKS
     | TIME_DAYS
     | TIME_HOURS
     | TIME_MINUTES
     | TIME_SECONDS
     | IDENTIFIER
     ;
