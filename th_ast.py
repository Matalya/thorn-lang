from dataclasses import dataclass
from enum import Enum, auto
from Token import *
from Token import TokenKind as TK

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

class Op(Enum):
    POWER = auto()
    MULT = auto()
    DIV = auto()
    MOD = auto()
    FLOOR_DIV = auto()
    ADD = auto()
    SUB = auto()
    EQUALS = auto()
    NOT_EQUAL = auto()
    LESS_THAN = auto()
    MORE_THAN = auto()
    LESS_EQUAL = auto()
    MORE_EQUAL = auto()
    NOT = auto()
    AND = auto()
    OR = auto()
    XOR = auto()
    NEG = auto()

PRECEDENCE: list[list[Op]] = [
    [Op.POWER],
    [Op.NOT, Op.NEG],
    [Op.MULT, Op.DIV, Op.MOD, Op.FLOOR_DIV],
    [Op.ADD, Op.SUB],
    [Op.EQUALS, Op.NOT_EQUAL, Op.LESS_THAN, Op.MORE_THAN, Op.LESS_EQUAL, Op.MORE_EQUAL],
    [Op.AND],
    [Op.OR, Op.XOR]
]

def is_unary(operator: Op) -> bool:
    return operator in [Op.NOT, Op.NEG]

def associativity(operator: Op) -> str:
    if not isinstance(operator, Op): 
        raise TypeError(f"precedence(): Expected operator type, got {type(operator)}")
    return "right" if operator in [Op.POWER, Op.NEG, Op.NOT] else "left"

def arity(operator: Op):
    if not isinstance(operator, Op): 
        raise TypeError(f"precedence(): Expected operator type, got {type(operator)}")
    return "unary" if operator in [Op.NEG, Op.NOT] else "binary"

def precedence(operator: Op) -> int:
    global PRECEDENCE
    if not isinstance(operator, Op):
        raise TypeError(f"precedence(): Expected operator type, got {type(operator)}")
    for i in range(len(PRECEDENCE)):
        if operator in PRECEDENCE[i]:
            return i
    raise ValueError("precedence(): Operator not identified")

@dataclass(frozen=True)
class SourceSpan:
    """A half-open source range: ``start`` is inclusive, ``end`` exclusive."""

    start: int
    end: int

    def __post_init__(self):
        if self.start < 0:
            raise ValueError("SourceSpan start cannot be negative")
        if self.end < self.start:
            raise ValueError("SourceSpan end cannot precede its start")


class Node:
    # Most existing node constructors do not call super().__init__. Keeping the
    # default here lets spans be introduced without a disruptive AST rewrite.
    span: SourceSpan | None = None

    def setSpan(self, start: int, end: int):
        self.span = SourceSpan(start, end)
        return self

    def pretty(self, indent: int = 0) -> str:
        return " " * indent + repr(self)

    def child(
        self,
        label: str,
        value,
        indent: int
    ) -> str:
        prefix = " " * indent

        if isinstance(value, Node):
            return (
                f"{prefix}{label}:\n"
                f"{value.pretty(indent + 2)}"
            )

        if isinstance(value, list):
            if not value:
                return f"{prefix}{label}: []"

            children = "\n".join(
                item.pretty(indent + 2)
                if isinstance(item, Node)
                else " " * (indent + 2) + repr(item)
                for item in value
            )

            return f"{prefix}{label}:\n{children}"

        return f"{prefix}{label}: {value}"

# parent node
class Program(Node):
    def __init__(self, statements: list[Node] | None = None):
        self.statements = [] if statements is None else statements

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        if not self.statements:
            return f"{prefix}Program: empty"

        statements = "\n".join(
            statement.pretty(indent + 2)
            for statement in self.statements
        )

        return f"{prefix}Program:\n{statements}"

    def __repr__(self):
        return self.pretty()
    
    def addNode(self, node: Node):
        self.statements.append(node)

########################################## NODES ##########################################
class Uninitialized(Node):
    def __init__(self, type: Type = Type.UNINITIALIZED):
        self.type: Type = type
    
    def __repr__(self):
        return "<uninitialized>"
    
    def __str__(self):
        return "<uninitialized>"
UNINITIALIZED = Uninitialized()

class Identifier(Node):
    def __init__(self, name: str):
        self.name = name

    def pretty(self, indent: int = 0) -> str:
        return " " * indent + f"Identifier: {self.name}"

    def __repr__(self):
        return f"Identifier({self.name})"

