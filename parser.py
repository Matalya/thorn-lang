from Token import *
from Token import TYPES
from Token import TokenKind as TK
from enum import Enum, auto
from lexer import Lexer



class Type(Enum):
    INT = auto()
    STR = auto()
    CHAR = auto()
    FLOAT = auto()
    BOOL = auto()
    ANY = auto()
    NIL = auto()
    UNINITIALIZED = auto()

    def __str__(self):
        return self.name.lower()



def mapTKtoType(tokenKind: TokenKind) -> Type:
    match tokenKind:
        case TK.INT: return Type.INT
        case TK.STR: return Type.STR
        case TK.FLOAT: return Type.FLOAT
        case TK.BOOL: return Type.BOOL
        case TK.CHAR: return Type.CHAR
        case TK.ANY: return Type.ANY
        case TK.NIL: return Type.NIL
        case _: raise ValueError(f"Unknown type token: {tokenKind}")

def extractTypeFromLitToken(literalToken: Token) -> Type:
    match literalToken:
        case TK.INTEGER: return Type.INT
        case TK.DECIMAL: return Type.FLOAT
        case TK.STRING: return Type.STR
        case TK.TRUE | TK.FALSE: return Type.BOOL
        case _: raise ValueError(f"Token not recognized as literal: {literalToken}")

class Node:
    pass

class Program(Node):
    def __init__(self, statements: list):
        self.statements: list = statements
    
    def __repr__(self):
        return "tf you want me to say? It's the ENTIRE program, I can't print that!"
    
    def represent(self, depth = 5):
        preview = "\n    ".join(repr(stmt) for stmt in self.statements[:depth])
        more = "..." if len(self.statements) > depth else ""
        return f"Program:\n    {preview}\n    {more}"

class varDeclaration(Node):
    def __init__(self, varType : Type, varName: str, varValue: str = None):
        self.varType = varType
        self.varName = varName
        self.varValue = varValue
    
    def __str__(self):
        value = "" if self.varValue is UNINITIALIZED else f" = {self.varValue}"
        return f"varDeclaration: {self.varType.name.lower()} {self.varName}{value};"

class Literal(Node):
    def __init__(self, litType: Type, litValue: str):
        self.litType = litType
        self.litValue = litValue
    
    def __str__(self):
        return f"Literal: {self.litValue} ({self.litType})"

class Uninitialized(Node):
    def __init__(self, type: Type = Type.UNINITIALIZED):
        self.type = type
    
    def __repr__(self):
        return "<uninitialized>"
    
    def __str__(self):
        return "<uninitialized>"

UNINITIALIZED = Uninitialized()

class Parser:
    def __init__(self, tokens: list):
        self.tokens: list = tokens
        self.pos = 0
        self.tokenCount = len(self.tokens)
    
    def __repr__(self):
        return f"tokens: {"yes" if self.tokens else "no"}"
        
    
    # Helper functions
    def advance(self):
        self.pos += 1
    
    def current(self) -> Token | None:
        return self.tokens[self.pos] if self.pos < self.tokenCount else None
    
    def current_is(self, kind: TokenKind) -> bool:
        current = self.current()
        if current == None:
            return False
        return current.kind == kind
    
    def peek(self, offset: int = 1) -> Token | None:
        index = self.pos + offset
        return self.tokens[index] if index < self.tokenCount else None
    
    def match(self, *kinds: tuple) -> Token | None:
        if isinstance(kinds[0], list):
            raise ValueError("List passed instead of variadic arguments")
        if self.current() and self.current().kind in kinds:
            token = self.current()
            self.advance()
            return token
        return None
    
    def expect(self, kind: Token, message: str = "Unexpected token") -> Token:
        token = self.match(kind)
        if token == None:
            raise SyntaxError(f"{message}: expected {kind}, got {self.current().kind}")
        return Token
    
    def parse_evaluation(self):
        current = self.current()
        if self.current_is(TK.COMPOSITE_STR):
            self.advance() #current after this should be a string
            pass
        elif current.kind in LITERALS: # then it's a literal
            return Literal(extractTypeFromLitToken(current.kind), current.value)
        else: # it's probably an operation or other kind of compound evaluation
            pass

            
        
    def parse_instruction(self):
        pass

    def parse_assignment(self, type: Token):
        current = self.current()
        next = self.peek()
        varType = mapTKtoType(type.kind)
        varName = self.expect(TK.IDENTIFIER)
        if current.kind == TK.ASSIGN:
            self.advance()
            self.parse_evaluation()
        elif self.current().kind == TK.SEMICOLON:
            varValue = UNINITIALIZED
            self.advance()
        
    
    # Parsing logic
    def parse(self) -> Program:
        for token in self.tokens:
            if token == None:
                raise SyntaxError("Unexpected value: None")
            if self.match(*TYPES):
                current = self.current()
                self.advance()
                self.parse_instruction(current)
            elif self.match():
                pass
            
"""
with open("./samples/lexer-test.ᚦ", encoding="utf8") as file:
    lexer = Lexer(file.read())
    lexer.Tokenize()
    parser = Parser(lexer.tokens)
    ast = parser.parse()
"""