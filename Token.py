from enum import Enum, auto

class TokenKind(Enum):
    # Internal / meta
    DEBUG_NULL    = auto() #✅
    DEBUG_UNKNOWN = auto() #✅
    EOF_KIND      = auto() #✅

    # Literals
    INTEGER       = auto() #✅
    DECIMAL       = auto() #✅
    STRING        = auto() #✅
    COMPOSITE_STR = auto() #✅

    # Identifiers / keywords
    IDENTIFIER    = auto() #✅
    INT           = auto() #✅
    STR           = auto() #✅
    FLOAT         = auto() #✅
    BOOL          = auto() #✅
    CHAR          = auto() #✅
    ANY           = auto() #✅
    NIL           = auto() #✅

    # Flow control
    IF            = auto() #✅
    ELSIF         = auto() #✅
    ELSE          = auto() #✅
    WHILE         = auto() #✅
    UNTIL         = auto() #✅
    FOR           = auto() #✅
    FOREACH       = auto() #✅
    
    # Symbols
    ASSIGN        = auto() #✅
    DOT           = auto() #✅
    QUESTION_MARK = auto() #✅
    COMMA         = auto() #✅

    # Arithmetic operators
    PLUS          = auto() #✅
    MINUS         = auto() #✅
    ASTERISK      = auto() #✅
    SLASH         = auto() #✅
    EXPONENT      = auto() #✅ ✅
    MODULO        = auto() #✅
    DOUBLE_SLASH  = auto() #✅

    # Logical comparison
    EQUALS        = auto() #✅
    NOT_EQUAL     = auto() #✅ ✅
    MORE_THAN     = auto() #✅
    LESS_THAN     = auto() #✅
    MORE_EQUAL    = auto() #✅ ✅
    LESS_EQUAL    = auto() #✅ ✅
    # Logical operators
    NOT           = auto() #✅
    AND           = auto() #✅
    OR            = auto() #✅
    XOR           = auto() #✅
    # Logical literals
    TRUE          = auto() #✅
    FALSE         = auto() #✅

    # Delimeters
    OPEN_PAREN    = auto() #✅
    CLOSE_PAREN   = auto() #✅
    OPEN_CURLY    = auto() #✅
    CLOSE_CURLY   = auto() #✅
    OPEN_BRACK    = auto() #✅
    CLOSE_BRACK   = auto() #✅
    SEMICOLON     = auto() #✅

    def Name(self):
        return self.name.lower()

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
        case _:
            return f"unmatched symbol: {tokenKind.name}"

class Token:
    def __init__(self, tokenKind: TokenKind, value: str = "", index: int = -1):
        self.kind = tokenKind
        self.value = value
        self.index = index
    
    def __repr__(self):
        return f"{self.kind.Name()} ({self.value})"
    
    def is_a(self, *options: tuple[TokenKind, ...]):
        return self.kind in options
    
    def debug(self):
        print(f"{self.kind.Name()} ({self.value})")

def newToken(kind: TokenKind, value: str):
    return Token(kind, value)

TYPES: list[TokenKind] = [
    TokenKind.INT,
    TokenKind.STR,
    TokenKind.FLOAT,
    TokenKind.BOOL,
    TokenKind.CHAR,
    TokenKind.ANY,
    TokenKind.NIL
]

CONTROL_FLOW = [
    TokenKind.IF,
    TokenKind.ELSE,
    TokenKind.ELSIF,
    TokenKind.WHILE,
    TokenKind.UNTIL,
    TokenKind.FOR,
    TokenKind.FOREACH
]

LITERALS = [
    TokenKind.INTEGER,
    TokenKind.DECIMAL,
    TokenKind.STRING,
    TokenKind.TRUE,
    TokenKind.FALSE
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
    TokenKind.LESS_EQUAL
)
LOGICAL_OPS = (
    TokenKind.NOT,
    TokenKind.AND,
    TokenKind.OR,
    TokenKind.XOR,
)