class TypeNode(Node):
    pass


class NamedTypeDeclaration(Node):
    """
    Base node for declarations that introduce a named type.

    StructDeclaration and EnumDeclaration will inherit from this
    class. Keeping the common name here lets semantic analysis
    predeclare every type before inspecting declaration bodies, which
    permits self-referential and mutually recursive named types.
    """

    def __init__(
        self,
        name: Identifier,
        kind: str = "type"
    ):
        self.name: Identifier = name
        self.kind: str = kind

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}NamedTypeDeclaration: {self.kind}",
            self.child(
                "name",
                self.name,
                indent + 2
            )
        ])

    def __repr__(self):
        return (
            f"NamedTypeDeclaration("
            f"{self.name!r}, "
            f"kind={self.kind!r}"
            f")"
        )


class EnumMemberDeclaration(Node):
    def __init__(
        self,
        name: Identifier,
        value: Node = UNINITIALIZED
    ):
        self.name: Identifier = name
        self.value: Node = value
        self.hasResolvedValue: bool = False
        self.resolvedValue: object | None = None
        self.resolvedType: TypeNode | None = None

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}EnumMemberDeclaration",
            self.child("name", self.name, indent + 2),
            self.child("value", self.value, indent + 2)
        ])

    def __repr__(self):
        return (
            f"EnumMemberDeclaration("
            f"{self.name!r}, "
            f"value={self.value!r}"
            f")"
        )


class EnumDeclaration(NamedTypeDeclaration):
    def __init__(
        self,
        baseType: TypeNode,
        name: Identifier,
        members: list[EnumMemberDeclaration]
    ):
        super().__init__(name, kind="enum")
        self.baseType: TypeNode = baseType
        self.members: list[EnumMemberDeclaration] = members

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}EnumDeclaration",
            self.child("baseType", self.baseType, indent + 2),
            self.child("name", self.name, indent + 2),
            self.child("members", self.members, indent + 2)
        ])

    def __repr__(self):
        return (
            f"EnumDeclaration("
            f"{self.baseType!r}, "
            f"{self.name!r}, "
            f"members={self.members!r}"
            f")"
        )


class StructFieldDeclaration(Node):
    def __init__(
        self,
        fieldType: "TypeNode",
        name: Identifier,
        defaultValue: Node = UNINITIALIZED,
        modifiers: "DeclarationModifiers | None" = None
    ):
        self.fieldType: TypeNode = fieldType
        self.name: Identifier = name
        self.defaultValue: Node = defaultValue
        self.modifiers: DeclarationModifiers = (
            DeclarationModifiers()
            if modifiers is None
            else modifiers
        )

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}StructFieldDeclaration",
            self.child("modifiers", self.modifiers, indent + 2),
            self.child("type", self.fieldType, indent + 2),
            self.child("name", self.name, indent + 2),
            self.child("default", self.defaultValue, indent + 2)
        ])

    def __repr__(self):
        return (
            f"StructFieldDeclaration("
            f"{self.fieldType!r}, "
            f"{self.name!r}, "
            f"defaultValue={self.defaultValue!r}, "
            f"modifiers={self.modifiers!r}"
            f")"
        )


class StructDeclaration(NamedTypeDeclaration):
    def __init__(
        self,
        name: Identifier,
        fields: list[StructFieldDeclaration],
        methods: list["FunctionDeclaration"] | None = None
    ):
        super().__init__(name, kind="struct")
        self.fields: list[StructFieldDeclaration] = fields
        self.methods: list[FunctionDeclaration] = (
            [] if methods is None else methods
        )

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}StructDeclaration",
            self.child("name", self.name, indent + 2),
            self.child("fields", self.fields, indent + 2),
            self.child("methods", self.methods, indent + 2)
        ])

    def __repr__(self):
        return (
            f"StructDeclaration("
            f"{self.name!r}, "
            f"fields={self.fields!r}, "
            f"methods={self.methods!r}"
            f")"
        )


class StructFieldInitializer(Node):
    def __init__(self, name: Identifier, value: Node):
        self.name: Identifier = name
        self.value: Node = value

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}StructFieldInitializer",
            self.child("name", self.name, indent + 2),
            self.child("value", self.value, indent + 2)
        ])

    def __repr__(self):
        return (
            f"StructFieldInitializer("
            f"{self.name!r}, "
            f"{self.value!r}"
            f")"
        )


