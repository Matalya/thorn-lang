from Token import *
from Token import TokenKind as TK

EOF: str = "\0"

class Lexer:
    def __init__(self, src:str, pos:int = 0, tokens:list = []):
        self.source = src
        self.pos = pos
        self.tokens = tokens
    def current(self) -> str:
        if self.pos >= len(self.source):
            return "\0"
        return self.source[self.pos]
    
    def printTokens(self, printSource: bool = False):
        if printSource:
            print(self.source, end = "\n\n")
        for token in self.tokens:
            if token != None:
                token.debug()
            else:
                print("None")
    
    def add(self, token: Token):
        if isinstance(token, Token):
            self.tokens.append(token)
        else:
            tokenKind: TokenKind = token # for better readability
            self.tokens.append(Token(tokenKind, symbolize(tokenKind), self.pos))
    
    def advance(self, amount = 1):
        self.pos += amount

    def peek(self, offset: int = 1):
        if self.pos + offset >= len(self.source):
            return EOF
        return self.source[self.pos + offset]
    
    def peek_str(self, amount: int):
        if self.pos + amount >= len(self.source):
            return EOF
        return self.source[self.pos + 1:self.pos + 1 + amount]
    
    def tokenize_number(self) -> Token:
        start = self.pos
        while self.current().isdigit():
            self.advance()
            if self.current() == "." and self.peek().isdigit():
                self.advance()
                while self.current().isdigit():
                    self.advance()
                value = self.source[start:self.pos]
                return Token(TK.DECIMAL, value, start)
        value = self.source[start:self.pos]
        return Token(TK.INTEGER, value, start)
    
    def tokenize_string(self) -> Token:
        start = self.pos
        self.pos += 1
        while self.current() != "\"":
            self.advance()
        self.advance()
        value = self.source[start:self.pos]
        return Token(TK.STRING, value, start)
    
    def tokenize_alpha(self):
        start = self.pos
        while self.current().isalpha() or self.current() == "_":
            self.advance()
        Value = self.source[start:self.pos]
        
        def lookup_alpha(alpha):
            if alpha == "c" and self.peek() == "\"":
                self.advance()
                return TK.COMPOSITE_STR
            else:
                match alpha:
                    case "int" | "ᛁᚾᛏ":
                        return TK.INT
                    case "str" | "ᛋᛏᚱ" | "ᛥᚱ":
                        return TK.STR
                    case "float" | "ᚠᛚᚩᛏ":
                        return TK.FLOAT
                    case "bool" | "ᛒᚣᛚ":
                        return TK.BOOL
                    case "char" | "ᚳᚻᚪᚱ":
                        return TK.CHAR
                    case "any" | "ᛖᚾᛁ":
                        return TK.ANY
                    case "nil" | "ᚾᛁᛚ":
                        return TK.NIL
                    case "true" | "ᛏᚱᚣ":
                        return TK.TRUE
                    case "false" | "ᚠᛟᛚᛋ":
                        return TK.FALSE
                    case "and" | "ᚫᚾᛞ":
                        return TK.AND
                    case "or" | "ᛟᚱ":
                        return TK.OR
                    case "xor" | "ᛉᛟᚱ":
                        return TK.XOR
                    case "nor" | "ᚾᛟᚱ":
                        return TK.NOR
                    case "nand" | "ᚾᚫᚾᛞ":
                        return TK.NAND
                    case _:
                        return TK.IDENTIFIER

        return Token(lookup_alpha(Value), Value, index = start)
    
    def Tokenize(self): # Where the magic happens B)
        while self.current() != EOF:
            ch = self.current()
            if ch.isspace():
                self.advance()
                continue # Ignore dat shee
            elif ch == "c" and self.peek() == "\"":
                self.add(TK.COMPOSITE_STR)
                self.advance(1)
                self.add(self.tokenize_string())
            elif ch.isdigit():
                self.add(self.tokenize_number())
            elif ch.isalpha():
                self.add(self.tokenize_alpha())
            else:
                match ch:
                    case "+":
                        self.add(TK.PLUS)
                    case "-":
                        self.add(TK.MINUS)
                    case "*":
                        if self.peek() == "*":
                            self.add(TK.EXPONENT)
                            self.advance()
                        else:
                            self.add(TK.ASTERISK)
                    case "^":
                        self.add(TK.EXPONENT)
                    case "/":
                        if self.peek() == "/":
                            self.add(TK.DOUBLE_SLASH)
                            self.advance()
                        else:
                            self.add(TK.SLASH)
                    case "\"":
                        self.add(self.tokenize_string())
                    case "!":
                        if self.peek() == "=":
                            self.advance()
                            self.add(TK.NOT_EQUAL)
                        else:
                            self.add(TK.DEBUG_UNKNOWN)
                    case "?":
                        self.add(TK.QUESTION_MARK)
                    case ".":
                        self.add(TK.DOT)
                    case "=":
                        if self.peek() == "=":
                            self.add(TK.EQUALS)
                            self.advance()
                        else:
                            self.add(TK.ASSIGN)
                    case ";":
                        self.add(TK.SEMICOLON)
                    case "(":
                        self.add(TK.OPEN_PAREN)
                    case ")":
                        self.add(TK.CLOSE_PAREN)
                    case "[":
                        self.add(TK.OPEN_BRACK)
                    case "]":
                        self.add(TK.CLOSE_BRACK)
                    case "{":
                        self.add(TK.OPEN_CURLY)
                    case "}":
                        self.add(TK.CLOSE_CURLY)
                    case "%":
                        self.add(TK.MODULO)
                    case "≠":
                        self.add(TK.NOT_EQUAL)
                    case ">":
                        if self.peek() == "=":
                            self.add(TK.GREATER_EQUAL)
                        else:
                            self.add(TK.GREATER_THAN)
                    case "<":
                        if self.peek() == "=":
                            self.add(TK.LESS_EQUAL)
                        else:
                            self.add(TK.LESS_THAN)
                    case "≥":
                        self.add(TK.GREATER_EQUAL)
                    case "≤":
                        self.add(TK.LESS_EQUAL)
                    case "":
                        pass
                    case "":
                        pass
                    case _:
                        self.add(TK.DEBUG_UNKNOWN)
                self.advance()
        self.add(TK.EOF_KIND)

def main():
    with open("./samples/lexer-test.ᚦ", encoding="utf8") as file:
        lexer = Lexer(file.read())
        lexer.Tokenize()
        lexer.printTokens(printSource = True)

if __name__ == "__main__":
    main()