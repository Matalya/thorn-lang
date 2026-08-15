from functools import wraps
import pyperclip
from Token import *
from Token import TokenKind as TK
from lexer import Lexer, LexerError
from th_ast import *

class TokenError(SyntaxError):
    pass

class TokenKindError(Exception):
    pass

class EndOfFile(Exception):
    pass

class UnpairedParenthesis(Exception):
    pass

class InvalidEvlauation(Exception):
    pass


def located(parseMethod):
    """Attach the source consumed by a parser method to its returned node."""
    @wraps(parseMethod)
    def wrapper(self, *args, **kwargs):
        startPosition = self.tokenStream.pos
        start = self.current().index
        node = parseMethod(self, *args, **kwargs)

        if isinstance(node, Node) and self.tokenStream.pos > startPosition:
            node.setSpan(start, self.tokenStream.previous().end)

        return node

    return wrapper

DECLARATION_MODIFIER_KINDS = (
    TK.NEW,
    TK.GLOBAL,
    TK.CONST
)

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

def mapCompoundAssignmentToOperator(
    token: Token
) -> Op:
    match token.kind:
        case TK.PLUS_ASSIGN:
            return Op.ADD

        case TK.MINUS_ASSIGN:
            return Op.SUB

        case TK.MULT_ASSIGN:
            return Op.MULT

        case TK.DIV_ASSIGN:
            return Op.DIV

        case TK.EXPONENT_ASSIGN:
            return Op.POWER

        case TK.MODULO_ASSIGN:
            return Op.MOD

        case TK.FLOOR_DIV_ASSIGN:
            return Op.FLOOR_DIV

        case _:
            raise TokenKindError(
                f"mapCompoundAssignmentToOperator(): "
                f"Expected compound assignment token, "
                f"got {token.kind}"
            )

def mapKindToType(tokenKind: TokenKind) -> Type:
    match tokenKind:
        case TK.INT | TK.INTEGER: return Type.INT
        case TK.STR: return Type.STR
        case TK.FLOAT | TK.DECIMAL: return Type.FLOAT
        case TK.BOOL: return Type.BOOL
        case TK.CHAR: return Type.CHAR
        case TK.ANY: return Type.ANY
        case TK.NIL: return Type.NIL
        case TK.UNINITIALIZED: return Type.UNINITIALIZED
        case TK.FILE: return Type.FILE
        case TK.PYOBJECT: return Type.PYOBJECT
        case _: raise TokenKindError(f"mapKindToType(): Unknown or invalid type token {tokenKind}")

def mapLiteralToType(literalToken: Token) -> Type:
    match literalToken.kind:
        case TK.INTEGER:
            return Type.INT
        case TK.DECIMAL:
            return Type.FLOAT
        case TK.STRING:
            return Type.STR
        case TK.CHAR_LITERAL:
            return Type.CHAR
        case TK.TRUE | TK.FALSE:
            return Type.BOOL
        case TK.NIL:
            return Type.NIL
        case _:
            raise TokenKindError(
                f"mapLiteralToType(): {literalToken} Token not recognized as literal"
            )