class StructLiteral(Node):
    def __init__(
        self,
        fields: list[StructFieldInitializer],
        typeName: Identifier | None = None
    ):
        self.typeName: Identifier | None = typeName
        self.fields: list[StructFieldInitializer] = fields

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent
        typeName = (
            self.typeName.name
            if self.typeName is not None
            else "contextual"
        )

        return "\n".join([
            f"{prefix}StructLiteral: {typeName}",
            self.child("fields", self.fields, indent + 2)
        ])

    def __repr__(self):
        return (
            f"StructLiteral("
            f"fields={self.fields!r}, "
            f"typeName={self.typeName!r}"
            f")"
        )

class PrimitiveType(TypeNode):
    def __init__(self, value: Type):
        self.value: Type = value

    def pretty(self, indent: int = 0) -> str:
        return " " * indent + f"PrimitiveType: {self.value}"

    def __repr__(self):
        return f"PrimitiveType({self.value})"

class NamedType(TypeNode):
    def __init__(self, name: Identifier):
        self.name: Identifier = name

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}NamedType",
            self.child(
                "name",
                self.name,
                indent + 2
            )
        ])

    def __repr__(self):
        return f"NamedType({self.name!r})"

class ListType(TypeNode):
    def __init__(self, elementType: TypeNode):
        self.elementType: TypeNode = elementType

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}ListType",
            self.child("elementType", self.elementType, indent + 2)
        ])

    def __repr__(self):
        return f"ListType({self.elementType})"

class ArrayType(TypeNode):
    def __init__(
        self,
        elementType: TypeNode,
        capacity: int
    ):
        self.elementType: TypeNode = elementType
        self.capacity: int = capacity

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}ArrayType",
            self.child(
                "elementType",
                self.elementType,
                indent + 2
            ),
            f"{' ' * (indent + 2)}capacity: {self.capacity}"
        ])

    def __repr__(self):
        return (
            f"ArrayType("
            f"{self.elementType}, "
            f"capacity={self.capacity}"
            f")"
        )

class SetType(TypeNode):
    def __init__(self, elementType: TypeNode):
        self.elementType: TypeNode = elementType

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}SetType",
            self.child(
                "elementType",
                self.elementType,
                indent + 2
            )
        ])

    def __repr__(self):
        return f"SetType({self.elementType})"

class UnionType(TypeNode):
    def __init__(self, members: list[TypeNode]):
        self.members: list[TypeNode] = members

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}UnionType",
            self.child(
                "members",
                self.members,
                indent + 2
            )
        ])

    def __repr__(self):
        return f"UnionType({self.members!r})"

class DeclarationModifiers(Node):
    def __init__(
        self,
        isNew: bool = False,
        isGlobal: bool = False,
        isConst: bool = False
    ):
        self.isNew: bool = isNew
        self.isGlobal: bool = isGlobal
        self.isConst: bool = isConst

    def names(self) -> list[str]:
        """Return modifiers in Thorn's canonical order."""
        names = []

        if self.isNew:
            names.append("new")

        if self.isGlobal:
            names.append("global")

        if self.isConst:
            names.append("const")

        return names

    def pretty(self, indent: int = 0) -> str:
        names = self.names()
        value = " ".join(names) if names else "none"

        return " " * indent + value

    def __repr__(self):
        return (
            f"DeclarationModifiers("
            f"isNew={self.isNew}, "
            f"isGlobal={self.isGlobal}, "
            f"isConst={self.isConst}"
            f")"
        )

class VarDeclaration(Node):
    def __init__(
        self,
        varType: TypeNode,
        varName: Identifier,
        varValue: Node = UNINITIALIZED,
        modifiers: DeclarationModifiers | None = None
    ):
        self.varType: TypeNode = varType
        self.varName: Identifier = varName
        self.varValue: Node = varValue
        self.modifiers: DeclarationModifiers = (
            DeclarationModifiers()
            if modifiers is None
            else modifiers
        )

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}VarDeclaration",
            self.child(
                "modifiers",
                self.modifiers,
                indent + 2
            ),
            self.child(
                "type",
                self.varType,
                indent + 2
            ),
            self.child(
                "name",
                self.varName,
                indent + 2
            ),
            self.child(
                "value",
                self.varValue,
                indent + 2
            )
        ])

    def __repr__(self):
        return (
            f"VarDeclaration("
            f"{self.varType}, "
            f"{self.varName!r}, "
            f"{self.varValue}, "
            f"modifiers={self.modifiers!r}"
            f")"
        )

