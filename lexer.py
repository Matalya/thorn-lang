from Token import *
from Token import TokenKind as TK

class LexerError(Exception):
    pass

EOF: str = "\0"

class Lexer:
    def __init__(self, src:str, pos:int = 0, tokenStream: list[Token] | None = None):
        self.source: str = src
        self.pos: int = pos
        self.tokenStream: list[Token] = [] if tokenStream is None else tokenStream

    def current(self) -> str:
        if self.pos >= len(self.source):
            return "\0"
        return self.source[self.pos]
    
    def printTokens(self, printSource: bool = False):
        if printSource:
            print(self.source, end = "\n\n")
        for token in self.tokenStream:
            token.debug()
    
    def add(self, token: Token | TokenKind):
        if isinstance(token, Token):
            self.tokenStream.append(token)
        else:
            tokenKind: TokenKind = token # for better readability
            self.tokenStream.append(Token(tokenKind, symbolize(tokenKind), self.pos))

    def add_symbol(self, kind: TokenKind, start: int):
        """Add a symbol whose first character is at ``start``."""
        self.tokenStream.append(
            Token(kind, symbolize(kind), start, self.pos + 1)
        )
    
    def advance(self, amount: int = 1):
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

    def tokenize_comment(self) -> Token:
        start = self.pos

        while self.current() not in ("\n", EOF):
            self.advance()

        value = self.source[start:self.pos]
        return Token(TK.COMMENT, value, start)
    
    def tokenize_quoted(
        self,
        quote: str,
        kind: TokenKind
    ) -> Token:
        start = self.pos
        self.advance()  # Skip opening quote.

        escaped = False

        while True:
            ch = self.current()

            if ch == EOF:
                raise LexerError(
                    f"Unterminated literal beginning at source index {start}."
                )

            if escaped:
                escaped = False
                self.advance()
                continue

            if ch == "\\":
                escaped = True
                self.advance()
                continue

            if ch == quote:
                self.advance()
                break

            if quote == "'" and ch == "\n":
                raise LexerError(
                    f"Character literal cannot contain a newline "
                    f"at source index {start}."
                )

            self.advance()

        value = self.source[start:self.pos]
        return Token(kind, value, start)
    
    def tokenize_alpha(self) -> Token:
        start = self.pos

        while self.current().isalnum() or self.current() == "_":
            self.advance()

        value = self.source[start:self.pos]
        kind = KEYWORDS.get(value, TK.IDENTIFIER)

        return Token(kind, value, start)

    def tokenize_composite_string(self) -> Token:
        start = self.pos

        self.advance()  # Move from c/ᚳ to opening quote.

        if self.current() != '"':
            raise LexerError(
                f"Expected quote after composite-string prefix "
                f"at source index {start}."
            )

        self.advance()  # Skip the outer opening quote.

        escaped = False
        braceDepth = 0
        interpolationQuote: str | None = None

        while True:
            ch = self.current()

            if ch == EOF:
                raise LexerError(
                    f"Unterminated composite string beginning "
                    f"at source index {start}."
                )

            if escaped:
                escaped = False
                self.advance()
                continue

            if ch == "\\":
                escaped = True
                self.advance()
                continue

            if braceDepth == 0:
                if ch == '"':
                    self.advance()
                    break

                if ch == "{":
                    braceDepth = 1
                    self.advance()
                    continue

                if ch == "}":
                    raise LexerError(
                        f"Unexpected closing brace in composite string "
                        f"at source index {self.pos}."
                    )

                self.advance()
                continue

            # Inside an interpolation, quoted literals may contain
            # braces without changing the interpolation depth.
            if interpolationQuote is not None:
                if ch == interpolationQuote:
                    interpolationQuote = None

                self.advance()
                continue

            if ch in ('"', "'"):
                interpolationQuote = ch
                self.advance()
                continue

            if ch == "{":
                braceDepth += 1

            elif ch == "}":
                braceDepth -= 1

            self.advance()

        value = self.source[start:self.pos]
        return Token(TK.COMPOSITE_STR, value, start)

    def Tokenize(self): # Where the magic happens B)
        while self.current() != EOF:
            ch = self.current()
            if ch.isspace():
                self.advance()
                continue # Ignore dat shee

            elif ch == "#":
                self.add(self.tokenize_comment())

            elif ch in ("c", "ᚳ") and self.peek() == '"':
                self.add(self.tokenize_composite_string())
            elif ch.isdigit():
                self.add(self.tokenize_number())
            elif ch.isalpha() or ch == "_":
                self.add(self.tokenize_alpha())

            elif ch == '"':
                self.add(
                    self.tokenize_quoted('"', TK.STRING)
                )

            elif ch == "'":
                self.add(
                    self.tokenize_quoted("'", TK.CHAR_LITERAL)
                )

            else:
                match ch:
                    case "+":
                        if self.peek() == "=":
                            self.add(TK.PLUS_ASSIGN)
                            self.advance()
                        else:
                            self.add(TK.PLUS)
                    case "-":
                        if self.peek() == "=":
                            self.add(TK.MINUS_ASSIGN)
                            self.advance()
                        elif self.peek() == ">":
                            start = self.pos
                            self.advance()
                            self.add_symbol(TK.ARROW, start)
                        else:
                            self.add(TK.MINUS)
                    case "*":
                        start = self.pos
                        if self.peek() == "*":
                            self.advance()

                            if self.peek() == "=":
                                self.advance()
                                self.add_symbol(TK.EXPONENT_ASSIGN, start)
                            else:
                                self.add_symbol(TK.EXPONENT, start)

                        elif self.peek() == "=":
                            self.add(TK.MULT_ASSIGN)
                            self.advance()

                        else:
                            self.add(TK.ASTERISK)
                    case "^":
                        if self.peek() == "=":
                            self.add(TK.EXPONENT_ASSIGN)
                            self.advance()
                        else:
                            self.add(TK.EXPONENT)
                    case "/":
                        start = self.pos
                        if self.peek() == "/":
                            self.advance()

                            if self.peek() == "=":
                                self.advance()
                                self.add_symbol(TK.FLOOR_DIV_ASSIGN, start)
                            else:
                                self.add_symbol(TK.DOUBLE_SLASH, start)

                        elif self.peek() == "=":
                            self.add(TK.DIV_ASSIGN)
                            self.advance()

                        else:
                            self.add(TK.SLASH)
                    case "!":
                        if self.peek() == "=":
                            start = self.pos
                            self.advance()
                            self.add_symbol(TK.NOT_EQUAL, start)
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
                    case ":":
                        self.add(TK.COLON)
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
                        if self.peek() == "=":
                            self.add(TK.MODULO_ASSIGN)
                            self.advance()
                        else:
                            self.add(TK.MODULO)
                    case "≠":
                        self.add_symbol(
                            TK.NOT_EQUAL,
                            self.pos
                        )
                    case ">":
                        if self.peek() == "=":
                            start = self.pos
                            self.advance()
                            self.add_symbol(TK.MORE_EQUAL, start)
                        else:
                            self.add(TK.MORE_THAN)

                    case "<":
                        if self.peek() == "=":
                            start = self.pos
                            self.advance()
                            self.add_symbol(TK.LESS_EQUAL, start)
                        else:
                            self.add(TK.LESS_THAN)
                    case "≥":
                        self.add_symbol(
                            TK.MORE_EQUAL,
                            self.pos
                        )
                    case "≤":
                        self.add_symbol(
                            TK.LESS_EQUAL,
                            self.pos
                        )
                    case ",":
                        self.add(TK.COMMA)
                    case "|":
                        self.add(TK.PIPE)
                    case _:
                        self.add(TK.DEBUG_UNKNOWN)
                self.advance()
        self.tokenStream.append(
            Token(
                TK.EOF_KIND,
                EOF,
                self.pos,
                self.pos
            )
        )

def main(): 
    with open("./samples/lexer-test.ᚦ", encoding="utf8") as file:
        lexer = Lexer(file.read())
        lexer.Tokenize()
        lexer.printTokens(printSource = True)

if __name__ == "__main__":
    main()
