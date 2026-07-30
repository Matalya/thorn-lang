from Token import *
from Token import TokenKind as TK
from lexer import Lexer
from th_ast import *

class TokenError(Exception):
    pass

class TokenKindError(Exception):
    pass

class EndOfFile(Exception):
    pass

class UnpairedParenthesis(Exception):
    pass

class InvalidEvlauation(Exception):
    pass

def mapTokenToOperator(token: Token, isMinus: bool = False) -> Op:
    match token.kind:
        # Arithmetic
        case TK.EXPONENT: return Op.POWER
        case TK.ASTERISK: return Op.MULT
        case TK.SLASH: return Op.DIV
        case TK.MODULO: return Op.MOD
        case TK.DOUBLE_SLASH: return Op.FLOOR_DIV
        case TK.PLUS: return Op.ADD
        case TK.MINUS: return Op.SUB if isMinus else Op.NEG
        # Comparison
        case TK.EQUALS: return Op.EQUALS
        case TK.NOT_EQUAL: return Op.NOT_EQUAL
        case TK.MORE_THAN: return Op.MORE_THAN
        case TK.LESS_THAN: return Op.LESS_THAN
        case TK.MORE_EQUAL: return Op.MORE_EQUAL
        case TK.LESS_EQUAL: return Op.LESS_EQUAL
        # Boolean
        case TK.NOT: return Op.NOT
        case TK.AND: return Op.AND
        case TK.OR: return Op.OR
        case TK.XOR: return Op.XOR
        case _: raise TokenKindError(f"mapTokenToOperator(): No Token Kind recognized: {token.kind}")

def mapKindToType(tokenKind: TokenKind) -> Type:
    match tokenKind:
        case TK.INT | TK.INTEGER | TK.DECIMAL: return Type.INT
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

class TokenStream:
    def __init__(self, tokens: list[Token]):
        self.tokens: list[Token] = tokens
        self.pos = 0
        self.tokenCount = len(self.tokens)
    
    # Helper functions
    def current(self) -> Token:
        """does not mutate index"""
        if self.pos >= self.tokenCount or self.pos < 0:
            raise IndexError(f"current(): program index {self.pos} out of bounds")
        return self.tokens[self.pos]
    
    def previous(self) -> Token:
        if self.pos > 0:
            return self.tokens[self.pos - 1]
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
            """print("Advanced; current:", end = " ")
            self.current().debug()"""
        elif self.current().kind == TK.EOF_KIND:
            print("advance(): reached the end of the token stream")
            raise EndOfFile
        else:
            raise IndexError(f"advance(): Cannot advance to token {self.pos + n}/{self.tokenCount}")
        
    
    def peek(self, offset: int = 1) -> Token | None:
        """does not mutate index"""
        index = self.pos + offset
        return self.tokens[index] if index < self.tokenCount else None

    def match(self, *kinds: TokenKind) -> Token | None:
        """mutates index after matching"""
        if isinstance(kinds[0], list):
            print("match(): List passed instead of variadic argumentokenStream, idiot")
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
            

####################################### PARSER CLASS #######################################

# START PARSER CLASS
class Parser:
    def __init__(self, tokenStream: TokenStream):
        self.tokenStream = tokenStream

    def __repr__(self):
        return f"tokens: {"yes" if self.tokenStream else "no"}"

    def parse(self) -> Program:
        program = Program()

        while not self.tokenStream.current_is(TK.EOF_KIND):
            program.addNode(self.parse_statement())

        return program
    def current(self):
        return self.tokenStream.current()
    def expect(self, *args, **kwargs):
        return self.tokenStream.expect(*args, **kwargs)
    def match(self, *args):
        return self.tokenStream.match(*args)
    def expectEqualSign(self):
        return self.tokenStream.expect(TK.ASSIGN, message = "Equal sign not found.")
    def expectSemicolon(self):
        return self.tokenStream.expect(TK.SEMICOLON, message = "Semicolon not found.")
 #################################### parsing functions ####################################
    def parse_statement(self):
        current = self.current()

        if current.kind in DATA_TYPES:
            return self.parseVarDecl()

        if current.kind == TK.IDENTIFIER:
            nextToken = self.tokenStream.peek()

            if nextToken is None:
                raise SyntaxError(
                    f"Unexpected end of input after identifier '{current.value}'."
                )

            if nextToken.kind == TK.ASSIGN:
                return self.parseVarAssign()

            if nextToken.kind == TK.OPEN_PAREN:
                return self.parseFuncCall()

            raise SyntaxError(
                f"Expected '=' or '(' after identifier '{current.value}'."
            )

        raise SyntaxError(
            f"Unexpected token {current.kind} ({current.value!r}) "
            f"at token index {self.tokenStream.pos}."
        )

    def parseVarDecl(self):
        # at this point it's still on int
        varDeclType: Token = self.expect(*DATA_TYPES, message = "Type keyword (int, str…) not found")
        varDeclIdent: Token = self.expect(TK.IDENTIFIER, message = "Identifier not found")
        if self.match(TK.ASSIGN):
            varDeclVal = self.parseExpression()
        else:
            varDeclVal = UNINITIALIZED
        self.expect(TK.SEMICOLON, message = "Semicolon not found")
        return VarDeclaration(mapKindToType(varDeclType.kind), Identifier(varDeclIdent.value), varDeclVal)

    def parseExpression(self):
        token = self.expect(TK.INTEGER, TK.DECIMAL, TK.STRING, TK.TRUE, TK.FALSE, TK.IDENTIFIER, message="Literal or identifier not found."
        )

        if token.kind == TK.IDENTIFIER:
            return Identifier(token.value)

        return Literal(
            mapLiteralToType(token),
            token.value
        )

    def parseVarAssign(self):
        varAssignIdent: Token = self.expect(TK.IDENTIFIER, message = "Identifier not found.")
        self.expectEqualSign()
        varAssignVal: Node = self.parseExpression()
        self.expectSemicolon()

        return VarAssign(Identifier(varAssignIdent.value), varAssignVal)

    def parseFuncCall(self):
        funcName: Token = self.expect(
            TK.IDENTIFIER,
            message="Function identifier not found."
        )

        self.expect(
            TK.OPEN_PAREN,
            message="Opening parenthesis not found after function name."
        )

        args = []

        if self.current().kind != TK.CLOSE_PAREN:
            args.append(self.parseExpression())

            while self.match(TK.COMMA):
                args.append(self.parseExpression())

        self.expect(
            TK.CLOSE_PAREN,
            message="Closing parenthesis not found after function arguments."
        )

        return FunctionCall(
            Identifier(funcName.value),
            args
        )

# END PARSER CLASS

with open("./samples/lexer-test.ᚦ", encoding="utf8") as file:
    lexer = Lexer(file.read())
    lexer.Tokenize()

    parserTokens = [
        token
        for token in lexer.tokenStream
        if token.kind != TK.COMMENT
    ]

    tokenStream = TokenStream(parserTokens)
    parser = Parser(tokenStream)
    program = parser.parse()

    print(program)