class Literal(Node):
    def __init__(self, litType: Type, litValue: str):
        self.litType: Type = litType
        self.litValue: str = litValue

    def pretty(self, indent: int = 0) -> str:
        return (
            " " * indent
            + f"Literal ({self.litType}): {self.litValue}"
        )
    
    def strfy(self):
        return "\"" if self.litType == Type.STR else ""
    def __repr__(self):
        return f"Literal({self.litType}:{self.strfy()}{self.litValue}{self.strfy()})"

class CompositeStringType(Enum):
    STRING_COMPONENT = auto()
    EVALUATION_COMPONENT = auto()


class stringComponent(Node):
    def __init__(
        self,
        type: CompositeStringType,
        value: str | Node
    ):
        self.type: CompositeStringType = type

        self.value: Literal | Node = (
            Literal(Type.STR, value)
            if (
                self.type
                == CompositeStringType.STRING_COMPONENT
                and isinstance(value, str)
            )
            else value
        )

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent
        label = (
            "StringComponent"
            if self.type
            == CompositeStringType.STRING_COMPONENT
            else "EvaluationComponent"
        )

        return "\n".join([
            f"{prefix}{label}",
            self.child(
                "value",
                self.value,
                indent + 2
            )
        ])

    def __repr__(self):
        prefix = (
            "EvalComp"
            if self.type
            == CompositeStringType.EVALUATION_COMPONENT
            else ""
        )

        return f"{prefix}{self.value}"


class CompositeString(Node):
    def __init__(
        self,
        components: list[stringComponent]
    ):
        self.components: list[stringComponent] = components

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}CompositeString",
            self.child(
                "components",
                self.components,
                indent + 2
            )
        ])

    def __repr__(self):
        return f"CompositeString({self.components!r})"

class BinaryOp(Node):
    def __init__(self, left: str|int, op: Op, right: str|int):
        self.left: str|int = left
        self.op: Op = op
        self.right: str|int = right

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}BinaryOp: {self.op.name}",
            self.child("left", self.left, indent + 2),
            self.child("right", self.right, indent + 2)
        ])
    
    def __repr__(self):
        return f"binOp({self.left}, {self.op}, {self.right})"

class UnaryOp(Node):
    def __init__(self, op: Op, right: Node):
        self.op: Op = op
        self.right: Node = right

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}UnaryOp: {self.op.name}",
            self.child("operand", self.right, indent + 2)
        ])

    def __repr__(self):
        return f"NEG(-{self.right})" if self.op == Op.NEG else f"NOT({self.right})"

class MemberAccess(Node):
    def __init__(self, target: Node, member: Identifier):
        self.target: Node = target
        self.member: Identifier = member

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}MemberAccess",
            self.child("target", self.target, indent + 2),
            self.child("member", self.member, indent + 2)
        ])

    def __repr__(self):
        return f"MemberAccess({self.target}, {self.member})"

class IndexAccess(Node):
    def __init__(self, target: Node, index: Node):
        self.target: Node = target
        self.index: Node = index

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}IndexAccess",
            self.child("target", self.target, indent + 2),
            self.child("index", self.index, indent + 2)
        ])

    def __repr__(self):
        return f"IndexAccess({self.target}, {self.index})"

class VarAssign(Node):
    def __init__(self, target: Node, value: Node):
        self.target: Node = target
        self.value: Node = value

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}Assignment",
            self.child("target", self.target, indent + 2),
            self.child("value", self.value, indent + 2)
        ])

    def __repr__(self):
        return f"Assignment({self.target}, {self.value})"

class CompoundAssign(Node):
    def __init__(
        self,
        target: Node,
        op: Op,
        value: Node
    ):
        self.target: Node = target
        self.op: Op = op
        self.value: Node = value

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}CompoundAssignment: {self.op.name}",
            self.child("target", self.target, indent + 2),
            self.child("value", self.value, indent + 2)
        ])

    def __repr__(self):
        return (
            f"CompoundAssign("
            f"{self.target}, "
            f"{self.op}, "
            f"{self.value}"
            f")"
        )

