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
    def __init__(self, statements: list = []):
        self.statements: list = statements
    
    def __repr__(self):
        return "tf you want me to say? It's the ENTIRE program, I can't print that!"
    
    def represent(self, depth = 5):
        preview = "\n    ".join(repr(stmt) for stmt in self.statements[:depth])
        more = "..." if len(self.statements) > depth else ""
        if not self.statements:
            print("Program empty")
        else:
            print(f"Program:\n    {preview}\n    {more}")
    
    def addNode(self, node: Node):
        self.statements.append(node)

############################################ NODES ############################################

class VarDeclaration(Node):
    def __init__(self, varType : Type, varName: str, varValue: str = None):
        self.varType = varType
        self.varName = varName
        self.varValue = varValue
    
    def __repr__(self):
        value = "" if self.varValue is UNINITIALIZED else f" = {self.varValue}"
        return f"varDeclaration: {self.varType.name.lower()} {self.varName}{value};"

class Literal(Node):
    def __init__(self, litType: Type, litValue: str):
        self.litType: Type = litType
        self.litValue: str = litValue
    
    def strfy(self):
        return "\"" if self.litType == Type.STR else ""
    def __repr__(self):
        return f"Literal({self.litType}:{self.strfy()}{self.litValue}{self.strfy()})"

class CST(Enum):
    STRING_COMPONENT = auto()
    EVALUATION_COMPONENT = auto()

class stringComponent(Node):
    def __init__(self, type: CST, value: str):
        self.type: CST = type
        self.value: Literal = Literal(Type.STR, value) if self.type == CST.STRING_COMPONENT else value
    def __repr__(self):
        return f"{"EvalComp" if self.type == CST.EVALUATION_COMPONENT else ""}{self.value}"

class CompositeString(Node):
    def __init__(self, string: str):
        
        def show_context(string: str, index: int, padding: int = 5):
            lower = index - padding
            upper = index + padding
            if lower > 0 and upper < len(string):
                return string[lower : upper]
            else:
                return string
            
        self.components: list[str] = list()
        acc: str = str()
        evalMode: bool = False
        openbraceindex = 0
        for i in range(len(string)):
            if string[i] == "\"":
                continue
            elif string[i] == "{":
                evalMode = True
                if acc:
                    self.components.append(stringComponent(CST.STRING_COMPONENT, acc))
                acc = ""
                openbraceindex = i
            elif string[i] == "}":
                evalMode = False
                self.components.append(stringComponent(CST.EVALUATION_COMPONENT, "{" + acc + "}"))
                acc = ""
            else:
                acc += string[i]
        if acc:
            self.components.append(stringComponent(CST.STRING_COMPONENT, acc)) # assumed string cuz if it was an eval it would've gotten flushed by "}"
        if evalMode:
            raise SyntaxWarning(f"Unclosed brace @ {openbraceindex}: …{show_context(string, openbraceindex)}…")
    
    def __repr__(self):
        return str(self.components)


class Uninitialized(Node):
    def __init__(self, type: Type = Type.UNINITIALIZED):
        self.type: Type = type
    
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
        print("Advanced; current:", end = " ")
        self.current().debug()
    
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
        return token

    def parse_instruction(self, current: Token):
        pass
    
    def parse_evaluation(self):
        if self.current_is(TK.COMPOSITE_STR):
            self.advance()
            if self.current_is(TK.STRING):
                return CompositeString(self.current().value)
        elif self.current().kind in LITERALS: # then it's a literal
            self.advance()
            return Literal(extractTypeFromLitToken(self.current().kind), self.current().value)
        else: # it's probably an operation or other kind of compound evaluation
            pass

    def parse_varDeclaration(self, type: Token):
        varType = mapTKtoType(type.kind)
        varName = self.expect(TK.IDENTIFIER).value
        if self.current().kind == TK.ASSIGN:
            self.advance()
            varValue = self.parse_evaluation()
        elif self.current().kind == TK.SEMICOLON:
            varValue = UNINITIALIZED
            self.advance()
        elif not (self.current_is(TK.ASSIGN) or self.current_is(TK.SEMICOLON)):
            raise SyntaxError("Expected semicolon or assignment at variable declaration")
        else:
            raise SyntaxError(f"Unknown token at variable declaration: {self.current()}")
        return VarDeclaration(varType, varName, varValue)
    
    def parse_controlFlow():
        pass
        
    
    # Parsing logic
    def parse(self) -> Program:
        program = Program()
        for token in self.tokens:
            if token == None:
                raise SyntaxError("Unexpected value: None")
            if current := self.match(*TYPES):
                program.addNode(self.parse_varDeclaration(current))
            elif current := self.match(*CONTROL_FLOW):
                program.addNode(self.parse_control_flow(current))
        return program
            

with open("./samples/lexer-test.ᚦ", encoding="utf8") as file:
    lexer = Lexer(file.read())
    lexer.Tokenize()
    parser = Parser(lexer.tokens)
    program = parser.parse()
    program.represent()