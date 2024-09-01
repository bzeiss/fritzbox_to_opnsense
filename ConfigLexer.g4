lexer grammar ConfigLexer;

LCURLY : '{';
RCURLY : '}';
EQUALS : '=';
SEMICOLON : ';';
COMMA : ',';
COLON : ':' ;

IDENTIFIER : [a-zA-Z_] [a-zA-Z0-9_]*;

STRING : '"' (ESC | PRINTABLE_CHAR | OCTAL_ESC)* '"' ;
fragment ESC : '\\' [btnfr"'\\] ;
fragment OCTAL_ESC : '\\' [0-3] [0-7] [0-7] ;
fragment PRINTABLE_CHAR : ~["\\\u0000-\u001F] ;

NUMBER : '-'? INT ('.' [0-9]+)?;
fragment INT : '0' | [1-9] [0-9]*;

BOOLEAN : 'yes' | 'no';

TIME_MINUTES : [0-9]+'m';
TIME_SECONDS : [0-9]+'s';
TIME_HOURS : [0-9]+'h';
TIME_DAYS : [0-9]+'d';
TIME_WEEKS : [0-9]+'w';

IPV6_ADDRESS
    : (HEX_SEGMENT (':' HEX_SEGMENT)* '::' HEX_SEGMENT? (':' HEX_SEGMENT)*) 
    | (HEX_SEGMENT (':' HEX_SEGMENT){7})
    | '::' (HEX_SEGMENT (':' HEX_SEGMENT)*)
    | '::'
    ;

fragment HEX_SEGMENT : HEX_DIGIT+ ;
fragment HEX_DIGIT : [0-9a-fA-F] ;

IPV4_ADDRESS : OCTET '.' OCTET '.' OCTET '.' OCTET ;
fragment OCTET : [0-9] | [1-9][0-9] | '1'[0-9][0-9] | '2'[0-4][0-9] | '25'[0-5] ;

MAC_ADDRESS : HEX_PAIR ':' HEX_PAIR ':' HEX_PAIR ':' HEX_PAIR ':' HEX_PAIR ':' HEX_PAIR;
fragment HEX_PAIR : [0-9a-fA-F][0-9a-fA-F];

WHITESPACE : [ \t\r\n]+ -> skip;

COMMENT : '//' ~[\r\n]* -> skip;
MULTILINE_COMMENT : '/*' .*? '*/' -> skip;

