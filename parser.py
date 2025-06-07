from Token import *
from Token import TokenKind as TK
from enum import Enum, auto
from lexer import Lexer
from thast import *

class TokenError(Exception):
    pass

class TokenKindError(Exception):
    pass

class EndOfFile(Exception):
    pass

def mapTokenToOperator(token: Token) -> Op:
    match token.kind:
        # Arithmetic
        case TK.EXPONENT: return Op.POWER
        case TK.ASTERISK: return Op.MULT
        case TK.SLASH: return Op.DIV
        case TK.MODULO: return Op.MOD
        case TK.DOUBLE_SLASH: return Op.FLOOR_DIV
        case TK.PLUS: return Op.ADD
        case TK.MINUS: return Op.SUB
        # Comparison
        case TK.EQUALS: return Op.EQUALS
        case TK.NOT_EQUAL: return Op.NOT_EQUAL
        case TK.MORE_THAN: return Op.MORE_THAN
        case TK.LESS_THAN: return Op.LESS_THAN
        case TK.MORE_EQUAL: return Op.MORE_EQUAL
        case TK.LESS_EQUAL: return Op.LESS_EQUAL
        # Boolean
        case TK.NOT: return Op.NEG
        case TK.AND: return Op.AND
        case TK.OR: return Op.OR
        case TK.XOR: return Op.XOR
        case _: raise TokenKindError(f"mapTokenToOperator(): No Token Kind recognized: {token.kind}")

def mapKindToType(tokenKind: TokenKind) -> Type:
    match tokenKind:
        case TK.INT: return Type.INT
        case TK.STR: return Type.STR
        case TK.FLOAT: return Type.FLOAT
        case TK.BOOL: return Type.BOOL
        case TK.CHAR: return Type.CHAR
        case TK.ANY: return Type.ANY
        case TK.NIL: return Type.NIL
        case _: raise TokenKindError(f"mapKindToType(): Unknown or invalid type token {tokenKind}")

def mapLiteralToType(literalToken: Token) -> Type:
    match literalToken.kind:
        case TK.INTEGER: return Type.INT
        case TK.DECIMAL: return Type.FLOAT
        case TK.STRING: return Type.STR
        case TK.TRUE | TK.FALSE: return Type.BOOL
        case _: raise TokenKindError(f"mapLiteralToType(): {literalToken} Token not recognized as literal")


def safe_get_prev(tokenStream: list[Token | Node], index: int):
    """Handles if current operand is a Token or already a nested operation"""
    if isinstance(tokenStream[index - 1], Node):
        return tokenStream[index - 1]
    elif isinstance(tokenStream[index - 1], Token):
        return tokenStream[index - 1].value
def safe_get_next(tokenStream: list[Token | Node], index: int):
    """Handles if current operand is a Token or already a nested operation"""
    if isinstance(tokenStream[index + 1], Node):
        return tokenStream[index + 1]
    elif isinstance(tokenStream[index + 1], Token):
        return tokenStream[index + 1].value