class FunctionCall(Node):
    def __init__(self, callee: Node, arguments: list[Node]):
        self.callee: Node = callee
        self.arguments: list[Node] = arguments

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        lines = [
            f"{prefix}FunctionCall",
            self.child("callee", self.callee, indent + 2),
            self.child("arguments", self.arguments, indent + 2)
        ]

        return "\n".join(lines)

    def __repr__(self):
        arguments = ", ".join(repr(arg) for arg in self.arguments)
        return f"FunctionCall({self.callee}, [{arguments}])"

class NamedArgument(Node):
    def __init__(self, name: Identifier, value: Node):
        self.name: Identifier = name
        self.value: Node = value

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}NamedArgument",
            self.child("name", self.name, indent + 2),
            self.child("value", self.value, indent + 2)
        ])

    def __repr__(self):
        return f"NamedArgument({self.name!r}, {self.value!r})"


class ExpressionStatement(Node):
    def __init__(self, expression: Node):
        self.expression = expression

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}ExpressionStatement",
            self.expression.pretty(indent + 2)
        ])

    def __repr__(self):
        return f"ExpressionStatement({self.expression})"

class Block(Node):
    def __init__(self, statements: list[Node] | None = None):
        self.statements: list[Node] = (
            statements if statements is not None else []
        )

    def addNode(self, node: Node):
        self.statements.append(node)

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        if not self.statements:
            return f"{prefix}Block: empty"

        statements = "\n".join(
            statement.pretty(indent + 2)
            for statement in self.statements
        )

        return f"{prefix}Block:\n{statements}"

    def __repr__(self):
        statements = ", ".join(
            repr(statement)
            for statement in self.statements
        )

        return f"Block([{statements}])"

class ElseIfBranch(Node):
    def __init__(self, condition: Node, body: Block):
        self.condition: Node = condition
        self.body: Block = body

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}ElseIfBranch",
            self.child("condition", self.condition, indent + 2),
            self.child("body", self.body, indent + 2)
        ])

    def __repr__(self):
        return f"ElseIfBranch({self.condition}, {self.body})"

class IfStatement(Node):
    def __init__(
        self,
        condition: Node,
        thenBranch: Block,
        elsifBranches: list[ElseIfBranch] | None = None,
        elseBranch: Block | None = None
    ):
        self.condition: Node = condition
        self.thenBranch: Block = thenBranch
        self.elsifBranches: list[ElseIfBranch] = (
            [] if elsifBranches is None else elsifBranches
        )
        self.elseBranch: Block | None = elseBranch

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        lines = [
            f"{prefix}IfStatement",
            self.child("condition", self.condition, indent + 2),
            self.child("then", self.thenBranch, indent + 2)
        ]

        if self.elsifBranches:
            lines.append(
                self.child(
                    "elsif",
                    self.elsifBranches,
                    indent + 2
                )
            )

        if self.elseBranch is not None:
            lines.append(
                self.child(
                    "else",
                    self.elseBranch,
                    indent + 2
                )
            )

        return "\n".join(lines)

    def __repr__(self):
        return (
            f"IfStatement("
            f"{self.condition}, "
            f"{self.thenBranch}, "
            f"elsif={self.elsifBranches}, "
            f"else={self.elseBranch}"
            f")"
        )

class WhileStatement(Node):
    def __init__(self, condition: Node, body: Block):
        self.condition: Node = condition
        self.body: Block = body

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}WhileStatement",
            self.child("condition", self.condition, indent + 2),
            self.child("body", self.body, indent + 2)
        ])

    def __repr__(self):
        return (
            f"WhileStatement("
            f"{self.condition}, "
            f"{self.body}"
            f")"
        )

class UntilStatement(Node):
    def __init__(self, condition: Node, body: Block):
        self.condition: Node = condition
        self.body: Block = body

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}UntilStatement",
            self.child("condition", self.condition, indent + 2),
            self.child("body", self.body, indent + 2)
        ])

    def __repr__(self):
        return (
            f"UntilStatement("
            f"{self.condition}, "
            f"{self.body}"
            f")"
        )

class Parameter(Node):
    def __init__(
        self,
        paramType: TypeNode,
        name: Identifier,
        defaultValue: Node = UNINITIALIZED
    ):
        self.paramType: TypeNode = paramType
        self.name: Identifier = name
        self.defaultValue: Node = defaultValue

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}Parameter",
            self.child("type", self.paramType, indent + 2),
            self.child("name", self.name, indent + 2),
            self.child("default", self.defaultValue, indent + 2)
        ])

    def __repr__(self):
        return (
            f"Parameter("
            f"{self.paramType}, "
            f"{self.name}, "
            f"defaultValue={self.defaultValue!r}"
            f")"
        )