class TokenStream:
    def __init__(self, tokens: list[Token], source: str | None = None):
        self.tokens: list[Token] = tokens
        self.source = source
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
        self.arrayLiteralDepth = 0

    def __repr__(self):
        return f"tokens: {"yes" if self.tokenStream else "no"}"

    @located
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
    def expectSemicolon(self, context: str = "statement"):
        semicolon = self.match(TK.SEMICOLON)

        if semicolon is not None:
            return semicolon

        previous = self.tokenStream.previous()
        insertionIndex = previous.end
        source = self.tokenStream.source

        if source is None:
            raise TokenError(
                f"Missing semicolon after {context} at source "
                f"index {insertionIndex}. Add ';' here."
            )

        line = source.count("\n", 0, insertionIndex) + 1
        lastNewline = source.rfind("\n", 0, insertionIndex)
        column = insertionIndex - lastNewline
        sourceLines = source.splitlines()
        sourceLine = (
            sourceLines[line - 1]
            if line <= len(sourceLines)
            else ""
        )
        gutter = len(str(line))

        raise TokenError("\n".join((
            f"Missing semicolon after {context} at line {line}, "
            f"column {column}.",
            f"{line:>{gutter}} | {sourceLine}",
            f"{' ' * gutter} | {' ' * (column - 1)}^ add ';' here",
        )))

    def tokensAreOnDifferentLines(
        self,
        left: Token,
        right: Token
    ) -> bool:
        source = self.tokenStream.source
        if source is None:
            return False
        return "\n" in source[left.end:right.index]

    def cover(self, node: Node, *children: Node) -> Node:
        spans = [child.span for child in children if child.span is not None]
        if spans:
            node.setSpan(
                min(span.start for span in spans),
                max(span.end for span in spans)
            )
        return node

    def parseEmbeddedExpression(
        self,
        source: str,
        absoluteStart: int
    ) -> Node:
        try:
            lexer = Lexer(source)
            lexer.Tokenize()
        except LexerError as error:
            raise SyntaxError(
                f"Invalid interpolation beginning at source "
                f"index {absoluteStart}: {error}"
            ) from error

        shiftedTokens = []

        for token in lexer.tokenStream:
            if token.kind == TK.COMMENT:
                continue

            shiftedTokens.append(
                Token(
                    token.kind,
                    token.value,
                    token.index + absoluteStart,
                    token.end + absoluteStart
                )
            )

        parser = Parser(
            TokenStream(shiftedTokens)
        )
        expression = parser.parseExpression()

        if not parser.tokenStream.current_is(
            TK.EOF_KIND
        ):
            unexpected = parser.current()

            raise TokenError(
                f"Unexpected token "
                f"'{unexpected.value}' in interpolation "
                f"at source index {unexpected.index}."
            )

        return expression

    def findInterpolationEnd(
        self,
        content: str,
        openingIndex: int
    ) -> int:
        depth = 1
        quote: str | None = None
        escaped = False
        index = openingIndex + 1

        while index < len(content):
            char = content[index]

            if escaped:
                escaped = False
                index += 1
                continue

            if char == "\\":
                escaped = True
                index += 1
                continue

            if quote is not None:
                if char == quote:
                    quote = None

                index += 1
                continue

            if char in ('"', "'"):
                quote = char
                index += 1
                continue

            if char == "{":
                depth += 1

            elif char == "}":
                depth -= 1

                if depth == 0:
                    return index

            index += 1

        raise SyntaxError(
            f"Unclosed interpolation beginning at "
            f"composite-string content index {openingIndex}."
        )

    def parseCompositeStringToken(
        self,
        token: Token
    ) -> CompositeString:
        # token.value includes the one-character prefix and both
        # outer quote characters: c"..." or ᚳ"...".
        content = token.value[2:-1]
        contentStart = token.index + 2
        components: list[stringComponent] = []

        textCharacters: list[str] = []
        textStart = 0
        index = 0

        def flushText(endIndex: int):
            nonlocal textCharacters

            if not textCharacters:
                return

            component = stringComponent(
                CompositeStringType.STRING_COMPONENT,
                "".join(textCharacters)
            ).setSpan(
                contentStart + textStart,
                contentStart + endIndex
            )

            components.append(component)
            textCharacters = []

        while index < len(content):
            char = content[index]

            # Escaped braces remain ordinary string contents. Keep
            # the escape sequence intact for the eventual runtime.
            if char == "\\" and index + 1 < len(content):
                textCharacters.append(char)
                textCharacters.append(
                    content[index + 1]
                )
                index += 2
                continue

            if char != "{":
                textCharacters.append(char)
                index += 1
                continue

            flushText(index)

            closingIndex = self.findInterpolationEnd(
                content,
                index
            )
            expressionSource = content[
                index + 1:closingIndex
            ]

            if not expressionSource.strip():
                raise SyntaxError(
                    f"Composite-string interpolation cannot "
                    f"be empty at source index "
                    f"{contentStart + index}."
                )

            expressionStart = contentStart + index + 1
            expression = self.parseEmbeddedExpression(
                expressionSource,
                expressionStart
            )

            components.append(
                stringComponent(
                    CompositeStringType.EVALUATION_COMPONENT,
                    expression
                ).setSpan(
                    contentStart + index,
                    contentStart + closingIndex + 1
                )
            )

            index = closingIndex + 1
            textStart = index

        flushText(len(content))

        return CompositeString(components).setSpan(
            token.index,
            token.end
        )

    def parseExpressionList(
        self,
        closingKind: TokenKind
    ) -> list[Node]:
        expressions = []

        if not self.tokenStream.current_is(closingKind):
            expressions.append(self.parseExpression())

            while self.match(TK.COMMA):
                if self.tokenStream.current_is(closingKind):
                    break

                expressions.append(self.parseExpression())

        return expressions

    @located
    def parseCallArgument(self) -> Node:
        if (
            self.tokenStream.current_is(TK.IDENTIFIER)
            and self.tokenStream.peek() is not None
            and self.tokenStream.peek().kind == TK.ASSIGN
        ):
            nameToken = self.expect(TK.IDENTIFIER)
            self.expect(TK.ASSIGN)
            return NamedArgument(
                Identifier(nameToken.value).setSpan(
                    nameToken.index,
                    nameToken.end
                ),
                self.parseExpression()
            )

        return self.parseExpression()

    def parseCallArgumentList(
        self,
        closingKind: TokenKind
    ) -> list[Node]:
        arguments = []

        if not self.tokenStream.current_is(closingKind):
            arguments.append(self.parseCallArgument())

            while self.match(TK.COMMA):
                if self.tokenStream.current_is(closingKind):
                    break

                arguments.append(self.parseCallArgument())

        return arguments

    def typeLengthAhead(
        self,
        offset: int = 0
    ) -> int | None:
        """
        Return the number of tokens occupied by a complete
        type, including union members.
        """

        firstLength = self.atomicTypeLengthAhead(
            offset
        )

        if firstLength is None:
            return None

        totalLength = firstLength

        while True:
            pipe = self.tokenStream.peek(
                offset + totalLength
            )

            if (
                pipe is None
                or pipe.kind != TK.PIPE
            ):
                break

            nextLength = self.atomicTypeLengthAhead(
                offset + totalLength + 1
            )

            if nextLength is None:
                return None

            totalLength += 1 + nextLength

        return totalLength


    def atomicTypeLengthAhead(
        self,
        offset: int = 0
    ) -> int | None:
        """
        Return the number of tokens occupied by one
        non-union type component.
        """

        token = self.tokenStream.peek(offset)

        if token is None:
            return None

        # Primitive or named type.
        if token.kind in DATA_TYPES:
            return 1

        if token.kind == TK.IDENTIFIER:
            return 1

        # list(type) and set(type)
        if token.kind in (TK.LIST, TK.SET):
            opening = self.tokenStream.peek(
                offset + 1
            )

            if (
                opening is None
                or opening.kind != TK.OPEN_PAREN
            ):
                return None

            elementLength = self.typeLengthAhead(
                offset + 2
            )

            if elementLength is None:
                return None

            closing = self.tokenStream.peek(
                offset + 2 + elementLength
            )

            if (
                closing is None
                or closing.kind != TK.CLOSE_PAREN
            ):
                return None

            return elementLength + 3

        # dict(key_type, value_type)
        if token.kind == TK.DICT:
            opening = self.tokenStream.peek(offset + 1)
            if opening is None or opening.kind != TK.OPEN_PAREN:
                return None

            keyLength = self.typeLengthAhead(offset + 2)
            if keyLength is None:
                return None

            comma = self.tokenStream.peek(offset + 2 + keyLength)
            if comma is None or comma.kind != TK.COMMA:
                return None

            valueLength = self.typeLengthAhead(offset + 3 + keyLength)
            if valueLength is None:
                return None

            closing = self.tokenStream.peek(
                offset + 3 + keyLength + valueLength
            )
            if closing is None or closing.kind != TK.CLOSE_PAREN:
                return None

            return keyLength + valueLength + 4

        # arr(type, capacity) or a heterogeneous positional schema such as
        # arr(int, str * 2). The final capacity is optional for a schema.
        if token.kind == TK.ARR:
            opening = self.tokenStream.peek(
                offset + 1
            )

            if (
                opening is None
                or opening.kind != TK.OPEN_PAREN
            ):
                return None

            cursor = offset + 2

            while True:
                elementLength = self.typeLengthAhead(cursor)
                if elementLength is None:
                    return None
                cursor += elementLength

                repeat = self.tokenStream.peek(cursor)
                if repeat is not None and repeat.kind == TK.ASTERISK:
                    count = self.tokenStream.peek(cursor + 1)
                    if count is None or count.kind != TK.INTEGER:
                        return None
                    cursor += 2

                delimiter = self.tokenStream.peek(cursor)
                if delimiter is None:
                    return None
                if delimiter.kind == TK.CLOSE_PAREN:
                    return cursor - offset + 1
                if delimiter.kind != TK.COMMA:
                    return None

                possibleCapacity = self.tokenStream.peek(cursor + 1)
                possibleClosing = self.tokenStream.peek(cursor + 2)
                if (
                    possibleCapacity is not None
                    and possibleCapacity.kind == TK.INTEGER
                    and possibleClosing is not None
                    and possibleClosing.kind == TK.CLOSE_PAREN
                ):
                    return cursor - offset + 3

                cursor += 1

        return None

    def declarationKindAhead(
        self
    ) -> str | None:
        """
        Detect whether the upcoming tokens begin a variable or
        function declaration.

        Returns:
            "variable"
            "function"
            None
        """

        offset = 0

        # Declaration modifiers may appear in any order.
        while True:
            token = self.tokenStream.peek(offset)

            if (
                token is None
                or token.kind
                not in DECLARATION_MODIFIER_KINDS
            ):
                break

            offset += 1

        typeLength = self.typeLengthAhead(offset)

        if typeLength is None:
            return None

        nameToken = self.tokenStream.peek(
            offset + typeLength
        )

        afterName = self.tokenStream.peek(
            offset + typeLength + 1
        )

        if (
            nameToken is None
            or nameToken.kind != TK.IDENTIFIER
            or afterName is None
        ):
            return None

        if afterName.kind == TK.OPEN_PAREN:
            return "function"

        if afterName.kind in (
            TK.ASSIGN,
            TK.SEMICOLON,
            TK.CLOSE_CURLY,
            TK.EOF_KIND
        ):
            return "variable"

        # Without this recovery, `int count` followed by a new
        # statement is parsed as an expression and produces an
        # unrelated error. Treat the line break as evidence that this
        # was an uninitialized declaration with a missing semicolon.
        if self.tokensAreOnDifferentLines(nameToken, afterName):
            return "variable"

        return None

    def parseArrayElements(self) -> list[Node]:
        elements = []

        if self.tokenStream.current_is(TK.MORE_THAN):
            return elements

        while True:
            elements.append(
                self.parseArrayElement()
            )

            if not self.match(TK.COMMA):
                break

            if self.tokenStream.current_is(TK.MORE_THAN):
                break

        return elements

    def parseArrayElement(self) -> Node:
        return self.parseOr()

    @located
    def parseDeclarationModifiers(self) -> DeclarationModifiers:
        seen: set[TokenKind] = set()

        while modifier := self.match(
            *DECLARATION_MODIFIER_KINDS
        ):
            if modifier.kind in seen:
                raise SyntaxError(
                    f"Duplicate declaration modifier "
                    f"'{modifier.value}' at source index "
                    f"{modifier.index}."
                )

            seen.add(modifier.kind)

        return DeclarationModifiers(
            isNew=TK.NEW in seen,
            isGlobal=TK.GLOBAL in seen,
            isConst=TK.CONST in seen
        )
 #################################### parsing functions ####################################
    @located
    def parse_statement(self):
        current = self.current()

        if current.kind == TK.STRUCT:
            return self.parseStructDeclaration()

        if current.kind == TK.ENUM:
            return self.parseEnumDeclaration()

        if current.kind == TK.IMPORT:
            if (
                self.tokenStream.peek() is not None
                and self.tokenStream.peek().kind == TK.PYTHON
            ):
                return self.parsePythonImport()
            return self.parseImportStatement()

        if current.kind == TK.FROM:
            return self.parseFromImportStatement()

        if current.kind == TK.IF:
            return self.parseIfStatement()

        if current.kind == TK.WHILE:
            return self.parseWhileStatement()

        if current.kind == TK.UNTIL:
            return self.parseUntilStatement()

        if current.kind == TK.FOR:
            return self.parseForStatement()

        if current.kind == TK.FOREACH:
            return self.parseForeachStatement()

        if current.kind == TK.BREAK:
            return self.parseBreakStatement()

        if current.kind == TK.CONTINUE:
            return self.parseContinueStatement()

        if current.kind == TK.RETURN:
            return self.parseReturnStatement()

        declarationKind = self.declarationKindAhead()

        if declarationKind == "function":
            if current.kind in DECLARATION_MODIFIER_KINDS:
                raise SyntaxError(
                    "Variable declaration modifiers cannot "
                    "be applied to function declarations."
                )

            return self.parseFunctionDeclaration()

        if declarationKind == "variable":
            return self.parseVarDecl()

        expression = self.parseExpression()

        assignmentToken = self.match(
            *ASSIGNMENT_OPERATORS
        )

        if assignmentToken:
            if not isinstance(
                expression,
                (Identifier, MemberAccess, IndexAccess)
            ):
                raise SyntaxError(
                    f"Invalid assignment target: {expression}"
                )

            value = self.parseExpression()
            self.expectSemicolon("assignment")

            if assignmentToken.kind == TK.ASSIGN:
                return VarAssign(
                    expression,
                    value
                )

            return CompoundAssign(
                expression,
                mapCompoundAssignmentToOperator(
                    assignmentToken
                ),
                value
            )

        self.expectSemicolon("expression statement")

        return ExpressionStatement(expression)

    @located
    def parsePythonImport(self) -> VarDeclaration:
        """Parse native Python imports as typed ``pyimport`` declarations."""
        self.expect(
            TK.IMPORT,
            message="'import' keyword not found."
        )
        self.expect(
            TK.PYTHON,
            message="'python' keyword not found after 'import'."
        )
        moduleToken = self.expect(
            TK.STRING,
            message="Python module name must be a string literal."
        )
        self.expect(
            TK.AS,
            message="'as' keyword not found after Python module name."
        )
        aliasToken = self.expect(
            TK.IDENTIFIER,
            message="Import binding name not found after 'as'."
        )
        self.expectSemicolon("Python import")

        module = Literal(Type.STR, moduleToken.value).setSpan(
            moduleToken.index,
            moduleToken.end
        )
        importCall = FunctionCall(
            Identifier("pyimport").setSpan(
                moduleToken.index,
                moduleToken.index
            ),
            [module]
        ).setSpan(moduleToken.index, moduleToken.end)

        return VarDeclaration(
            PrimitiveType(Type.PYOBJECT),
            Identifier(aliasToken.value).setSpan(
                aliasToken.index,
                aliasToken.end
            ),
            importCall
        )

    def parseModuleName(self) -> Identifier:
        token = self.expect(
            TK.IDENTIFIER,
            message="Module name not found."
        )
        return Identifier(token.value).setSpan(token.index, token.end)

    @located
    def parseImportStatement(self) -> ImportStatement:
        self.expect(TK.IMPORT, message="'import' keyword not found.")
        module = self.parseModuleName()
        if self.current().kind == TK.DOT:
            raise TokenError(
                "Dotted module names are not supported. To import a member "
                "of a module, use 'from module import member;'."
            )
        alias = None
        if self.match(TK.AS):
            token = self.expect(
                TK.IDENTIFIER,
                message="Import binding name not found after 'as'."
            )
            alias = Identifier(token.value).setSpan(token.index, token.end)
        self.expectSemicolon("module import")
        return ImportStatement(module, alias)

    @located
    def parseFromImportStatement(self) -> FromImportStatement:
        self.expect(TK.FROM, message="'from' keyword not found.")
        module = self.parseModuleName()
        if self.current().kind == TK.DOT:
            raise TokenError(
                "Dotted module names are not supported; module names must "
                "be single identifiers."
            )
        self.expect(
            TK.IMPORT,
            message="'import' keyword not found after module path."
        )
        token = self.expect(
            TK.IDENTIFIER,
            message="Imported name not found after 'import'."
        )
        importedName = Identifier(token.value).setSpan(token.index, token.end)
        alias = None
        if self.match(TK.AS):
            token = self.expect(
                TK.IDENTIFIER,
                message="Import binding name not found after 'as'."
            )
            alias = Identifier(token.value).setSpan(token.index, token.end)
        self.expectSemicolon("from import")
        return FromImportStatement(module, importedName, alias)

    @located
    def parseStructDeclaration(self) -> StructDeclaration:
        self.expect(
            TK.STRUCT,
            message="'struct' keyword not found."
        )

        nameToken = self.expect(
            TK.IDENTIFIER,
            message="Struct name not found."
        )
        name = Identifier(nameToken.value).setSpan(
            nameToken.index,
            nameToken.end
        )

        self.expect(
            TK.OPEN_CURLY,
            message="Opening curly brace not found after struct name."
        )

        fields = []
        methods = []

        while not self.tokenStream.current_is(
            TK.CLOSE_CURLY,
            TK.EOF_KIND
        ):
            declarationKind = self.declarationKindAhead()

            if declarationKind == "function":
                if self.current().kind in DECLARATION_MODIFIER_KINDS:
                    raise SyntaxError(
                        "Variable declaration modifiers cannot "
                        "be applied to struct methods."
                    )

                methods.append(
                    self.parseFunctionDeclaration()
                )
                continue

            if declarationKind == "variable":
                fields.append(
                    self.parseStructFieldDeclaration()
                )
                continue

            raise SyntaxError(
                f"Invalid struct member declaration at source "
                f"index {self.current().index}."
            )

        self.expect(
            TK.CLOSE_CURLY,
            message="Closing curly brace not found after struct declaration."
        )

        # Struct declarations conventionally omit a trailing
        # semicolon, but accepting one is harmless and convenient.
        self.match(TK.SEMICOLON)

        return StructDeclaration(
            name,
            fields,
            methods=methods
        )

    @located
    def parseEnumDeclaration(self) -> EnumDeclaration:
        self.expect(
            TK.ENUM,
            message="'enum' keyword not found."
        )
        self.expect(
            TK.OPEN_PAREN,
            message="Opening parenthesis not found after 'enum'."
        )
        baseType = self.parseType()
        self.expect(
            TK.CLOSE_PAREN,
            message="Closing parenthesis not found after enum type."
        )

        nameToken = self.expect(
            TK.IDENTIFIER,
            message="Enum name not found."
        )
        name = Identifier(nameToken.value).setSpan(
            nameToken.index,
            nameToken.end
        )

        self.expect(
            TK.ASSIGN,
            message="Equal sign not found after enum name."
        )
        self.expect(
            TK.OPEN_PAREN,
            message="Opening parenthesis not found for enum members."
        )

        members = []

        while not self.tokenStream.current_is(
            TK.CLOSE_PAREN,
            TK.EOF_KIND
        ):
            members.append(self.parseEnumMemberDeclaration())

        self.expect(
            TK.CLOSE_PAREN,
            message="Closing parenthesis not found after enum declaration."
        )
        self.match(TK.SEMICOLON)

        return EnumDeclaration(
            baseType,
            name,
            members
        )

    @located
    def parseEnumMemberDeclaration(
        self
    ) -> EnumMemberDeclaration:
        nameToken = self.expect(
            TK.IDENTIFIER,
            message="Enum member name not found."
        )
        name = Identifier(nameToken.value).setSpan(
            nameToken.index,
            nameToken.end
        )
        value = (
            self.parseExpression()
            if self.match(TK.ASSIGN)
            else UNINITIALIZED
        )

        if not self.match(TK.SEMICOLON):
            if not self.tokenStream.current_is(TK.CLOSE_PAREN):
                self.expectSemicolon("enum member")

        return EnumMemberDeclaration(name, value)

    @located
    def parseStructFieldDeclaration(
        self
    ) -> StructFieldDeclaration:
        modifiers = self.parseDeclarationModifiers()
        fieldType = self.parseType()

        nameToken = self.expect(
            TK.IDENTIFIER,
            message="Struct field name not found."
        )
        name = Identifier(nameToken.value).setSpan(
            nameToken.index,
            nameToken.end
        )

        if self.match(TK.ASSIGN):
            defaultValue = self.parseExpression()
        else:
            defaultValue = UNINITIALIZED

        self.expectSemicolon("struct field declaration")

        return StructFieldDeclaration(
            fieldType,
            name,
            defaultValue=defaultValue,
            modifiers=modifiers
        )

    @located
    def parseVarDecl(self):
        modifiers = self.parseDeclarationModifiers()

        varDeclType = self.parseType()

        varDeclIdent = self.expect(
            TK.IDENTIFIER,
            message="Identifier not found."
        )

        if self.match(TK.ASSIGN):
            if (
                isinstance(varDeclType, DictType)
                and self.tokenStream.current_is(TK.OPEN_CURLY)
                and self.tokenStream.peek() is not None
                and self.tokenStream.peek().kind == TK.CLOSE_CURLY
            ):
                varDeclVal = self.parseDictLiteral()
            else:
                varDeclVal = self.parseExpression()
        else:
            varDeclVal = UNINITIALIZED

        self.expectSemicolon("variable declaration")

        return VarDeclaration(
            varDeclType,
            Identifier(varDeclIdent.value).setSpan(
                varDeclIdent.index,
                varDeclIdent.end
            ),
            varDeclVal,
            modifiers=modifiers
        )

    @located
    def parseExpression(self):
        return self.parseOr()

    @located
    def parseOr(self):
        expression = self.parseXor()

        while operator := self.match(TK.OR):
            right = self.parseXor()

            left = expression
            expression = self.cover(BinaryOp(
                left,
                mapTokenToOperator(operator),
                right
            ), left, right)

        return expression


    @located
    def parseXor(self):
        expression = self.parseAnd()

        while operator := self.match(TK.XOR):
            right = self.parseAnd()

            left = expression
            expression = self.cover(BinaryOp(
                left,
                mapTokenToOperator(operator),
                right
            ), left, right)

        return expression


    @located
    def parseAnd(self):
        expression = self.parseComparison()

        while operator := self.match(TK.AND):
            right = self.parseComparison()

            left = expression
            expression = self.cover(BinaryOp(
                left,
                mapTokenToOperator(operator),
                right
            ), left, right)

        return expression

    @located
    def parseComparison(self):
        expression = self.parseTerm()

        comparisonKinds = [
            TK.EQUALS,
            TK.NOT_EQUAL,
            TK.LESS_THAN,
            TK.MORE_EQUAL,
            TK.LESS_EQUAL
        ]

        if self.arrayLiteralDepth == 0:
            comparisonKinds.append(TK.MORE_THAN)

        while operator := self.match(*comparisonKinds):
            right = self.parseTerm()

            left = expression
            expression = self.cover(BinaryOp(
                left,
                mapTokenToOperator(operator),
                right
            ), left, right)

        return expression

    @located
    def parseTerm(self):
        expression = self.parseFactor()

        while operator := self.match(TK.PLUS, TK.MINUS):
            right = self.parseFactor()

            left = expression
            expression = self.cover(BinaryOp(
                left,
                mapTokenToOperator(operator, isMinus=True),
                right
            ), left, right)

        return expression


    @located
    def parseFactor(self):
        expression = self.parsePower()

        while operator := self.match(
            TK.ASTERISK,
            TK.SLASH,
            TK.MODULO,
            TK.DOUBLE_SLASH
        ):
            right = self.parsePower()

            left = expression
            expression = self.cover(BinaryOp(
                left,
                mapTokenToOperator(operator),
                right
            ), left, right)

        return expression


    @located
    def parsePower(self):
        expression = self.parseUnary()

        if operator := self.match(TK.EXPONENT):
            right = self.parsePower()

            left = expression
            expression = self.cover(BinaryOp(
                left,
                mapTokenToOperator(operator),
                right
            ), left, right)

        return expression

    @located
    def parseUnary(self):
        operator = self.match(TK.MINUS, TK.NOT)

        if operator:
            right = self.parseUnary()

            return self.cover(UnaryOp(
                mapTokenToOperator(operator),
                right
            ), right).setSpan(operator.index, right.span.end)

        return self.parsePostfix()

    @located
    def parsePostfix(self):
        expression = self.parsePrimary()

        while True:
            if self.match(TK.DOT):
                member = self.expect(
                    TK.IDENTIFIER,
                    TK.NEW,
                    *DATA_TYPES,
                    *COLLECTION_TYPES,
                    message="Member identifier not found after '.'."
                )

                target = expression
                memberNode = Identifier(member.value).setSpan(
                    member.index,
                    member.end
                )
                expression = MemberAccess(target, memberNode).setSpan(
                    target.span.start,
                    member.end
                )

            elif self.match(TK.OPEN_BRACK):
                # [:end] or [:]
                if self.match(TK.COLON):
                    start = None

                    if self.tokenStream.current_is(TK.CLOSE_BRACK):
                        end = None
                    else:
                        end = self.parseExpression()

                    self.expect(
                        TK.CLOSE_BRACK,
                        message="Closing bracket not found after slice."
                    )

                    target = expression
                    expression = SliceAccess(
                        target,
                        start,
                        end
                    ).setSpan(target.span.start, self.tokenStream.previous().end)

                else:
                    # Parse the expression before either ']' or ':'.
                    first = self.parseExpression()

                    # [start:end] or [start:]
                    if self.match(TK.COLON):
                        start = first

                        if self.tokenStream.current_is(TK.CLOSE_BRACK):
                            end = None
                        else:
                            end = self.parseExpression()

                        self.expect(
                            TK.CLOSE_BRACK,
                            message="Closing bracket not found after slice."
                        )

                        target = expression
                        expression = SliceAccess(
                            target,
                            start,
                            end
                        ).setSpan(target.span.start, self.tokenStream.previous().end)

                    # [index]
                    else:
                        self.expect(
                            TK.CLOSE_BRACK,
                            message="Closing bracket not found after index expression."
                        )

                        target = expression
                        expression = IndexAccess(
                            target,
                            first
                        ).setSpan(target.span.start, self.tokenStream.previous().end)

            elif self.match(TK.OPEN_PAREN):
                arguments = self.parseCallArgumentList(
                    TK.CLOSE_PAREN
                )

                self.expect(
                    TK.CLOSE_PAREN,
                    message="Closing parenthesis not found after arguments."
                )

                callee = expression
                expression = FunctionCall(
                    callee,
                    arguments
                ).setSpan(callee.span.start, self.tokenStream.previous().end)

            else:
                break

        return expression

    @located
    def parsePrimary(self):
        if self.tokenStream.current_is(TK.LIST, TK.ARR, TK.SET, TK.DICT):
            return self.parseCollectionConversion()

        if self.tokenStream.current_is(TK.OPEN_CURLY):
            return self.parseCurlyLiteral()

        if (
            self.tokenStream.current_is(TK.IDENTIFIER)
            and self.tokenStream.peek() is not None
            and self.tokenStream.peek().kind == TK.OPEN_CURLY
        ):
            typeToken = self.expect(TK.IDENTIFIER)
            typeName = Identifier(typeToken.value).setSpan(
                typeToken.index,
                typeToken.end
            )

            return self.parseStructLiteral(typeName)

        if self.match(TK.OPEN_BRACK):
            elements = self.parseExpressionList(
                TK.CLOSE_BRACK
            )

            self.expect(
                TK.CLOSE_BRACK,
                message="Closing bracket not found after list literal."
            )

            return ListLiteral(elements)

        if self.match(TK.LESS_THAN):
            self.arrayLiteralDepth += 1

            try:
                elements = self.parseArrayElements()

                self.expect(
                    TK.MORE_THAN,
                    message="Closing '>' not found after array literal."
                )
            finally:
                self.arrayLiteralDepth -= 1

            return ArrayLiteral(elements)

        if self.match(TK.OPEN_PAREN):
            savedArrayDepth = self.arrayLiteralDepth
            self.arrayLiteralDepth = 0

            try:
                # () is the empty set literal.
                if self.match(TK.CLOSE_PAREN):
                    return SetLiteral([])

                firstExpression = self.parseExpression()

                # No comma means ordinary grouping.
                if not self.match(TK.COMMA):
                    self.expect(
                        TK.CLOSE_PAREN,
                        message="Closing parenthesis not found after expression."
                    )

                    return firstExpression

                # A comma means this is a set literal.
                elements = [firstExpression]

                # Allows the single-element form: (value,)
                if not self.tokenStream.current_is(TK.CLOSE_PAREN):
                    elements.append(self.parseExpression())

                    while self.match(TK.COMMA):
                        if self.tokenStream.current_is(TK.CLOSE_PAREN):
                            break

                        elements.append(self.parseExpression())

                self.expect(
                    TK.CLOSE_PAREN,
                    message="Closing parenthesis not found after set literal."
                )

                return SetLiteral(elements)

            finally:
                self.arrayLiteralDepth = savedArrayDepth

        token = self.expect(
            TK.INTEGER,
            TK.DECIMAL,
            TK.STRING,
            TK.CHAR_LITERAL,
            TK.COMPOSITE_STR,
            TK.TRUE,
            TK.FALSE,
            TK.NIL,
            TK.IDENTIFIER,
            TK.SELF,
            TK.INT,
            TK.STR,
            TK.FLOAT,
            TK.BOOL,
            TK.CHAR,
            message=(
                "Literal, identifier or primitive "
                "conversion function not found."
            )
        )

        if token.kind in (TK.IDENTIFIER, TK.SELF):
            return Identifier(
                "self" if token.kind == TK.SELF else token.value
            )

        if token.kind in (
            TK.INT,
            TK.STR,
            TK.FLOAT,
            TK.BOOL,
            TK.CHAR
        ):
            # Primitive type keywords double as conversion
            # function names in evaluation position. Normalize
            # Runic aliases to their Latin builtin names.
            return Identifier(
                str(mapKindToType(token.kind))
            )

        if token.kind == TK.COMPOSITE_STR:
            return self.parseCompositeStringToken(token)

        return Literal(
            mapLiteralToType(token),
            token.value
        )

    @located
    def parseCollectionConversion(self) -> CollectionConversion | DictConversion:
        kindToken = self.expect(TK.LIST, TK.ARR, TK.SET, TK.DICT)
        collectionKind = {
            TK.LIST: "list",
            TK.ARR: "arr",
            TK.SET: "set",
            TK.DICT: "dict",
        }[kindToken.kind]

        self.expect(
            TK.OPEN_PAREN,
            message=f"Opening parenthesis not found after '{collectionKind}'."
        )
        firstType = self.parseType()
        if kindToken.kind == TK.DICT:
            self.expect(
                TK.COMMA,
                message="Comma not found after dictionary key type."
            )
            valueType = self.parseType()
            arguments = []
            if self.match(TK.COMMA):
                arguments = self.parseCallArgumentList(TK.CLOSE_PAREN)
            self.expect(
                TK.CLOSE_PAREN,
                message="Closing parenthesis not found after 'dict' conversion."
            )
            return DictConversion(firstType, valueType, arguments)

        elementType = firstType
        arguments = []
        if self.match(TK.COMMA):
            arguments = self.parseCallArgumentList(TK.CLOSE_PAREN)
        self.expect(
            TK.CLOSE_PAREN,
            message=f"Closing parenthesis not found after '{collectionKind}' conversion."
        )

        return CollectionConversion(
            collectionKind,
            elementType,
            arguments
        )

    def curlyLiteralKind(self) -> str:
        """Distinguish anonymous struct fields from dictionary entries."""
        if (
            self.tokenStream.peek() is not None
            and self.tokenStream.peek().kind == TK.CLOSE_CURLY
        ):
            # Preserve contextually typed empty struct literals. Empty
            # dictionaries use the unambiguous dict(K, V) constructor.
            return "struct"

        depth = 0
        offset = 1
        openingKinds = (TK.OPEN_PAREN, TK.OPEN_BRACK, TK.OPEN_CURLY)
        closingKinds = (TK.CLOSE_PAREN, TK.CLOSE_BRACK, TK.CLOSE_CURLY)
        while token := self.tokenStream.peek(offset):
            if token.kind in openingKinds:
                depth += 1
            elif token.kind in closingKinds:
                if token.kind == TK.CLOSE_CURLY and depth == 0:
                    break
                depth -= 1
            elif depth == 0:
                if token.kind == TK.ARROW:
                    return "dict"
                if token.kind == TK.ASSIGN:
                    return "struct"
            offset += 1
        return "struct"

    @located
    def parseCurlyLiteral(self) -> StructLiteral | DictLiteral:
        if self.curlyLiteralKind() == "dict":
            return self.parseDictLiteral()
        return self.parseStructLiteral()

    @located
    def parseDictLiteral(self) -> DictLiteral:
        self.expect(
            TK.OPEN_CURLY,
            message="Opening curly brace not found for dictionary literal."
        )
        entries: list[DictEntry] = []
        while not self.tokenStream.current_is(TK.CLOSE_CURLY, TK.EOF_KIND):
            key = self.parseExpression()
            self.expect(
                TK.ARROW,
                message="'->' not found between dictionary key and value."
            )
            value = self.parseExpression()
            entries.append(DictEntry(key, value).setSpan(
                key.span.start,
                value.span.end
            ))

            if self.match(TK.SEMICOLON):
                continue
            if not self.tokenStream.current_is(TK.CLOSE_CURLY):
                self.expectSemicolon("dictionary entry")

        self.expect(
            TK.CLOSE_CURLY,
            message="Closing curly brace not found after dictionary literal."
        )
        return DictLiteral(entries)

    @located
    def parseStructLiteral(
        self,
        typeName: Identifier | None = None
    ) -> StructLiteral:
        self.expect(
            TK.OPEN_CURLY,
            message="Opening curly brace not found for struct literal."
        )

        fields = []

        while not self.tokenStream.current_is(
            TK.CLOSE_CURLY,
            TK.EOF_KIND
        ):
            fields.append(
                self.parseStructFieldInitializer()
            )

        self.expect(
            TK.CLOSE_CURLY,
            message="Closing curly brace not found after struct literal."
        )

        return StructLiteral(fields, typeName=typeName)

    @located
    def parseStructFieldInitializer(
        self
    ) -> StructFieldInitializer:
        nameToken = self.expect(
            TK.IDENTIFIER,
            message="Struct field name not found in literal."
        )
        name = Identifier(nameToken.value).setSpan(
            nameToken.index,
            nameToken.end
        )

        self.expect(
            TK.ASSIGN,
            message="Equal sign not found after struct field name."
        )
        value = self.parseExpression()

        if not self.match(TK.SEMICOLON):
            if not self.tokenStream.current_is(TK.CLOSE_CURLY):
                self.expectSemicolon("struct field initializer")

        return StructFieldInitializer(name, value)

    @located
    def parseBlock(self) -> Block:
        self.expect(
            TK.OPEN_CURLY,
            message="Opening curly brace not found before block."
        )

        block = Block()

        while not self.tokenStream.current_is(
            TK.CLOSE_CURLY,
            TK.EOF_KIND
        ):
            block.addNode(self.parse_statement())

        self.expect(
            TK.CLOSE_CURLY,
            message="Closing curly brace not found after block."
        )

        return block

    @located
    def parseIfStatement(self) -> IfStatement:
        self.expect(
            TK.IF,
            message="'if' keyword not found."
        )

        self.expect(
            TK.OPEN_PAREN,
            message="Opening parenthesis not found after 'if'."
        )

        condition = self.parseExpression()

        self.expect(
            TK.CLOSE_PAREN,
            message="Closing parenthesis not found after if condition."
        )

        thenBranch = self.parseBlock()
        elsifBranches = []
        elseBranch = None

        while elsifToken := self.match(TK.ELSIF):
            self.expect(
                TK.OPEN_PAREN,
                message="Opening parenthesis not found after 'elsif'."
            )

            elsifCondition = self.parseExpression()

            self.expect(
                TK.CLOSE_PAREN,
                message="Closing parenthesis not found after elsif condition."
            )

            elsifBody = self.parseBlock()

            elsifBranches.append(
                ElseIfBranch(
                    elsifCondition,
                    elsifBody
                ).setSpan(elsifToken.index, elsifBody.span.end)
            )

        if self.match(TK.ELSE):
            elseBranch = self.parseBlock()

        return IfStatement(
            condition,
            thenBranch,
            elsifBranches,
            elseBranch
        )

    @located
    def parseWhileStatement(self) -> WhileStatement:
        self.expect(
            TK.WHILE,
            message="'while' keyword not found."
        )

        self.expect(
            TK.OPEN_PAREN,
            message="Opening parenthesis not found after 'while'."
        )

        condition = self.parseExpression()

        self.expect(
            TK.CLOSE_PAREN,
            message="Closing parenthesis not found after while condition."
        )

        body = self.parseBlock()

        return WhileStatement(
            condition,
            body
        )

    @located
    def parseUntilStatement(self) -> UntilStatement:
        self.expect(
            TK.UNTIL,
            message="'until' keyword not found."
        )

        self.expect(
            TK.OPEN_PAREN,
            message="Opening parenthesis not found after 'until'."
        )

        condition = self.parseExpression()

        self.expect(
            TK.CLOSE_PAREN,
            message="Closing parenthesis not found after until condition."
        )

        body = self.parseBlock()

        return UntilStatement(
            condition,
            body
        )

    @located
    def parseParameter(self) -> Parameter:
        if self.tokenStream.current_is(TK.SELF):
            token = self.current()
            spelling = token.value
            typedForm = (
                "StructType ᛋᛖᛚᚠ"
                if spelling == "ᛋᛖᛚᚠ"
                else "StructType self"
            )
            example = (
                "Product ᛋᛖᛚᚠ"
                if spelling == "ᛋᛖᛚᚠ"
                else "Product self"
            )
            raise TokenError(
                f"Parameter '{spelling}' is missing its type. "
                f"Instance methods must declare it as "
                f"'{typedForm}', for example '{example}'."
            )

        paramType = self.parseType()

        nameToken = self.expect(
            TK.IDENTIFIER,
            TK.SELF,
            message="Parameter name not found."
        )

        name = (
            "self"
            if nameToken.kind == TK.SELF
            else nameToken.value
        )

        defaultValue = (
            self.parseExpression()
            if self.match(TK.ASSIGN)
            else UNINITIALIZED
        )

        return Parameter(
            paramType,
            Identifier(name).setSpan(
                nameToken.index,
                nameToken.end
            ),
            defaultValue=defaultValue
        )

    @located
    def parseFunctionDeclaration(self) -> FunctionDeclaration:
        returnType = self.parseType()

        nameToken = self.expect(
            TK.IDENTIFIER,
            message="Function name not found."
        )

        self.expect(
            TK.OPEN_PAREN,
            message="Opening parenthesis not found after function name."
        )

        parameters = []

        if not self.tokenStream.current_is(TK.CLOSE_PAREN):
            parameters.append(self.parseParameter())

            while self.match(TK.COMMA):
                parameters.append(self.parseParameter())

        self.expect(
            TK.CLOSE_PAREN,
            message="Closing parenthesis not found after function parameters."
        )

        body = self.parseBlock()

        return FunctionDeclaration(
            returnType,
            Identifier(nameToken.value).setSpan(
                nameToken.index,
                nameToken.end
            ),
            parameters,
            body
        )

    @located
    def parseReturnStatement(self) -> ReturnStatement:
        self.expect(
            TK.RETURN,
            message="'return' keyword not found."
        )

        if self.tokenStream.current_is(TK.SEMICOLON):
            self.expectSemicolon("return statement")
            return ReturnStatement()

        if self.tokenStream.current_is(TK.CLOSE_CURLY, TK.EOF_KIND):
            self.expectSemicolon("return statement")

        value = self.parseExpression()
        self.expectSemicolon("return statement")

        return ReturnStatement(value)

    @located
    def parseBreakStatement(self) -> BreakStatement:
        self.expect(
            TK.BREAK,
            message="'break' keyword not found."
        )
        self.expectSemicolon("break statement")
        return BreakStatement()

    @located
    def parseContinueStatement(self) -> ContinueStatement:
        self.expect(
            TK.CONTINUE,
            message="'continue' keyword not found."
        )
        self.expectSemicolon("continue statement")
        return ContinueStatement()

    @located
    def parseForStatement(self) -> ForStatement:
        self.expect(
            TK.FOR,
            message="'for' keyword not found."
        )

        self.expect(
            TK.OPEN_PAREN,
            message="Opening parenthesis not found after 'for'."
        )

        iteratorToken = self.expect(
            TK.IDENTIFIER,
            message="Iterator identifier not found in for loop."
        )

        self.expect(
            TK.FROM,
            message="'from' keyword not found after for-loop iterator."
        )

        start = self.parseExpression()

        self.expect(
            TK.TO,
            message="'to' keyword not found after for-loop start expression."
        )

        end = self.parseExpression()

        self.expect(
            TK.CLOSE_PAREN,
            message="Closing parenthesis not found after for-loop range."
        )

        body = self.parseBlock()

        return ForStatement(
            Identifier(iteratorToken.value).setSpan(
                iteratorToken.index,
                iteratorToken.end
            ),
            start,
            end,
            body
        )

    @located
    def parseForeachStatement(self) -> ForeachStatement:
        self.expect(
            TK.FOREACH,
            message="'foreach' keyword not found."
        )

        self.expect(
            TK.OPEN_PAREN,
            message="Opening parenthesis not found after 'foreach'."
        )

        iteratorToken = self.expect(
            TK.IDENTIFIER,
            message="Iterator identifier not found in foreach loop."
        )

        self.expect(
            TK.IN,
            message="'in' keyword not found after foreach iterator."
        )

        collection = self.parseExpression()

        self.expect(
            TK.CLOSE_PAREN,
            message="Closing parenthesis not found after foreach collection."
        )

        body = self.parseBlock()

        return ForeachStatement(
            Identifier(iteratorToken.value).setSpan(
                iteratorToken.index,
                iteratorToken.end
            ),
            collection,
            body
        )

    @located
    def parseType(self) -> TypeNode:
        return self.parseUnionType()


    @located
    def parseUnionType(self) -> TypeNode:
        members = [
            self.parseAtomicType()
        ]

        while self.match(TK.PIPE):
            members.append(
                self.parseAtomicType()
            )

        if len(members) == 1:
            return members[0]

        return UnionType(members)


    @located
    def parseAtomicType(self) -> TypeNode:
        if self.match(TK.LIST):
            self.expect(
                TK.OPEN_PAREN,
                message=(
                    "Opening parenthesis not found "
                    "after 'list'."
                )
            )

            elementType = self.parseType()

            self.expect(
                TK.CLOSE_PAREN,
                message=(
                    "Closing parenthesis not found "
                    "after list element type."
                )
            )

            return ListType(elementType)

        if self.match(TK.ARR):
            self.expect(
                TK.OPEN_PAREN,
                message=(
                    "Opening parenthesis not found "
                    "after 'arr'."
                )
            )

            specifications: list[tuple[TypeNode, int]] = []
            usedRepeat = False
            explicitCapacity = None

            while True:
                elementType = self.parseType()
                count = 1

                if self.match(TK.ASTERISK):
                    usedRepeat = True
                    countToken = self.expect(
                        TK.INTEGER,
                        message=(
                            "Positive integer count not found after '*' "
                            "in heterogeneous array schema."
                        )
                    )
                    count = int(countToken.value)
                    if count < 1:
                        raise TokenError(
                            "Heterogeneous array type counts must be "
                            "positive integers."
                        )

                specifications.append((elementType, count))

                if self.tokenStream.current_is(TK.CLOSE_PAREN):
                    break

                self.expect(
                    TK.COMMA,
                    message="Comma not found after array type entry."
                )

                if (
                    self.tokenStream.current_is(TK.INTEGER)
                    and self.tokenStream.peek() is not None
                    and self.tokenStream.peek().kind == TK.CLOSE_PAREN
                ):
                    capacityToken = self.expect(TK.INTEGER)
                    explicitCapacity = int(capacityToken.value)
                    break

            self.expect(
                TK.CLOSE_PAREN,
                message=(
                    "Closing parenthesis not found "
                    "after array type."
                )
            )

            if (
                len(specifications) == 1
                and not usedRepeat
                and explicitCapacity is not None
            ):
                return ArrayType(
                    specifications[0][0],
                    explicitCapacity
                )

            if len(specifications) == 1 and not usedRepeat:
                raise TokenError(
                    "Homogeneous array types require a capacity, such as "
                    "'arr(int, 3)'."
                )

            slotTypes = [
                entryType
                for entryType, count in specifications
                for _ in range(count)
            ]
            inferredCapacity = len(slotTypes)

            if (
                explicitCapacity is not None
                and explicitCapacity != inferredCapacity
            ):
                raise TokenError(
                    f"Heterogeneous array schema defines "
                    f"{inferredCapacity} slot(s), but its explicit "
                    f"capacity is {explicitCapacity}."
                )

            return ArrayType(
                slotTypes[0],
                inferredCapacity,
                slotTypes=slotTypes
            )

        if self.match(TK.SET):
            self.expect(
                TK.OPEN_PAREN,
                message=(
                    "Opening parenthesis not found "
                    "after 'set'."
                )
            )

            elementType = self.parseType()

            self.expect(
                TK.CLOSE_PAREN,
                message=(
                    "Closing parenthesis not found "
                    "after set element type."
                )
            )

            return SetType(elementType)

        if self.match(TK.DICT):
            self.expect(
                TK.OPEN_PAREN,
                message="Opening parenthesis not found after 'dict'."
            )
            keyType = self.parseType()
            self.expect(
                TK.COMMA,
                message="Comma not found after dictionary key type."
            )
            valueType = self.parseType()
            self.expect(
                TK.CLOSE_PAREN,
                message="Closing parenthesis not found after dictionary type."
            )
            return DictType(keyType, valueType)

        if nameToken := self.match(TK.IDENTIFIER):
            name = Identifier(
                nameToken.value
            ).setSpan(
                nameToken.index,
                nameToken.end
            )

            return NamedType(name)

        return self.parsePrimitiveType()

    @located
    def parsePrimitiveType(self) -> PrimitiveType:
        token = self.expect(
            *DATA_TYPES,
            message="Primitive type not found."
        )

        return PrimitiveType(
            mapKindToType(token.kind)
        )

# END PARSER CLASS

def main():
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

    from semantic import SemanticAnalyzer

    analyzer = SemanticAnalyzer()
    issues = analyzer.analyze(program)

    print("\nSemantic analysis:")

    if not issues:
        print("No issues found.")
    else:
        for issue in issues:
            print(f"- {issue}")


if __name__ == "__main__":
    main()