####################################### PARSER CLASS #######################################
class Parser:
    def __init__(self, tokenStream: list[Token]):
        self.tokenStream: list[Token] = tokenStream
        self.pos = 0
        self.tokenCount = len(self.tokenStream)

    def __repr__(self):
        return f"tokens: {"yes" if self.tokenStream else "no"}"
    
    # Helper functions
    def current(self) -> Token:
        """does not mutate index"""
        if self.pos >= self.tokenCount or self.pos < 0:
            raise IndexError(f"current(): program index {self.pos} out of bounds")
        return self.tokenStream[self.pos]
    
    def previous(self) -> Token:
        if self.pos > 0:
            return self.tokenStream[self.pos - 1]
        raise IndexError(f"previous(): cannot access token @ index -1")
    
    def current_is(self, *kinds: TokenKind) -> bool:
        """does not mutate index"""
        return self.current().kind in kinds
    
    def token_is(self, token: Token, *kinds: TokenKind) -> bool:
        """does not mutate index"""
        try:
            return token.kind in kinds
        except AttributeError:
            raise TokenError(f"token_is(): invalid token parameter {token}")
    
    def advance(self, n = 1):
        """Mutates index"""
        if self.pos < self.tokenCount - n:
            self.pos += n
            print("Advanced; current:", end = " ")
            self.current().debug()
        elif self.current().kind == TK.EOF_KIND:
            print("advance(): reached the end of the token stream")
            raise EndOfFile
        else:
            raise IndexError(f"advance(): Cannot advance to token {self.pos + n}/{self.tokenCount}")
    
    def retreat(self):
        if self.pos > 0:
            self.pos -= 1
            print("Retreated; current:", end = " ")
            self.current().debug()
        raise IndexError(f"retreat(): cannot retreat to {self.pos - 1}")
        
    
    def peek(self, offset: int = 1) -> Token | None:
        """does not mutate index"""
        index = self.pos + offset
        return self.tokenStream[index] if index < self.tokenCount else None

    def match(self, *kinds: TokenKind) -> Token | None:
        """mutates index after matching"""
        if isinstance(kinds[0], list):
            print("match(): List passed instead of variadic arguments, idiot")
        current = self.current()
        if current.kind in kinds:
            token = self.current()
            self.advance()
            return token
        return None
    
    def expect(self, *kinds: TokenKind, message: str = "Unexpected token") -> Token:
        """mutates index after matching"""
        token = self.match(*kinds)
        if token == None:
            current = self.current()
            current_kind = current.kind if current else "EOF"
            raise TokenError(f"{message}: expected {kinds}, got {current_kind}")
        return token
    
    def is_operator(self, token: Token) -> bool:
        return token.kind in OPERATORS

    ########################################## parsing functions ##########################################

    def parse_evaluation(self):
        predecendesSet: set[int] = set()

        # Get the present operators precendence
        flatOperationsStream: list[Token | Node] = list()
        while self.current().kind != TK.SEMICOLON:
            flatOperationsStream.append(self.current())
            if self.current_is(*OPERATORS):
                predecendesSet.add(precedence(mapTokenToOperator(self.current())))
            self.advance()
        precendencesPresent: list[int] = list(predecendesSet)
        precendencesPresent.sort()
        for Precendence in precendencesPresent:
            print(f"{Precendence}: {PRECEDENCE[Precendence]}")

        # do as many passes as there are precedences
        for currentPrecendenceIndex in range(len(precendencesPresent)):
            currentPrecendence = precendencesPresent[currentPrecendenceIndex]
            for i in range(len(flatOperationsStream) - 1):
                token = flatOperationsStream[i]
                if self.is_operator(token) and precedence(mapTokenToOperator(token)) == currentPrecendence:
                    flatOperationsStream[i - 1 : i + 2] = [
                        BinaryOp(
                            safe_get_prev(flatOperationsStream, i),
                            mapTokenToOperator(token),
                            safe_get_next(flatOperationsStream, i)
                        )
                    ]
        print(flatOperationsStream)

    def parse_varDeclaration(self) -> Node:
        varType: Type = mapKindToType(self.match(*TYPES).kind)
        varName: str = self.expect(TK.IDENTIFIER).value
        if self.current().kind == TK.ASSIGN:
            self.advance()
            varValue: Node = self.parse_evaluation()
            return VarDeclaration(varType, varName, varValue)
        elif self.current().kind == TK.SEMICOLON:
            return VarDeclaration(varType, varName) # case type var; with no initialization, autoassigned to UNINITIALIZED type
        else:
            print("what")
            
    # Parsing logic
    def parse(self) -> Program:
        program: Program = Program()
        try:
            if self.current().kind in TYPES:
                program.addNode(self.parse_varDeclaration())
        except EndOfFile:
            return program
            

with open("./samples/lexer-test.ᚦ", encoding="utf8") as file:
    lexer = Lexer(file.read())
    lexer.Tokenize()
    parser = Parser(lexer.tokenStream)
    program: Program = parser.parse()
    print(program)