class FunctionDeclaration(Node):
    def __init__(
        self,
        returnType: TypeNode,
        name: Identifier,
        parameters: list[Parameter],
        body: Block
    ):
        self.returnType: TypeNode = returnType
        self.name: Identifier = name
        self.parameters: list[Parameter] = parameters
        self.body: Block = body

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}FunctionDeclaration",
            self.child("returnType", self.returnType, indent + 2),
            self.child("name", self.name, indent + 2),
            self.child("parameters", self.parameters, indent + 2),
            self.child("body", self.body, indent + 2)
        ])

    def __repr__(self):
        return (
            f"FunctionDeclaration("
            f"{self.returnType}, "
            f"{self.name}, "
            f"{self.parameters}, "
            f"{self.body}"
            f")"
        )

class ReturnStatement(Node):
    def __init__(self, value: Node | None = None):
        self.value: Node | None = value

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        if self.value is None:
            return f"{prefix}ReturnStatement"

        return "\n".join([
            f"{prefix}ReturnStatement",
            self.child("value", self.value, indent + 2)
        ])

    def __repr__(self):
        return f"ReturnStatement({self.value})"

class ForStatement(Node):
    def __init__(
        self,
        iterator: Identifier,
        start: Node,
        end: Node,
        body: Block
    ):
        self.iterator: Identifier = iterator
        self.start: Node = start
        self.end: Node = end
        self.body: Block = body

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}ForStatement",
            self.child("iterator", self.iterator, indent + 2),
            self.child("start", self.start, indent + 2),
            self.child("end", self.end, indent + 2),
            self.child("body", self.body, indent + 2)
        ])

    def __repr__(self):
        return (
            f"ForStatement("
            f"{self.iterator}, "
            f"{self.start}, "
            f"{self.end}, "
            f"{self.body}"
            f")"
        )

class ForeachStatement(Node):
    def __init__(
        self,
        iterator: Identifier,
        collection: Node,
        body: Block
    ):
        self.iterator: Identifier = iterator
        self.collection: Node = collection
        self.body: Block = body

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}ForeachStatement",
            self.child("iterator", self.iterator, indent + 2),
            self.child("collection", self.collection, indent + 2),
            self.child("body", self.body, indent + 2)
        ])

    def __repr__(self):
        return (
            f"ForeachStatement("
            f"{self.iterator}, "
            f"{self.collection}, "
            f"{self.body}"
            f")"
        )

class ListLiteral(Node):
    def __init__(self, elements: list[Node]):
        self.elements: list[Node] = elements

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}ListLiteral",
            self.child("elements", self.elements, indent + 2)
        ])

    def __repr__(self):
        elements = ", ".join(repr(element) for element in self.elements)
        return f"ListLiteral([{elements}])"

class ArrayLiteral(Node):
    def __init__(self, elements: list[Node]):
        self.elements: list[Node] = elements

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}ArrayLiteral",
            self.child("elements", self.elements, indent + 2)
        ])

    def __repr__(self):
        elements = ", ".join(
            repr(element)
            for element in self.elements
        )

        return f"ArrayLiteral(<{elements}>)"

class SetLiteral(Node):
    def __init__(self, elements: list[Node]):
        self.elements: list[Node] = elements

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}SetLiteral",
            self.child(
                "elements",
                self.elements,
                indent + 2
            )
        ])

    def __repr__(self):
        elements = ", ".join(
            repr(element)
            for element in self.elements
        )

        return f"SetLiteral(({elements}))"

class SliceAccess(Node):
    def __init__(
        self,
        target: Node,
        start: Node | None,
        end: Node | None
    ):
        self.target: Node = target
        self.start: Node | None = start
        self.end: Node | None = end

    def pretty(self, indent: int = 0) -> str:
        prefix = " " * indent

        return "\n".join([
            f"{prefix}SliceAccess",
            self.child("target", self.target, indent + 2),
            self.child("start", self.start, indent + 2),
            self.child("end", self.end, indent + 2)
        ])

    def __repr__(self):
        return (
            f"SliceAccess("
            f"{self.target}, "
            f"start={self.start}, "
            f"end={self.end}"
            f")"
        )
