from enum import Enum, auto

class TokenKind(Enum):
    # Internal / meta
    DEBUG_NULL    = auto()
    DEBUG_UNKNOWN = auto()
    EOF_KIND      = auto()
    COMMENT       = auto()

    # Literals
    INTEGER       = auto()
    DECIMAL       = auto()
    STRING        = auto()
    CHAR_LITERAL  = auto()
    COMPOSITE_STR = auto()

    # Primitive and collection types
    IDENTIFIER    = auto()
    INT           = auto()
    STR           = auto()
    FLOAT         = auto()
    BOOL          = auto()
    CHAR          = auto()
    ANY           = auto()
    NIL           = auto()
    UNINITIALIZED = auto()

    LIST          = auto()
    ARR           = auto()
    SET           = auto()

    # Custom type declarations
    STRUCT        = auto()
    ENUM          = auto()

    # Declaration modifiers
    NEW           = auto()
    GLOBAL        = auto()
    CONST         = auto()

    # Reserved identifiers
    SELF          = auto()

    # Flow control
    IF            = auto()
    ELSIF         = auto()
    ELSE          = auto()
    WHILE         = auto()
    UNTIL         = auto()
    FOR           = auto()
    FOREACH       = auto()
    FROM          = auto()
    TO            = auto()
    IN            = auto()
    RETURN        = auto()

    # Symbols
    ASSIGN        = auto()
    DOT           = auto()
    QUESTION_MARK = auto()
    COMMA         = auto()
    COLON         = auto()
    PIPE          = auto()

    # Arithmetic operators
    PLUS          = auto()
    MINUS         = auto()
    ASTERISK      = auto()
    SLASH         = auto()
    EXPONENT      = auto()
    MODULO        = auto()
    DOUBLE_SLASH  = auto()

    # Compound assignment
    PLUS_ASSIGN       = auto()
    MINUS_ASSIGN      = auto()
    MULT_ASSIGN       = auto()
    DIV_ASSIGN        = auto()
    EXPONENT_ASSIGN   = auto()
    MODULO_ASSIGN     = auto()
    FLOOR_DIV_ASSIGN  = auto()

    # Comparison
    EQUALS        = auto()
    NOT_EQUAL     = auto()
    MORE_THAN     = auto()
    LESS_THAN     = auto()
    MORE_EQUAL    = auto()
    LESS_EQUAL    = auto()

    # Logical operators
    NOT           = auto()
    AND           = auto()
    OR            = auto()
    XOR           = auto()

    # Logical literals
    TRUE          = auto()
    FALSE         = auto()

    # Delimiters
    OPEN_PAREN    = auto()
    CLOSE_PAREN   = auto()
    OPEN_CURLY    = auto()
    CLOSE_CURLY   = auto()
    OPEN_BRACK    = auto()
    CLOSE_BRACK   = auto()
    SEMICOLON     = auto()
    HASH          = auto()

    def Name(self):
        return self.name.lower()

