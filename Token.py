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
    IF            = auto() #❌
    ELSIF         = auto() #❌
    ELSE          = auto() #❌
    WHILE         = auto() #❌
    UNTIL         = auto() #❌
    FOR           = auto() #❌
    FOREACH       = auto() #❌
    
    # Symbols
    ASSIGN        = auto() #✅
    DOT           = auto() #✅
    QUESTION_MARK = auto() #✅

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
    GREATER_THAN  = auto() #✅
    LESS_THAN     = auto() #✅
    GREATER_EQUAL = auto() #✅ ✅
    LESS_EQUAL    = auto() #✅ ✅
    # Logical operators
    AND           = auto() #✅
    OR            = auto() #✅
    XOR           = auto() #✅
    NOR           = auto() #✅
    NAND          = auto() #✅
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

def symbolize(tokenKind):
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
        case _:
            return "unmatched symbol"

class Token:
    def __init__(self, tokenKind: TokenKind, value: str = "", index = -1):
        self.kind = tokenKind
        self.value = value
        self.index = index
    
    def is_a(self, *options):
        return self.kind in options
    
    def debug(self):
        print(f"{self.kind.Name()} ({self.value})")

def newToken(kind: TokenKind, value: str):
    return Token(kind, value)

TYPES: TokenKind = (
    TokenKind.INT,
    TokenKind.STR,
    TokenKind.FLOAT,
    TokenKind.BOOL,
    TokenKind.CHAR,
    TokenKind.ANY,
    TokenKind.NIL
)

CONTROL_FLOW = (
    TokenKind.IF,
    TokenKind.ELSE,
    TokenKind.ELSIF,
    TokenKind.WHILE,
    TokenKind.UNTIL,
    TokenKind.FOR,
    TokenKind.FOREACH
)

LITERALS = (
    TokenKind.INTEGER,
    TokenKind.DECIMAL,
    TokenKind.STRING,
    TokenKind.TRUE,
    TokenKind.FALSE,
)