KEYWORDS: dict[str, TokenKind] = {
    # Primitive types
    "int": TokenKind.INT,
    "ᛁᚾᛏ": TokenKind.INT,

    "str": TokenKind.STR,
    "ᛋᛏᚱ": TokenKind.STR,
    "ᛥᚱ": TokenKind.STR,

    "float": TokenKind.FLOAT,
    "ᚠᛚᚩᛏ": TokenKind.FLOAT,

    "bool": TokenKind.BOOL,
    "ᛒᚣᛚ": TokenKind.BOOL,

    "char": TokenKind.CHAR,
    "ᚳᚻᚪᚱ": TokenKind.CHAR,

    "any": TokenKind.ANY,
    "ᛖᚾᛁ": TokenKind.ANY,

    "nil": TokenKind.NIL,
    "ᚾᛁᛚ": TokenKind.NIL,

    "uninitialized": TokenKind.UNINITIALIZED,
    "ᚢᚾᛁᚾᛁᛋᚻᚢᛚᛡᛋᛏ": TokenKind.UNINITIALIZED,
    "ᚢᚾᛁᚾᛁᛋᚻᚢᛚᛡᛥ": TokenKind.UNINITIALIZED,

    # Collections
    "list": TokenKind.LIST,
    "ᛚᛁᛋᛏ": TokenKind.LIST,
    "ᛚᛁᛥ": TokenKind.LIST,

    "arr": TokenKind.ARR,
    "ᚪᚱ": TokenKind.ARR,

    "set": TokenKind.SET,
    "ᛋᛖᛏ": TokenKind.SET,

    # Custom types
    "struct": TokenKind.STRUCT,
    "ᛋᛏᚱᚢᚳᛏ": TokenKind.STRUCT,
    "ᛥᚱᚢᚳᛏ": TokenKind.STRUCT,

    "enum": TokenKind.ENUM,
    "ᛁᚾᚣᛗ": TokenKind.ENUM,

    # Declaration modifiers
    "new": TokenKind.NEW,
    "ᚾᛁᚢ": TokenKind.NEW,

    "global": TokenKind.GLOBAL,
    "ᚷᛚᚩᛒᚢᛚ": TokenKind.GLOBAL,

    "const": TokenKind.CONST,
    "ᚳᛟᚾᛋᛏ": TokenKind.CONST,

    # Reserved identifiers
    "self": TokenKind.SELF,
    "ᛋᛖᛚᚠ": TokenKind.SELF,

    # Boolean literals/operators
    "true": TokenKind.TRUE,
    "ᛏᚱᚣ": TokenKind.TRUE,

    "false": TokenKind.FALSE,
    "ᚠᛟᛚᛋ": TokenKind.FALSE,

    "not": TokenKind.NOT,
    "ᚾᛟᛏ": TokenKind.NOT,

    "and": TokenKind.AND,
    "ᚫᚾᛞ": TokenKind.AND,

    "or": TokenKind.OR,
    "ᛟᚱ": TokenKind.OR,

    "xor": TokenKind.XOR,
    "ᛉᛟᚱ": TokenKind.XOR,

    # Control flow
    "if": TokenKind.IF,
    "ᛁᚠ": TokenKind.IF,

    "elsif": TokenKind.ELSIF,
    "ᛖᛚᛁᚠ": TokenKind.ELSIF,

    "else": TokenKind.ELSE,
    "ᛖᛚᛋ": TokenKind.ELSE,

    "while": TokenKind.WHILE,
    "ᚹᛠᛚ": TokenKind.WHILE,

    "until": TokenKind.UNTIL,
    "ᚢᚾᛏᛁᛚ": TokenKind.UNTIL,

    "for": TokenKind.FOR,
    "ᚠᛟ": TokenKind.FOR,

    "foreach": TokenKind.FOREACH,
    "ᚠᛟᚱᛁᛁᚳᚻ": TokenKind.FOREACH,

    "from": TokenKind.FROM,
    "ᚠᚱᛟᛗ": TokenKind.FROM,

    "to": TokenKind.TO,
    "ᛏᚣ": TokenKind.TO,

    "in": TokenKind.IN,
    "ᛁᚾ": TokenKind.IN,

    "return": TokenKind.RETURN,
    "ᚱᛁᛏᚢᚱᚾ": TokenKind.RETURN,
}

def symbolize(tokenKind: TokenKind):
    match tokenKind:
        case TokenKind.PLUS:
            return "+"
        case TokenKind.MINUS:
            return "-"
        case TokenKind.ASTERISK:
            return "*"
        case TokenKind.SLASH:
            return "/"
        case TokenKind.EOF_KIND:
            return "\0"
        case TokenKind.ASSIGN:
            return "="
        case TokenKind.EXPONENT:
            return "^"
        case TokenKind.OPEN_PAREN:
            return "("
        case TokenKind.CLOSE_PAREN:
            return ")"
        case TokenKind.OPEN_CURLY:
            return "{"
        case TokenKind.CLOSE_CURLY:
            return "}"
        case TokenKind.OPEN_BRACK:
            return "["
        case TokenKind.CLOSE_BRACK:
            return "]"
        case TokenKind.SEMICOLON:
            return ";"
        case TokenKind.COMPOSITE_STR:
            return "c"
        case TokenKind.COMMA:
            return ","
        case TokenKind.DOUBLE_SLASH:
            return "//"
        case TokenKind.DOT:
            return "."
        case TokenKind.HASH:
            return "#"
        case TokenKind.EQUALS:
            return "=="
        case TokenKind.NOT_EQUAL:
            return "!="
        case TokenKind.MORE_THAN:
            return ">"
        case TokenKind.LESS_THAN:
            return "<"
        case TokenKind.MORE_EQUAL:
            return ">="
        case TokenKind.LESS_EQUAL:
            return "<="
        case TokenKind.COLON:
            return ":"
        case TokenKind.QUESTION_MARK:
            return "?"
        case TokenKind.MODULO:
            return "%"
        case TokenKind.PLUS_ASSIGN:
            return "+="
        case TokenKind.MINUS_ASSIGN:
            return "-="
        case TokenKind.MULT_ASSIGN:
            return "*="
        case TokenKind.DIV_ASSIGN:
            return "/="
        case TokenKind.EXPONENT_ASSIGN:
            return "^="
        case TokenKind.MODULO_ASSIGN:
            return "%="
        case TokenKind.FLOOR_DIV_ASSIGN:
            return "//="
        case TokenKind.PIPE:
            return "|"
        case _:
            return f"unmatched symbol: {tokenKind.name}"

class Token:
    def __init__(
        self,
        tokenKind: TokenKind,
        value: str = "",
        index: int = -1,
        end: int | None = None
    ):
        self.kind = tokenKind
        self.value = value
        self.index = index
        self._end = index + len(value) if end is None else end

    @property
    def end(self) -> int:
        """Exclusive source offset immediately after this token."""
        return self._end
    
    def __repr__(self):
        return f"{self.kind.Name()} ({self.value})"
    
    def is_a(self, *options: tuple[TokenKind, ...]):
        return self.kind in options
    
    def debug(self):
        print(f"{self.kind.Name()} ({self.value})")

def newToken(kind: TokenKind, value: str):
    return Token(kind, value)

DATA_TYPES: list[TokenKind] = [
    TokenKind.INT,
    TokenKind.STR,
    TokenKind.FLOAT,
    TokenKind.BOOL,
    TokenKind.CHAR,
    TokenKind.ANY,
    TokenKind.NIL,
    TokenKind.UNINITIALIZED
]


COLLECTION_TYPES: list[TokenKind] = [
    TokenKind.LIST,
    TokenKind.ARR,
    TokenKind.SET
]


TYPE_STARTS: list[TokenKind] = [
    *DATA_TYPES,
    *COLLECTION_TYPES,
    TokenKind.IDENTIFIER
]


CONTROL_FLOW = [
    TokenKind.IF,
    TokenKind.ELSE,
    TokenKind.ELSIF,
    TokenKind.WHILE,
    TokenKind.UNTIL,
    TokenKind.FOR,
    TokenKind.FOREACH,
    TokenKind.RETURN
]


LITERALS = [
    TokenKind.INTEGER,
    TokenKind.DECIMAL,
    TokenKind.STRING,
    TokenKind.CHAR_LITERAL,
    TokenKind.COMPOSITE_STR,
    TokenKind.TRUE,
    TokenKind.FALSE,
    TokenKind.NIL
]


ASSIGNMENT_OPERATORS = [
    TokenKind.ASSIGN,
    TokenKind.PLUS_ASSIGN,
    TokenKind.MINUS_ASSIGN,
    TokenKind.MULT_ASSIGN,
    TokenKind.DIV_ASSIGN,
    TokenKind.EXPONENT_ASSIGN,
    TokenKind.MODULO_ASSIGN,
    TokenKind.FLOOR_DIV_ASSIGN
]

DELIMITERS = [
    TokenKind.OPEN_PAREN,
    TokenKind.CLOSE_PAREN,
    TokenKind.OPEN_CURLY,
    TokenKind.CLOSE_CURLY,
    TokenKind.OPEN_BRACK,
    TokenKind.CLOSE_BRACK,
    TokenKind.SEMICOLON
]

OPERATORS = [
    TokenKind.PLUS,
    TokenKind.MINUS,
    TokenKind.ASTERISK,
    TokenKind.SLASH,
    TokenKind.EXPONENT,
    TokenKind.MODULO,
    TokenKind.DOUBLE_SLASH,
    TokenKind.EQUALS,
    TokenKind.NOT_EQUAL,
    TokenKind.MORE_THAN,
    TokenKind.LESS_THAN,
    TokenKind.LESS_EQUAL,
    TokenKind.LESS_EQUAL,
    TokenKind.NOT,
    TokenKind.AND,
    TokenKind.OR,
    TokenKind.XOR,
    TokenKind.XOR
]

ARITHMETIC_OPS = (
    TokenKind.PLUS,
    TokenKind.MINUS,
    TokenKind.ASTERISK,
    TokenKind.SLASH,
    TokenKind.EXPONENT,
    TokenKind.MODULO,
    TokenKind.DOUBLE_SLASH
)

COMPARISON_OPS = (
    TokenKind.EQUALS,
    TokenKind.NOT_EQUAL,
    TokenKind.MORE_THAN,
    TokenKind.LESS_THAN,
    TokenKind.LESS_EQUAL,
    TokenKind.MORE_EQUAL
)
LOGICAL_OPS = (
    TokenKind.NOT,
    TokenKind.AND,
    TokenKind.OR,
    TokenKind.XOR,
)
