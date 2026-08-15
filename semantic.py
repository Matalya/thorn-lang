from contextlib import contextmanager
from dataclasses import dataclass
from ast import literal_eval
from th_ast import *
from module_system import ModuleLoadError

@dataclass
class SemanticIssue:
    message: str
    span: SourceSpan | None = None

    def __str__(self) -> str:
        if self.span is None:
            return self.message

        message = self.message.rstrip(".")

        return (
            f"{message} "
            f"at [{self.span.start}, {self.span.end})"
        )

@dataclass
class VariableSymbol:
    name: str
    declaredType: TypeNode | None
    isConst: bool
    initialized: bool
    declaration: Node


@dataclass
class FunctionSymbol:
    name: str
    declaration: FunctionDeclaration

@dataclass(frozen=True)
class ParameterSignature:
    name: str
    paramType: TypeNode
    hasDefault: bool

@dataclass(frozen=True)
class CollectionMethodSignature:
    name: str
    parameters: tuple[ParameterSignature, ...]
    returnType: TypeNode

@dataclass
class BuiltinFunctionSymbol:
    name: str
    returnType: TypeNode
    parameterTypes: tuple[TypeNode, ...]
    parameterNames: tuple[str, ...]
    minimumArguments: int
    maximumArguments: int


@dataclass
class EnumMemberSymbol:
    name: str
    declaredType: NamedType
    declaration: EnumMemberDeclaration
    enumDeclaration: EnumDeclaration


@dataclass
class AmbiguousEnumMemberSymbol:
    name: str
    members: list[EnumMemberSymbol]


@dataclass
class TypeSymbol:
    name: str
    declaration: NamedTypeDeclaration
    kind: str


@dataclass
class AssignmentTargetInfo:
    valueType: TypeNode | None
    variable: VariableSymbol | None = None
    description: str = "assignment target"
    destinationTypes: tuple[TypeNode, ...] | None = None

Symbol = (
    VariableSymbol
    | FunctionSymbol
    | BuiltinFunctionSymbol
    | EnumMemberSymbol
    | AmbiguousEnumMemberSymbol
)

BUILTIN_ALIASES = {
    "print": ("print", "ᛈᚱᛁᚾᛏ"),
    "input": ("input", "ᛁᚾᛈᚣᛏ"),
    "index": ("index", "ᛁᚾᛞᛖᛉ"),
    "int": ("int", "ᛁᚾᛏ"),
    "str": ("str", "ᛋᛏᚱ", "ᛥᚱ"),
    "float": ("float", "ᚠᛚᚩᛏ"),
    "bool": ("bool", "ᛒᚣᛚ"),
    "char": ("char", "ᚳᚻᚪᚱ"),
    "is_int": ("is_int", "ᛁᛋ_ᛁᚾᛏ"),
    "is_char": ("is_char", "ᛁᛋ_ᚳᚻᚪᚱ"),
    "is_str": ("is_str", "ᛁᛋ_ᛋᛏᚱ"),
    "is_float": ("is_float", "ᛁᛋ_ᚠᛚᚩᛏ"),
    "is_bool": ("is_bool", "ᛁᛋ_ᛒᚣᛚ"),
    "is_list": ("is_list", "ᛁᛋ_ᛚᛁᛋᛏ"),
    "is_arr": ("is_arr", "ᛁᛋ_ᚪᚱ"),
    "is_set": ("is_set", "ᛁᛋ_ᛋᛖᛏ"),
    "is_dict": ("is_dict",),
    "is_empty": ("is_empty", "ᛁᛋ_ᛖᛗᛈᛏᛁ"),
    "is_full": ("is_full", "ᛁᛋ_ᚠᚣᛚ"),
    "to_int": ("to_int", "ᛏᚣ_ᛁᚾᛏ"),
    "to_char": ("to_char", "ᛏᚣ_ᚳᚻᚪᚱ"),
    "to_str": ("to_str", "ᛏᚣ_ᛋᛏᚱ"),
    "to_float": ("to_float", "ᛏᚣ_ᚠᛚᚩᛏ"),
    "to_bool": ("to_bool", "ᛏᚣ_ᛒᚣᛚ"),
    "to_list": ("to_list", "ᛏᚣ_ᛚᛁᛋᛏ"),
    "to_arr": ("to_arr", "ᛏᚣ_ᚪᚱ"),
    "open": ("open", "ᚩᛈᛖᚾ"),
    "pyimport": ("pyimport", "ᛈᛠᛁᛗᛈᛟᚱᛏ")
}

STRUCT_BUILTIN_METHOD_CANONICAL = {
    "new": "new",
    "ᚾᛁᚢ": "new",
    "copy": "copy",
    "ᚳᚪᛈᛁ": "copy",
    "ᚳᚪᛈᛁᛁ": "copy",
    "resembles": "resembles",
    "ᚱᛁᛋᛖᛗᛒᚢᛚ": "resembles",
}

COLLECTION_METHOD_ALIASES = {
    "append": ("append", "ᚢᛈᛖᚾᛞ"),
    "insert": ("insert", "ᛁᚾᛋᚢᚱᛏ"),
    "prepend": ("prepend", "ᛈᚱᛁᛈᛖᚾᛞ"),
    "replace_at": ("replace_at", "ᚱᛁᛈᛚᛠᛋ_ᚫᛏ"),
    "shorten": ("shorten", "ᛋᚻᛟᛏᛖᚾ"),
    "remove_at": ("remove_at", "ᚱᛁᛗᚣᚠ_ᚫᛏ"),
    "shave": ("shave", "ᛋᚻᛠᚠ"),
    "length": ("length", "ᛚᛖᛝᚦ"),
    "find_first": (
        "find_first",
        "ᚠᛠᚾᛞ_ᚠᚢᛋᛏ"
    ),
    "find_nth": (
        "find_nth",
        "ᚠᛠᚾᛞ_ᚾᚦ"
    ),
    "find_last": (
        "find_last",
        "ᚠᛠᚾᛞ_ᛚᚫᛋᛏ"
    ),
    "locate": ("locate", "ᛚᚪᚳᛠᛏ"),
    "compress": ("compress", "ᚳᚢᛗᛈᚱᛖᛋ"),
    "copy": ("copy", "ᚳᚪᛈᛁ", "ᚳᚪᛈᛁᛁ"),
    "resize": ("resize", "ᚱᛁᛋᛠᛋ"),
    "capacity": ("capacity", "ᚳᚢᛈᛋᛁᛏᛁᛁ"),
    "fill": ("fill", "ᚠᛁᛚ"),
    "skintight": ("skintight", "ᛋᚳᛁᚾᛏᛠᛏ"),
    "shrink_to_fit": (
        "shrink_to_fit",
        "ᛋᚻᚱᛁᛝᚳ_ᛏᚣ_ᚠᛁᛏ"
    ),
    "get": ("get", "ᚷᛖᛏ"),
    "has": ("has", "ᚻᚫᛋ"),
    "remove": ("remove", "ᚱᛁᛗᚣᚠ"),
    "keys": ("keys", "ᚳᛁᛁᛋ"),
    "values": ("values", "ᚠᚫᛚᛄᚣᛋ"),
    "items": ("items", "ᛠᛏᛖᛗᛋ"),
    "clear": ("clear", "ᚳᛚᛁᚢᚱ"),
    "join": ("join",),
}

COLLECTION_METHOD_CANONICAL = {
    alias: canonical
    for canonical, aliases in COLLECTION_METHOD_ALIASES.items()
    for alias in aliases
}

INTEGER_METHOD_ALIASES = {
    "gt": ("gt", "ᚷᚦ"),
    "lt": ("lt", "ᛚᚦ"),
    "between": ("between", "ᛒᛁᛏᚹᛁᛁᚾ"),
}
INTEGER_METHOD_CANONICAL = {
    alias: canonical
    for canonical, aliases in INTEGER_METHOD_ALIASES.items()
    for alias in aliases
}

STRING_METHOD_ALIASES = {
    "length": ("length", "ᛚᛖᛝᚦ"),
    "lower": ("lower",),
    "upper": ("upper",),
    "strip": ("strip",),
    "split": ("split",),
    "replace": ("replace",),
    "contains": ("contains",),
    "starts_with": ("starts_with",),
    "ends_with": ("ends_with",),
    "find": ("find",),
    "count": ("count",),
}
STRING_METHOD_CANONICAL = {
    alias: canonical
    for canonical, aliases in STRING_METHOD_ALIASES.items()
    for alias in aliases
}

FILE_METHOD_ALIASES = {
    "read": ("read", "ᚱᛁᛁᛞ"),
    "readline": ("readline", "ᚱᛁᛁᛞᛚᛠᚾ"),
    "readlines": ("readlines", "ᚱᛁᛁᛞᛚᛠᚾᛋ"),
    "write": ("write", "ᚹᚱᛠᛏ"),
    "writelines": ("writelines", "ᚹᚱᛠᛏᛚᛠᚾ"),
    "flush": ("flush", "ᚠᛚᚢᛋᚻ"),
    "seek": ("seek", "ᛋᛁᛁᚳ"),
    "tell": ("tell", "ᛏᛖᛚ"),
    "close": ("close", "ᚳᛚᚩᛋ"),
    "closed": ("closed", "ᚳᛚᚩᛋᛞ"),
    "readable": ("readable", "ᚱᛁᛁᛞᚢᛒᚢᛚ"),
    "writable": ("writable", "ᚹᚱᛠᛏᚢᛒᚢᛚ"),
    "seekable": ("seekable", "ᛋᛁᛁᚳᚢᛒᚢᛚ"),
}
FILE_METHOD_CANONICAL = {
    alias: canonical
    for canonical, aliases in FILE_METHOD_ALIASES.items()
    for alias in aliases
}

NUMERIC_TYPES = (
    Type.INT,
    Type.FLOAT
)

ENUM_BACKING_TYPES = (
    Type.INT,
    Type.FLOAT,
    Type.STR,
    Type.CHAR,
    Type.BOOL
)

ARITHMETIC_OPERATORS = (
    Op.POWER,
    Op.MULT,
    Op.DIV,
    Op.MOD,
    Op.FLOOR_DIV,
    Op.ADD,
    Op.SUB
)

COMPARISON_OPERATORS = (
    Op.EQUALS,
    Op.NOT_EQUAL,
    Op.LESS_THAN,
    Op.MORE_THAN,
    Op.LESS_EQUAL,
    Op.MORE_EQUAL
)

LOGICAL_OPERATORS = (
    Op.AND,
    Op.OR,
    Op.XOR
)

OPERATOR_TEXT = {
    Op.POWER: "^",
    Op.MULT: "*",
    Op.DIV: "/",
    Op.MOD: "%",
    Op.FLOOR_DIV: "//",
    Op.ADD: "+",
    Op.SUB: "-",
    Op.EQUALS: "==",
    Op.NOT_EQUAL: "!=",
    Op.LESS_THAN: "<",
    Op.MORE_THAN: ">",
    Op.LESS_EQUAL: "<=",
    Op.MORE_EQUAL: ">=",
    Op.NOT: "not",
    Op.AND: "and",
    Op.OR: "or",
    Op.XOR: "xor",
    Op.NEG: "-"
}

class Scope:
    def __init__(
        self,
        parent: "Scope | None" = None,
        name: str = "scope"
    ):
        self.parent = parent
        self.name = name

        self.symbols: dict[str, Symbol] = {}

        # Types deliberately live in a separate namespace from
        # variables and functions. This allows declarations such as:
        #
        # struct Person { ... }
        # int Person = 5;
        self.types: dict[str, TypeSymbol] = {}

        self.predeclaredFunctions: dict[
            str,
            FunctionSymbol
        ] = {}

    def root(self) -> "Scope":
        scope = self

        while scope.parent is not None:
            scope = scope.parent

        return scope

    def local(self, name: str) -> Symbol | None:
        return self.symbols.get(name)

    def resolve(self, name: str) -> Symbol | None:
        symbol = self.local(name)

        if symbol is not None:
            return symbol

        function = self.predeclaredFunctions.get(name)

        if function is not None:
            return function

        if self.parent is not None:
            return self.parent.resolve(name)

        return None

    def define(self, symbol: Symbol):
        self.symbols[symbol.name] = symbol

    def localType(
        self,
        name: str
    ) -> TypeSymbol | None:
        return self.types.get(name)

    def resolveType(
        self,
        name: str
    ) -> TypeSymbol | None:
        symbol = self.localType(name)

        if symbol is not None:
            return symbol

        if self.parent is not None:
            return self.parent.resolveType(name)

        return None

    def defineType(
        self,
        symbol: TypeSymbol
    ):
        self.types[symbol.name] = symbol

class SemanticAnalyzer:
    def __init__(
        self,
        *,
        module_loader=None,
        module_path=None
    ):
        self.globalScope = Scope(
            parent=None,
            name="global"
        )

        self.currentScope = self.globalScope
        self.moduleLoader = module_loader
        self.modulePath = module_path
        self.currentFunction: FunctionDeclaration | None = None
        self.currentMethodOwner: StructDeclaration | None = None
        self.loopDepth = 0
        self.currentExpectedType: TypeNode | None = None
        self.structLiteralResults: dict[
            tuple[int, str],
            bool
        ] = {}
        self.validatedEnumDeclarations: set[int] = set()
        self.enumValueDiagnostics: set[tuple[int, int]] = set()
        self.ambiguousEnumValueDiagnostics: set[int] = set()
        self.qualifiedMemberDiagnostics: set[int] = set()
        self.invalidConstantResults: dict[
            int,
            tuple[TypeNode, object]
        ] = {}
        self.invalidLiteralValues: dict[int, object] = {}
        self.invalidLiteralDiagnostics: set[int] = set()
        self.issues: list[SemanticIssue] = []

        self.installBuiltins()

    def analyze(
        self,
        program: Program
    ) -> list[SemanticIssue]:
        self.visit(program)
        return self.issues

    def report(
        self,
        node: Node,
        message: str
    ):
        self.issues.append(
            SemanticIssue(
                message,
                node.span
            )
        )

    @contextmanager
    def scope(self, name: str):
        previous = self.currentScope

        self.currentScope = Scope(
            parent=previous,
            name=name
        )

        try:
            yield self.currentScope
        finally:
            self.currentScope = previous

    @contextmanager
    def functionContext(
        self,
        function: FunctionDeclaration,
        methodOwner: StructDeclaration | None = None
    ):
        previousFunction = self.currentFunction
        previousMethodOwner = self.currentMethodOwner
        previousLoopDepth = self.loopDepth
        self.currentFunction = function
        self.currentMethodOwner = methodOwner
        # A callable declared inside a loop cannot target that outer loop.
        self.loopDepth = 0

        try:
            yield
        finally:
            self.currentFunction = previousFunction
            self.currentMethodOwner = previousMethodOwner
            self.loopDepth = previousLoopDepth

    @contextmanager
    def loopContext(self):
        self.loopDepth += 1
        try:
            yield
        finally:
            self.loopDepth -= 1

    @contextmanager
    def temporarySymbol(self, symbol: Symbol):
        existing = self.currentScope.local(symbol.name)
        self.currentScope.define(symbol)

        try:
            yield symbol
        finally:
            if existing is None:
                self.currentScope.symbols.pop(
                    symbol.name,
                    None
                )
            else:
                self.currentScope.define(existing)

    def activeVariableStates(
        self
    ) -> dict[int, tuple[VariableSymbol, bool]]:
        states: dict[
            int,
            tuple[VariableSymbol, bool]
        ] = {}
        scope = self.currentScope

        while scope is not None:
            for symbol in scope.symbols.values():
                if isinstance(symbol, VariableSymbol):
                    states[id(symbol)] = (
                        symbol,
                        symbol.initialized
                    )

            scope = scope.parent

        return states

    def restoreVariableStates(
        self,
        snapshot: dict[
            int,
            tuple[VariableSymbol, bool]
        ]
    ):
        for symbolId, (symbol, _) in (
            self.activeVariableStates().items()
        ):
            baseline = snapshot.get(symbolId)
            symbol.initialized = (
                baseline[1]
                if baseline is not None
                else False
            )

    def mergeVariableStates(
        self,
        paths: list[
            dict[int, tuple[VariableSymbol, bool]]
        ]
    ):
        for symbolId, (symbol, _) in (
            self.activeVariableStates().items()
        ):
            symbol.initialized = all(
                path.get(
                    symbolId,
                    (symbol, False)
                )[1]
                for path in paths
            )

    def visit(
        self,
        node: Node | None,
        expectedType: TypeNode | None = None
    ):
        if node is None:
            return

        previousExpectedType = self.currentExpectedType
        self.currentExpectedType = expectedType

        try:
            methodName = f"visit{type(node).__name__}"
            method = getattr(
                self,
                methodName,
                self.visitUnknown
            )

            return method(node)
        finally:
            self.currentExpectedType = previousExpectedType

    def visitUnknown(self, node: Node):
        raise NotImplementedError(
            f"No semantic visitor for "
            f"{type(node).__name__}"
        )

    def visitProgram(self, node: Program):
        self.predeclareTypes(node.statements)
        self.predeclareFunctions(node.statements)

        for statement in node.statements:
            self.visit(statement)

    def loadImportedModule(self, node, moduleName: str):
        if self.moduleLoader is None:
            self.report(
                node,
                f"Cannot import module '{moduleName}' without a module loader."
            )
            return None
        try:
            return self.moduleLoader.loadSemantic(moduleName)
        except ModuleLoadError as error:
            self.report(node, str(error))
            return None

    def defineImportedValue(self, node, name: str, symbol) -> bool:
        if self.currentScope.local(name) is not None:
            self.report(node, f"Name '{name}' is already declared in this scope.")
            return False

        if isinstance(symbol, FunctionSymbol):
            self.currentScope.define(FunctionSymbol(name, symbol.declaration))
        elif isinstance(symbol, VariableSymbol):
            self.currentScope.define(VariableSymbol(
                name=name,
                declaredType=symbol.declaredType,
                isConst=True,
                initialized=True,
                declaration=node,
            ))
        elif isinstance(symbol, EnumMemberSymbol):
            self.currentScope.define(EnumMemberSymbol(
                name=name,
                declaredType=symbol.declaredType,
                declaration=symbol.declaration,
                enumDeclaration=symbol.enumDeclaration,
            ))
        else:
            self.report(node, f"Imported name '{name}' is not a value.")
            return False
        return True

    def visitImportStatement(self, node: ImportStatement):
        record = self.loadImportedModule(node, node.moduleName)
        if record is None:
            return
        name = node.bindingName
        if self.currentScope.local(name) is not None:
            self.report(node, f"Name '{name}' is already declared in this scope.")
            return
        moduleType = ModuleType(node.moduleName, record)
        self.currentScope.define(VariableSymbol(
            name=name,
            declaredType=moduleType,
            isConst=True,
            initialized=True,
            declaration=node,
        ))

    def visitFromImportStatement(self, node: FromImportStatement):
        record = self.loadImportedModule(node, node.moduleName)
        if record is None:
            return

        sourceName = node.importedName.name
        bindingName = node.bindingName
        valueSymbol = record.valueSymbol(sourceName)
        typeSymbol = record.typeSymbol(sourceName)

        if valueSymbol is None and typeSymbol is None:
            self.report(
                node.importedName,
                f"Module '{node.moduleName}' has no exported name '{sourceName}'."
            )
            return

        if valueSymbol is not None:
            self.defineImportedValue(node, bindingName, valueSymbol)

        if typeSymbol is not None:
            existing = self.currentScope.resolveType(bindingName)
            if existing is not None:
                self.report(
                    node,
                    f"Type '{bindingName}' is already declared in this scope."
                )
            else:
                self.currentScope.defineType(TypeSymbol(
                    name=bindingName,
                    declaration=typeSymbol.declaration,
                    kind=typeSymbol.kind,
                ))


    def visitBlock(self, node: Block):
        # Thorn uses function-level lexical scope. Braces group
        # control flow, but do not create a variable scope.
        # Type/function hoisting is performed once for the entire
        # containing program or function body, including declarations
        # nested inside these non-scoping control-flow blocks.
        for statement in node.statements:
            self.visit(statement)

    def typeText(
        self,
        typeNode: TypeNode
    ) -> str:
        if isinstance(typeNode, PrimitiveType):
            return str(typeNode.value)

        if isinstance(typeNode, NamedType):
            return typeNode.name.name

        if isinstance(typeNode, ModuleType):
            return f"module({typeNode.moduleName})"

        if isinstance(typeNode, ListType):
            return (
                f"list("
                f"{self.typeText(typeNode.elementType)}"
                f")"
            )

        if isinstance(typeNode, ArrayType):
            if typeNode.isHeterogeneous:
                entries: list[str] = []
                slotTypes = typeNode.slotTypes or []
                index = 0
                while index < len(slotTypes):
                    slotType = slotTypes[index]
                    count = 1
                    while (
                        index + count < len(slotTypes)
                        and self.sameType(
                            slotType,
                            slotTypes[index + count]
                        )
                    ):
                        count += 1
                    rendered = self.typeText(slotType)
                    if len(slotTypes) == 1:
                        entries.append(f"{rendered} * 1")
                        index += count
                        continue
                    entries.append(
                        rendered if count == 1 else f"{rendered} * {count}"
                    )
                    index += count
                return f"arr({', '.join(entries)})"
            return (
                f"arr("
                f"{self.typeText(typeNode.elementType)}, "
                f"{typeNode.capacity}"
                f")"
            )

        if isinstance(typeNode, SetType):
            return (
                f"set("
                f"{self.typeText(typeNode.elementType)}"
                f")"
            )

        if isinstance(typeNode, DictType):
            return (
                f"dict({self.typeText(typeNode.keyType)}, "
                f"{self.typeText(typeNode.valueType)})"
            )

        if isinstance(typeNode, UnionType):
            return " | ".join(
                self.typeText(member)
                for member in typeNode.members
            )

        return type(typeNode).__name__

    def sameType(
        self,
        left: TypeNode,
        right: TypeNode
    ) -> bool:
        if type(left) is not type(right):
            return False

        if isinstance(left, PrimitiveType):
            return left.value == right.value

        if isinstance(left, NamedType):
            if (
                left.resolvedDeclaration is not None
                and right.resolvedDeclaration is not None
            ):
                return left.resolvedDeclaration is right.resolvedDeclaration
            leftName = (
                left.resolvedDeclaration.name.name
                if left.resolvedDeclaration is not None
                else left.name.name
            )
            rightName = (
                right.resolvedDeclaration.name.name
                if right.resolvedDeclaration is not None
                else right.name.name
            )
            return leftName == rightName

        if isinstance(left, ModuleType):
            return left.record is right.record

        if isinstance(left, ListType):
            return self.sameType(
                left.elementType,
                right.elementType
            )

        if isinstance(left, ArrayType):
            if left.isHeterogeneous or right.isHeterogeneous:
                if not (
                    left.isHeterogeneous
                    and right.isHeterogeneous
                ):
                    return False
                leftSlots = left.slotTypes or []
                rightSlots = right.slotTypes or []
                return (
                    len(leftSlots) == len(rightSlots)
                    and all(
                        self.sameType(leftSlot, rightSlot)
                        for leftSlot, rightSlot in zip(
                            leftSlots,
                            rightSlots
                        )
                    )
                )
            return self.sameType(
                left.elementType,
                right.elementType
            )

        if isinstance(left, SetType):
            return self.sameType(
                left.elementType,
                right.elementType
            )

        if isinstance(left, DictType):
            return (
                self.sameType(left.keyType, right.keyType)
                and self.sameType(left.valueType, right.valueType)
            )

        if isinstance(left, UnionType):
            if len(left.members) != len(right.members):
                return False

            unmatched = list(right.members)

            for leftMember in left.members:
                for index, rightMember in enumerate(
                    unmatched
                ):
                    if self.sameType(
                        leftMember,
                        rightMember
                    ):
                        unmatched.pop(index)
                        break
                else:
                    return False

            return not unmatched

        return False

    def isAnyType(
        self,
        typeNode: TypeNode
    ) -> bool:
        return (
            isinstance(typeNode, PrimitiveType)
            and typeNode.value == Type.ANY
        )

    def isPrimitive(
        self,
        typeNode: TypeNode,
        *values: Type
    ) -> bool:
        return (
            isinstance(typeNode, PrimitiveType)
            and typeNode.value in values
        )

    def uniqueUnion(
        self,
        members: list[TypeNode]
    ) -> TypeNode:
        unique: list[TypeNode] = []

        for member in members:
            nestedMembers = (
                member.members
                if isinstance(member, UnionType)
                else [member]
            )

            for nestedMember in nestedMembers:
                if not any(
                    self.sameType(nestedMember, existing)
                    for existing in unique
                ):
                    unique.append(nestedMember)

        if len(unique) == 1:
            return unique[0]

        return UnionType(unique)

    def inferBinaryResult(
        self,
        operator: Op,
        leftType: TypeNode,
        rightType: TypeNode
    ) -> TypeNode | None:
        leftMembers = (
            leftType.members
            if isinstance(leftType, UnionType)
            else [leftType]
        )
        rightMembers = (
            rightType.members
            if isinstance(rightType, UnionType)
            else [rightType]
        )

        if len(leftMembers) > 1 or len(rightMembers) > 1:
            results: list[TypeNode] = []

            # Every possible runtime pairing must support the
            # operation before it is safe on a union value.
            for leftMember in leftMembers:
                for rightMember in rightMembers:
                    result = self.inferBinaryResult(
                        operator,
                        leftMember,
                        rightMember
                    )

                    if result is None:
                        return None

                    results.append(result)

            return self.uniqueUnion(results)

        # `any` must be narrowed or converted before use.
        if (
            self.isAnyType(leftType)
            or self.isAnyType(rightType)
        ):
            return None

        leftIsNumeric = self.isPrimitive(
            leftType,
            *NUMERIC_TYPES
        )
        rightIsNumeric = self.isPrimitive(
            rightType,
            *NUMERIC_TYPES
        )

        if operator in ARITHMETIC_OPERATORS:
            if not (leftIsNumeric and rightIsNumeric):
                return None

            if operator == Op.DIV:
                return PrimitiveType(Type.FLOAT)

            if operator == Op.FLOOR_DIV:
                return PrimitiveType(Type.INT)

            if (
                self.isPrimitive(leftType, Type.FLOAT)
                or self.isPrimitive(rightType, Type.FLOAT)
            ):
                return PrimitiveType(Type.FLOAT)

            return PrimitiveType(Type.INT)

        if operator in LOGICAL_OPERATORS:
            if (
                self.isPrimitive(leftType, Type.BOOL)
                and self.isPrimitive(rightType, Type.BOOL)
            ):
                return PrimitiveType(Type.BOOL)

            return None

        if operator in COMPARISON_OPERATORS:
            bothBoolean = (
                self.isPrimitive(leftType, Type.BOOL)
                and self.isPrimitive(rightType, Type.BOOL)
            )

            if leftIsNumeric and rightIsNumeric:
                return PrimitiveType(Type.BOOL)

            if bothBoolean:
                return PrimitiveType(Type.BOOL)

            # Equality is also meaningful for matching non-numeric
            # types; it never coerces one operand into another.
            if (
                operator in (Op.EQUALS, Op.NOT_EQUAL)
                and self.sameType(leftType, rightType)
            ):
                return PrimitiveType(Type.BOOL)

        return None

    def inferUnaryResult(
        self,
        operator: Op,
        operandType: TypeNode
    ) -> TypeNode | None:
        if isinstance(operandType, UnionType):
            results: list[TypeNode] = []

            for member in operandType.members:
                result = self.inferUnaryResult(
                    operator,
                    member
                )

                if result is None:
                    return None

                results.append(result)

            return self.uniqueUnion(results)

        if self.isAnyType(operandType):
            return None

        if operator == Op.NEG and self.isPrimitive(
            operandType,
            *NUMERIC_TYPES
        ):
            return operandType

        if operator == Op.NOT and self.isPrimitive(
            operandType,
            Type.BOOL
        ):
            return PrimitiveType(Type.BOOL)

        return None


    def isAssignable(
        self,
        sourceType: TypeNode,
        destinationType: TypeNode
    ) -> bool:
        # Any value may be stored in an `any` destination.
        if self.isAnyType(destinationType):
            return True

        # Every possible source-union member must fit.
        if isinstance(sourceType, UnionType):
            return all(
                self.isAssignable(
                    member,
                    destinationType
                )
                for member in sourceType.members
            )

        # A value fits a destination union when it fits
        # at least one member.
        if isinstance(destinationType, UnionType):
            return any(
                self.isAssignable(
                    sourceType,
                    member
                )
                for member in destinationType.members
            )

        # An `any` source cannot flow into a concrete
        # destination without narrowing or conversion.
        if self.isAnyType(sourceType):
            return False

        # Lists are mutable, so their element types must
        # be invariant.
        if (
            isinstance(sourceType, ListType)
            and isinstance(destinationType, ListType)
        ):
            return self.sameType(
                sourceType.elementType,
                destinationType.elementType
            )

        # Homogeneous capacity is runtime metadata rather than part of
        # static identity. A heterogeneous positional schema is part of
        # identity. Array types remain invariant because arrays are mutable.
        if (
            isinstance(sourceType, ArrayType)
            and isinstance(destinationType, ArrayType)
        ):
            if (
                sourceType.isHeterogeneous
                or destinationType.isHeterogeneous
            ):
                return self.sameType(sourceType, destinationType)
            return self.sameType(
                sourceType.elementType,
                destinationType.elementType
            )

        # Sets are immutable, so widening their element
        # type is safe.
        if (
            isinstance(sourceType, SetType)
            and isinstance(destinationType, SetType)
        ):
            return self.isAssignable(
                sourceType.elementType,
                destinationType.elementType
            )

        # Dictionaries are mutable through indexed assignment, so both
        # key and value types are invariant.
        if (
            isinstance(sourceType, DictType)
            and isinstance(destinationType, DictType)
        ):
            return (
                self.sameType(sourceType.keyType, destinationType.keyType)
                and self.sameType(sourceType.valueType, destinationType.valueType)
            )

        return self.sameType(
            sourceType,
            destinationType
        )

    def expressionListAssignable(
        self,
        expressions: list[Node],
        destinationType: TypeNode
    ) -> bool | None:
        unknown = False

        for expression in expressions:
            compatible = self.isExpressionAssignable(
                expression,
                destinationType
            )

            if compatible is False:
                return False

            if compatible is None:
                unknown = True

        if unknown:
            return None

        return True

    def constantExpressionValue(
        self,
        expression: Node
    ) -> tuple[TypeNode, object] | None:
        if isinstance(expression, Literal):
            value: object

            try:
                if expression.litType == Type.INT:
                    value = int(expression.litValue)
                elif expression.litType == Type.FLOAT:
                    value = float(expression.litValue)
                elif expression.litType in (Type.STR, Type.CHAR):
                    value = literal_eval(expression.litValue)
                elif expression.litType == Type.BOOL:
                    value = expression.litValue in (
                        "true",
                        "ᛏᚱᚣ"
                    )
                elif expression.litType == Type.NIL:
                    value = None
                else:
                    return None
            except (ValueError, SyntaxError):
                return None

            literalType = PrimitiveType(expression.litType)

            if not self.constantValueMatchesType(
                literalType,
                value
            ):
                self.invalidLiteralValues[id(expression)] = value
                return None

            return literalType, value

        if (
            isinstance(expression, UnaryOp)
        ):
            operand = self.constantExpressionValue(
                expression.right
            )

            if operand is None:
                return None

            if (
                expression.op == Op.NEG
                and self.isPrimitive(
                    operand[0],
                    Type.INT,
                    Type.FLOAT
                )
            ):
                return operand[0], -operand[1]

            if (
                expression.op == Op.NOT
                and self.isPrimitive(
                    operand[0],
                    Type.BOOL
                )
            ):
                return PrimitiveType(Type.BOOL), not operand[1]

            return None

        if isinstance(expression, BinaryOp):
            left = self.constantExpressionValue(expression.left)
            right = self.constantExpressionValue(expression.right)

            if left is None or right is None:
                return None

            resultType = self.inferBinaryResult(
                expression.op,
                left[0],
                right[0]
            )

            if resultType is None:
                return None

            leftValue = left[1]
            rightValue = right[1]

            try:
                operations = {
                    Op.POWER: lambda: leftValue ** rightValue,
                    Op.MULT: lambda: leftValue * rightValue,
                    Op.DIV: lambda: leftValue / rightValue,
                    Op.MOD: lambda: leftValue % rightValue,
                    Op.FLOOR_DIV: lambda: int(
                        leftValue // rightValue
                    ),
                    Op.ADD: lambda: leftValue + rightValue,
                    Op.SUB: lambda: leftValue - rightValue,
                    Op.EQUALS: lambda: leftValue == rightValue,
                    Op.NOT_EQUAL: lambda: leftValue != rightValue,
                    Op.MORE_THAN: lambda: leftValue > rightValue,
                    Op.LESS_THAN: lambda: leftValue < rightValue,
                    Op.MORE_EQUAL: lambda: leftValue >= rightValue,
                    Op.LESS_EQUAL: lambda: leftValue <= rightValue,
                    Op.AND: lambda: leftValue and rightValue,
                    Op.OR: lambda: leftValue or rightValue,
                    Op.XOR: lambda: bool(leftValue) != bool(rightValue)
                }
                operation = operations.get(expression.op)

                if operation is None:
                    return None

                resultValue = operation()

                if not self.constantValueMatchesType(
                    resultType,
                    resultValue
                ):
                    self.invalidConstantResults[id(expression)] = (
                        resultType,
                        resultValue
                    )
                    return None

                return resultType, resultValue
            except (ArithmeticError, TypeError, ValueError):
                return None

        return None

    def constantValueMatchesType(
        self,
        typeNode: TypeNode,
        value: object
    ) -> bool:
        if not isinstance(typeNode, PrimitiveType):
            return False

        if typeNode.value == Type.INT:
            return type(value) is int

        if typeNode.value == Type.FLOAT:
            return type(value) is float

        if typeNode.value == Type.BOOL:
            return type(value) is bool

        if typeNode.value == Type.STR:
            return type(value) is str

        if typeNode.value == Type.CHAR:
            return type(value) is str and len(value) == 1

        if typeNode.value == Type.NIL:
            return value is None

        if typeNode.value == Type.ANY:
            return True

        return False

    def enumAcceptsConstant(
        self,
        declaration: EnumDeclaration,
        constantType: TypeNode,
        constantValue: object
    ) -> bool:
        return any(
            member.hasResolvedValue
            and member.resolvedType is not None
            and self.sameType(
                member.resolvedType,
                constantType
            )
            and member.resolvedValue == constantValue
            for member in declaration.members
        )

    def checkEnumConstantAssignment(
        self,
        expression: Node,
        destinationType: TypeNode
    ) -> tuple[bool, bool | None, TypeNode | None]:
        constant = self.constantExpressionValue(expression)

        if constant is None:
            return False, None, None

        constantType, constantValue = constant

        if isinstance(destinationType, NamedType):
            declaration = self.enumDeclaration(
                destinationType.name.name
            )

            if declaration is None:
                return False, None, None

            if self.enumAcceptsConstant(
                declaration,
                constantType,
                constantValue
            ):
                return (
                    True,
                    True,
                    NamedType(declaration.name)
                )

            diagnosticKey = (id(expression), id(declaration))

            if diagnosticKey not in self.enumValueDiagnostics:
                self.report(
                    expression,
                    (
                        f"Value {constantValue!r} is not a "
                        f"declared value of enum "
                        f"'{declaration.name.name}'."
                    )
                )
                self.enumValueDiagnostics.add(diagnosticKey)

            return True, None, None

        if not isinstance(destinationType, UnionType):
            return False, None, None

        enumMatches: list[EnumDeclaration] = []
        containsEnum = False
        primitiveCompatible = False

        for member in destinationType.members:
            declaration = (
                self.enumDeclaration(member.name.name)
                if isinstance(member, NamedType)
                else None
            )

            if declaration is not None:
                containsEnum = True

                if self.enumAcceptsConstant(
                    declaration,
                    constantType,
                    constantValue
                ):
                    enumMatches.append(declaration)
                continue

            if self.isAssignable(
                constantType,
                member
            ):
                primitiveCompatible = True

        if not containsEnum:
            return False, None, None

        if primitiveCompatible:
            # The expression can retain its ordinary primitive type;
            # no contextual enum conversion is needed.
            return True, True, constantType

        if len(enumMatches) == 1:
            return (
                True,
                True,
                NamedType(enumMatches[0].name)
            )

        if len(enumMatches) > 1:
            if id(expression) not in self.ambiguousEnumValueDiagnostics:
                self.report(
                    expression,
                    (
                        "Enum value is ambiguous; use a qualified "
                        "enum member."
                    )
                )
                self.ambiguousEnumValueDiagnostics.add(id(expression))

            return True, None, None

        return True, False, None

    def enumConstantInterpretations(
        self,
        expression: Node,
        destinationTypes: list[TypeNode]
    ) -> tuple[bool, list[TypeNode], list[EnumDeclaration]]:
        constant = self.constantExpressionValue(expression)

        if constant is None:
            return False, [], []

        constantType, constantValue = constant
        combinedDestination = self.uniqueUnion(destinationTypes)
        members = (
            combinedDestination.members
            if isinstance(combinedDestination, UnionType)
            else [combinedDestination]
        )
        containsEnum = False
        enumMatches: list[EnumDeclaration] = []
        seenDeclarations: set[int] = set()

        for member in members:
            declaration = (
                self.enumDeclaration(member.name.name)
                if isinstance(member, NamedType)
                else None
            )

            if declaration is None:
                continue

            containsEnum = True

            if (
                id(declaration) not in seenDeclarations
                and self.enumAcceptsConstant(
                    declaration,
                    constantType,
                    constantValue
                )
            ):
                enumMatches.append(declaration)
                seenDeclarations.add(id(declaration))

        interpretations = [constantType]
        interpretations.extend(
            NamedType(declaration.name)
            for declaration in enumMatches
        )
        return containsEnum, interpretations, enumMatches

    def resolveEnumConstantForAll(
        self,
        expression: Node,
        destinationTypes: list[TypeNode]
    ) -> tuple[bool, bool | None, TypeNode | None]:
        (
            containsEnum,
            interpretations,
            enumMatches
        ) = self.enumConstantInterpretations(
            expression,
            destinationTypes
        )

        if not containsEnum:
            return False, None, None

        compatibleTypes = [
            sourceType
            for sourceType in interpretations
            if all(
                self.isAssignable(sourceType, destinationType)
                for destinationType in destinationTypes
            )
        ]

        if compatibleTypes:
            constantType = interpretations[0]

            # Prefer the expression's ordinary primitive meaning when it
            # already satisfies every destination. Contextual conversion is
            # only needed when that interpretation is insufficient.
            if any(
                self.sameType(sourceType, constantType)
                for sourceType in compatibleTypes
            ):
                return True, True, constantType

            if len(compatibleTypes) == 1:
                return True, True, compatibleTypes[0]

            if id(expression) not in self.ambiguousEnumValueDiagnostics:
                self.report(
                    expression,
                    (
                        "Enum value is ambiguous; use a qualified "
                        "enum member."
                    )
                )
                self.ambiguousEnumValueDiagnostics.add(id(expression))

            return True, None, None

        if len(destinationTypes) == 1:
            applies, compatible, resolvedType = (
                self.checkEnumConstantAssignment(
                    expression,
                    destinationTypes[0]
                )
            )

            if applies and compatible is None:
                return True, None, resolvedType

        if (
            len(enumMatches) > 1
            and id(expression) not in self.ambiguousEnumValueDiagnostics
        ):
            self.report(
                expression,
                (
                    "Enum value is ambiguous; use a qualified "
                    "enum member."
                )
            )
            self.ambiguousEnumValueDiagnostics.add(id(expression))
            return True, None, None

        resolvedType = (
            NamedType(enumMatches[0].name)
            if len(enumMatches) == 1
            else None
        )
        return True, False, resolvedType


    def isExpressionAssignable(
        self,
        expression: Node,
        destinationType: TypeNode
    ) -> bool | None:
        enumCheckApplies, enumCompatible, _ = (
            self.checkEnumConstantAssignment(
                expression,
                destinationType
            )
        )

        if enumCheckApplies:
            return enumCompatible

        if isinstance(expression, StructLiteral):
            return self.isStructLiteralAssignable(
                expression,
                destinationType
            )

        # A fresh collection literal may be checked directly
        # against any collection member of a union.
        if (
            isinstance(
                expression,
                (ListLiteral, ArrayLiteral, SetLiteral, DictLiteral)
            )
            and isinstance(destinationType, UnionType)
        ):
            knownResult = False

            for member in destinationType.members:
                compatible = self.isExpressionAssignable(
                    expression,
                    member
                )

                if compatible is True:
                    return True

                if compatible is False:
                    knownResult = True

            return False if knownResult else None

        if (
            isinstance(expression, ListLiteral)
            and isinstance(destinationType, ListType)
        ):
            return self.expressionListAssignable(
                expression.elements,
                destinationType.elementType
            )

        if (
            isinstance(expression, ArrayLiteral)
            and isinstance(destinationType, ArrayType)
        ):
            if (
                len(expression.elements)
                > destinationType.capacity
            ):
                return False

            if destinationType.isHeterogeneous:
                slotTypes = destinationType.slotTypes or []
                unknown = False
                for element, slotType in zip(
                    expression.elements,
                    slotTypes
                ):
                    compatible = self.isExpressionAssignable(
                        element,
                        slotType
                    )
                    if compatible is False:
                        return False
                    if compatible is None:
                        unknown = True
                return None if unknown else True

            return self.expressionListAssignable(
                expression.elements,
                destinationType.elementType
            )

        if (
            isinstance(expression, SetLiteral)
            and isinstance(destinationType, SetType)
        ):
            return self.expressionListAssignable(
                expression.elements,
                destinationType.elementType
            )

        if (
            isinstance(expression, DictLiteral)
            and isinstance(destinationType, DictType)
        ):
            keysCompatible = self.expressionListAssignable(
                [entry.key for entry in expression.entries],
                destinationType.keyType
            )
            valuesCompatible = self.expressionListAssignable(
                [entry.value for entry in expression.entries],
                destinationType.valueType
            )
            if keysCompatible is False or valuesCompatible is False:
                return False
            if keysCompatible is None or valuesCompatible is None:
                return None
            return True

        sourceType = self.inferExpressionType(
            expression
        )

        if sourceType is None:
            return None

        return self.isAssignable(
            sourceType,
            destinationType
        )

    def inferElementType(
        self,
        elements: list[Node]
    ) -> TypeNode | None:
        if not elements:
            # An empty literal is compatible with any declared
            # element type; later insertions still use that type.
            return PrimitiveType(Type.ANY)

        elementTypes: list[TypeNode] = []

        for element in elements:
            elementType = self.inferExpressionType(
                element
            )

            if elementType is None:
                return None

            elementTypes.append(elementType)

        return self.uniqueUnion(elementTypes)

    def collectionElementType(
        self,
        collectionType: TypeNode
    ) -> TypeNode | None:
        if isinstance(collectionType, ArrayType):
            if collectionType.isHeterogeneous:
                slotTypes = collectionType.slotTypes or []
                if not slotTypes:
                    return PrimitiveType(Type.ANY)
                return self.uniqueUnion(slotTypes)
            return collectionType.elementType

        if isinstance(collectionType, (ListType, SetType)):
            return collectionType.elementType

        if isinstance(collectionType, DictType):
            # Foreach over a dictionary follows Python and iterates keys.
            return collectionType.keyType

        if isinstance(collectionType, UnionType):
            elementTypes: list[TypeNode] = []

            for member in collectionType.members:
                elementType = self.collectionElementType(
                    member
                )

                if elementType is None:
                    return None

                elementTypes.append(elementType)

            return self.uniqueUnion(elementTypes)

        return None

    def constantInteger(self, expression: Node | None) -> int | None:
        if expression is None:
            return None
        constant = self.constantExpressionValue(expression)
        if (
            constant is None
            or not self.isPrimitive(constant[0], Type.INT)
        ):
            return None
        return constant[1]

    def arrayIndexedType(
        self,
        arrayType: ArrayType,
        indexExpression: Node
    ) -> TypeNode | None:
        if not arrayType.isHeterogeneous:
            return arrayType.elementType

        slotTypes = arrayType.slotTypes or []
        index = self.constantInteger(indexExpression)
        if index is None or index < 0:
            return self.collectionElementType(arrayType)
        if index >= len(slotTypes):
            return None
        return slotTypes[index]

    def indexedCollectionType(
        self,
        collectionType: TypeNode,
        indexExpression: Node
    ) -> TypeNode | None:
        if isinstance(collectionType, ArrayType):
            return self.arrayIndexedType(collectionType, indexExpression)
        if isinstance(collectionType, (ListType, SetType)):
            return collectionType.elementType
        if isinstance(collectionType, UnionType):
            indexedTypes: list[TypeNode] = []
            for member in collectionType.members:
                indexedType = self.indexedCollectionType(
                    member,
                    indexExpression
                )
                if indexedType is None:
                    return None
                indexedTypes.append(indexedType)
            return self.uniqueUnion(indexedTypes)
        return None

    def heterogeneousSliceType(
        self,
        arrayType: ArrayType,
        start: Node | None,
        end: Node | None
    ) -> ArrayType | None:
        if not arrayType.isHeterogeneous:
            return arrayType
        startValue = self.constantInteger(start)
        endValue = self.constantInteger(end)
        if start is not None and (startValue is None or startValue < 0):
            return None
        if end is not None and (endValue is None or endValue < 0):
            return None
        slots = (arrayType.slotTypes or [])[slice(startValue, endValue)]
        elementType = (
            self.uniqueUnion(slots)
            if slots
            else PrimitiveType(Type.ANY)
        )
        return ArrayType(
            elementType,
            len(slots),
            slotTypes=slots
        )

    def dictTypes(
        self,
        typeNode: TypeNode
    ) -> list[DictType] | None:
        members = (
            typeNode.members
            if isinstance(typeNode, UnionType)
            else [typeNode]
        )
        if not members or not all(isinstance(member, DictType) for member in members):
            return None
        return members

    def dictIndexedValueType(
        self,
        typeNode: TypeNode
    ) -> TypeNode | None:
        dictionaries = self.dictTypes(typeNode)
        if dictionaries is None:
            return None
        return self.uniqueUnion([
            dictionary.valueType
            for dictionary in dictionaries
        ])

    def isCollectionType(
        self,
        typeNode: TypeNode
    ) -> bool:
        return self.collectionElementType(typeNode) is not None

    def fileMethodSignature(self, methodName: str) -> CollectionMethodSignature | None:
        canonical = FILE_METHOD_CANONICAL.get(methodName)
        if canonical is None:
            return None
        runic = methodName != canonical
        intType = PrimitiveType(Type.INT)
        strType = PrimitiveType(Type.STR)
        boolType = PrimitiveType(Type.BOOL)
        nilType = PrimitiveType(Type.NIL)
        optionalSize = self.uniqueUnion([intType, nilType])

        def parameter(asciiName, runicName, typeNode, default=False):
            return ParameterSignature(
                runicName if runic else asciiName,
                typeNode,
                default,
            )

        methods = {
            "read": ((parameter("size", "ᛋᛠᛋ", optionalSize, True),), strType),
            "readline": ((parameter("size", "ᛋᛠᛋ", optionalSize, True),), strType),
            "readlines": ((), ListType(strType)),
            "write": ((parameter("content", "ᚳᚪᚾᛏᛖᚾᛏ", strType),), intType),
            "writelines": ((parameter("lines", "ᛚᛠᚾᛋ", ListType(strType)),), nilType),
            "flush": ((), nilType),
            "seek": ((
                parameter("offset", "ᚢᚠᛋᛖᛏ", intType),
                parameter("origin", "ᚩᚱᛁᚷᚻᛁᚾ", intType, True),
            ), intType),
            "tell": ((), intType),
            "close": ((), nilType),
            "closed": ((), boolType),
            "readable": ((), boolType),
            "writable": ((), boolType),
            "seekable": ((), boolType),
        }
        parameters, returnType = methods[canonical]
        return CollectionMethodSignature(canonical, parameters, returnType)

    def stringMethodSignature(
        self,
        methodName: str
    ) -> CollectionMethodSignature | None:
        canonical = STRING_METHOD_CANONICAL.get(methodName)
        if canonical is None:
            return None

        strType = PrimitiveType(Type.STR)
        intType = PrimitiveType(Type.INT)
        boolType = PrimitiveType(Type.BOOL)

        def parameter(name, paramType, hasDefault=False):
            return ParameterSignature(name, paramType, hasDefault)

        methods = {
            "length": ((), intType),
            "lower": ((), strType),
            "upper": ((), strType),
            "strip": ((parameter("characters", strType, True),), strType),
            "split": ((parameter("separator", strType, True),), ListType(strType)),
            "replace": ((
                parameter("old", strType),
                parameter("replacement", strType),
                parameter("count", intType, True),
            ), strType),
            "contains": ((parameter("substring", strType),), boolType),
            "starts_with": ((parameter("prefix", strType),), boolType),
            "ends_with": ((parameter("suffix", strType),), boolType),
            "find": ((parameter("substring", strType),), self.uniqueUnion([
                intType,
                PrimitiveType(Type.NIL)
            ])),
            "count": ((parameter("substring", strType),), intType),
        }
        parameters, returnType = methods[canonical]
        return CollectionMethodSignature(canonical, parameters, returnType)

    def collectionMethodSignature(
        self,
        receiverType: TypeNode,
        methodName: str
    ) -> CollectionMethodSignature | None:
        canonicalName = COLLECTION_METHOD_CANONICAL.get(methodName)

        if canonicalName is None:
            return None

        intType = PrimitiveType(Type.INT)
        nilType = PrimitiveType(Type.NIL)
        anyType = PrimitiveType(Type.ANY)
        strType = PrimitiveType(Type.STR)
        optionalIndexType = self.uniqueUnion([
            intType,
            nilType
        ])

        def parameter(
            name: str,
            paramType: TypeNode,
            hasDefault: bool = False
        ) -> ParameterSignature:
            return ParameterSignature(
                name=name,
                paramType=paramType,
                hasDefault=hasDefault
            )

        if canonicalName == "join":
            if not isinstance(receiverType, (ListType, ArrayType, SetType)):
                return None

            elementType = (
                self.collectionElementType(receiverType)
                if isinstance(receiverType, ArrayType)
                else receiverType.elementType
            )
            elementMembers = (
                elementType.members
                if isinstance(elementType, UnionType)
                else [elementType]
            )
            if not elementMembers or not all(
                isinstance(member, PrimitiveType)
                and member.value in (Type.STR, Type.CHAR)
                for member in elementMembers
            ):
                return None

            return CollectionMethodSignature(
                name=canonicalName,
                parameters=(parameter("separator", strType, True),),
                returnType=strType
            )

        if isinstance(receiverType, ListType):
            elementType = receiverType.elementType
            methods = {
                "append": ((parameter("item", elementType),), nilType),
                "insert": ((
                    parameter("item", elementType),
                    parameter("index", intType)
                ), nilType),
                "prepend": ((parameter("item", elementType),), nilType),
                "replace_at": ((
                    parameter("item", elementType),
                    parameter("index", intType)
                ), elementType),
                "shorten": ((
                    parameter("amount", intType, True),
                ), ListType(elementType)),
                "remove_at": ((parameter("index", intType),), elementType),
                "shave": ((
                    parameter("amount", intType, True),
                ), ListType(elementType)),
                "length": ((), intType),
                "find_first": ((
                    parameter("item", anyType),
                ), optionalIndexType),
                "find_nth": ((
                    parameter("item", anyType),
                    parameter("number", intType)
                ), optionalIndexType),
                "find_last": ((
                    parameter("item", anyType),
                ), optionalIndexType),
                "locate": ((parameter("index", intType),), elementType),
                "compress": ((), nilType),
                "copy": ((), receiverType)
            }
        elif isinstance(receiverType, ArrayType):
            elementType = self.collectionElementType(receiverType)
            methods = {
                "length": ((), intType),
                "capacity": ((), intType),
                "append": ((parameter("item", elementType),), nilType),
                "replace_at": ((
                    parameter("item", elementType),
                    parameter("index", intType)
                ), elementType),
                "shorten": ((
                    parameter("amount", intType, True),
                ), ListType(elementType)),
                "find_first": ((
                    parameter("item", anyType),
                ), optionalIndexType),
                "find_nth": ((
                    parameter("item", anyType),
                    parameter("number", intType)
                ), optionalIndexType),
                "find_last": ((
                    parameter("item", anyType),
                ), optionalIndexType),
                "locate": ((parameter("index", intType),), elementType),
                "copy": ((), receiverType),
            }
            if not receiverType.isHeterogeneous:
                methods.update({
                    "resize": ((parameter("new_size", intType),), nilType),
                    "insert": ((
                        parameter("item", elementType),
                        parameter("index", intType)
                    ), nilType),
                    "prepend": ((parameter("item", elementType),), nilType),
                    "remove_at": ((parameter("index", intType),), elementType),
                    "shave": ((
                        parameter("amount", intType, True),
                    ), ListType(elementType)),
                    "compress": ((), nilType),
                    "fill": ((parameter("value", elementType),), nilType),
                    "skintight": ((), nilType),
                    "shrink_to_fit": ((), nilType)
                })
        elif isinstance(receiverType, SetType):
            elementType = receiverType.elementType
            methods = {
                "length": ((), intType),
                "find_first": ((
                    parameter("item", anyType),
                ), optionalIndexType),
                "find_nth": ((
                    parameter("item", anyType),
                    parameter("number", intType)
                ), optionalIndexType),
                "find_last": ((
                    parameter("item", anyType),
                ), optionalIndexType),
                "locate": ((parameter("index", intType),), elementType),
                "copy": ((), receiverType)
            }
        elif isinstance(receiverType, DictType):
            keyType = receiverType.keyType
            valueType = receiverType.valueType
            optionalValueType = self.uniqueUnion([valueType, nilType])
            itemType = ArrayType(
                self.uniqueUnion([keyType, valueType]),
                2
            )
            methods = {
                "length": ((), intType),
                "get": ((
                    parameter("key", keyType),
                    parameter("default", optionalValueType, True),
                ), optionalValueType),
                "has": ((parameter("key", keyType),), PrimitiveType(Type.BOOL)),
                "remove": ((parameter("key", keyType),), valueType),
                "keys": ((), ListType(keyType)),
                "values": ((), ListType(valueType)),
                "items": ((), ListType(itemType)),
                "clear": ((), nilType),
                "copy": ((), receiverType),
            }
        else:
            return None

        signature = methods.get(canonicalName)

        if signature is None:
            return None

        parameters, returnType = signature
        return CollectionMethodSignature(
            name=canonicalName,
            parameters=parameters,
            returnType=returnType
        )

    def collectionMethodSignatures(
        self,
        receiverType: TypeNode,
        methodName: str
    ) -> list[CollectionMethodSignature] | None:
        if isinstance(receiverType, UnionType):
            signatures: list[CollectionMethodSignature] = []

            for member in receiverType.members:
                signature = self.collectionMethodSignature(
                    member,
                    methodName
                )

                if signature is None:
                    return None

                signatures.append(signature)

            return signatures

        signature = self.collectionMethodSignature(
            receiverType,
            methodName
        )
        return [signature] if signature is not None else None

    @staticmethod
    def moduleValueSymbol(moduleType: ModuleType, name: str):
        return moduleType.record.valueSymbol(name)

    def moduleValueType(self, moduleType: ModuleType, name: str):
        symbol = self.moduleValueSymbol(moduleType, name)
        if isinstance(symbol, VariableSymbol):
            return symbol.declaredType
        if isinstance(symbol, EnumMemberSymbol):
            return symbol.declaredType
        return None

    def inferExpressionType(
        self,
        node: Node
    ) -> TypeNode | None:
        if isinstance(node, Literal):
            return PrimitiveType(
                node.litType
            )

        if isinstance(node, CompositeString):
            return PrimitiveType(
                Type.STR
            )

        if isinstance(node, Identifier):
            symbol = self.currentScope.resolve(
                node.name
            )

            if isinstance(
                symbol,
                (VariableSymbol, EnumMemberSymbol)
            ):
                return symbol.declaredType

            return None

        if isinstance(node, BinaryOp):
            leftType = self.inferExpressionType(
                node.left
            )
            rightType = self.inferExpressionType(
                node.right
            )

            if leftType is None or rightType is None:
                return None

            return self.inferBinaryResult(
                node.op,
                leftType,
                rightType
            )

        if isinstance(node, UnaryOp):
            operandType = self.inferExpressionType(
                node.right
            )

            if operandType is None:
                return None

            return self.inferUnaryResult(
                node.op,
                operandType
            )

        if isinstance(node, ListLiteral):
            elementType = self.inferElementType(
                node.elements
            )

            if elementType is None:
                return None

            return ListType(elementType)

        if isinstance(node, ArrayLiteral):
            elementType = self.inferElementType(
                node.elements
            )

            if elementType is None:
                return None

            return ArrayType(
                elementType,
                len(node.elements)
            )

        if isinstance(node, SetLiteral):
            elementType = self.inferElementType(
                node.elements
            )

            if elementType is None:
                return None

            return SetType(elementType)

        if isinstance(node, DictLiteral):
            keyType = self.inferElementType(
                [entry.key for entry in node.entries]
            )
            valueType = self.inferElementType(
                [entry.value for entry in node.entries]
            )
            if keyType is None or valueType is None:
                return None
            return DictType(keyType, valueType)

        if isinstance(node, CollectionConversion):
            if (
                isinstance(node.elementType, NamedType)
                and self.currentScope.resolveType(node.elementType.name.name) is None
            ):
                return None
            if node.collectionKind == "list":
                return ListType(node.elementType)
            if node.collectionKind == "arr":
                return ArrayType(node.elementType, 0)
            return SetType(node.elementType)

        if isinstance(node, DictConversion):
            return DictType(node.keyType, node.valueType)

        if isinstance(node, IndexAccess):
            targetType = self.inferExpressionType(
                node.target
            )

            if (
                isinstance(targetType, PrimitiveType)
                and targetType.value == Type.PYOBJECT
            ):
                return PrimitiveType(Type.PYOBJECT)

            if targetType is not None:
                dictValueType = self.dictIndexedValueType(targetType)
                if dictValueType is not None:
                    return dictValueType
                return self.indexedCollectionType(
                    targetType,
                    node.index
                )

            return None

        if isinstance(node, SliceAccess):
            targetType = self.inferExpressionType(
                node.target
            )

            if (
                isinstance(targetType, PrimitiveType)
                and targetType.value == Type.PYOBJECT
            ):
                return targetType

            if (
                targetType is not None
                and self.isCollectionType(targetType)
            ):
                if isinstance(targetType, ArrayType):
                    return self.heterogeneousSliceType(
                        targetType,
                        node.start,
                        node.end
                    )
                return targetType

            return None

        if isinstance(node, MemberAccess):
            typeOwner, ambiguous = self.qualifiedTypeMemberTarget(
                node.target,
                node.member.name,
                forCall=False
            )

            if ambiguous:
                return None

            if isinstance(typeOwner, EnumDeclaration):
                if self.enumMember(
                    typeOwner,
                    node.member.name
                ) is not None:
                    return NamedType(typeOwner.name)

                return None

            if isinstance(typeOwner, StructDeclaration):
                return None

            targetType = self.inferExpressionType(
                node.target
            )

            if targetType is None:
                return None

            if isinstance(targetType, ModuleType):
                return self.moduleValueType(
                    targetType,
                    node.member.name
                )

            return self.memberType(
                targetType,
                node.member.name
            )

        if isinstance(node, FunctionCall):
            if isinstance(node.callee, MemberAccess):
                typeOwner, ambiguous = (
                    self.qualifiedTypeMemberTarget(
                        node.callee.target,
                        node.callee.member.name,
                        forCall=True
                    )
                )

                if ambiguous:
                    return None

                if isinstance(typeOwner, EnumDeclaration):
                    return None

                if isinstance(typeOwner, StructDeclaration):
                    structBuiltin = STRUCT_BUILTIN_METHOD_CANONICAL.get(
                        node.callee.member.name
                    )
                    if structBuiltin == "new":
                        return NamedType(typeOwner.name)
                    method = self.structMethod(
                        typeOwner,
                        node.callee.member.name,
                        instanceMethod=False
                    )

                    return (
                        method.returnType
                        if method is not None
                        else None
                    )

                targetType = self.inferExpressionType(
                    node.callee.target
                )

                if targetType is None:
                    return None

                if isinstance(targetType, ModuleType):
                    symbol = self.moduleValueSymbol(
                        targetType,
                        node.callee.member.name
                    )
                    return (
                        symbol.declaration.returnType
                        if isinstance(symbol, FunctionSymbol)
                        else None
                    )

                if (
                    isinstance(targetType, PrimitiveType)
                    and targetType.value == Type.PYOBJECT
                ):
                    return PrimitiveType(Type.PYOBJECT)

                if (
                    isinstance(targetType, PrimitiveType)
                    and targetType.value == Type.INT
                    and node.callee.member.name in INTEGER_METHOD_CANONICAL
                ):
                    return PrimitiveType(Type.BOOL)

                if (
                    isinstance(targetType, PrimitiveType)
                    and targetType.value == Type.STR
                    and node.callee.member.name in STRING_METHOD_CANONICAL
                ):
                    signature = self.stringMethodSignature(
                        node.callee.member.name
                    )
                    return signature.returnType if signature is not None else None

                if isinstance(targetType, PrimitiveType) and targetType.value == Type.FILE:
                    signature = self.fileMethodSignature(node.callee.member.name)
                    return signature.returnType if signature is not None else None

                structBuiltin = STRUCT_BUILTIN_METHOD_CANONICAL.get(
                    node.callee.member.name
                )
                if structBuiltin == "copy" and isinstance(targetType, NamedType):
                    if self.structDeclaration(targetType) is not None:
                        return targetType

                if structBuiltin == "resembles" and isinstance(targetType, NamedType):
                    if self.structDeclaration(targetType) is not None:
                        return PrimitiveType(Type.BOOL)

                collectionMethods = self.collectionMethodSignatures(
                    targetType,
                    node.callee.member.name
                )

                if collectionMethods is not None:
                    return self.uniqueUnion([
                        method.returnType
                        for method in collectionMethods
                    ])

                methods = self.memberMethods(
                    targetType,
                    node.callee.member.name
                )

                if methods is None:
                    return None

                return self.uniqueUnion([
                    method.returnType
                    for _, method in methods
                ])

            if not isinstance(node.callee, Identifier):
                return None

            symbol = self.currentScope.resolve(
                node.callee.name
            )

            if isinstance(symbol, FunctionSymbol):
                return symbol.declaration.returnType

            if isinstance(symbol, BuiltinFunctionSymbol):
                return symbol.returnType

            if (
                isinstance(symbol, VariableSymbol)
                and isinstance(symbol.declaredType, PrimitiveType)
                and symbol.declaredType.value == Type.PYOBJECT
            ):
                return PrimitiveType(Type.PYOBJECT)

            return None

        if isinstance(node, StructLiteral):
            if node.typeName is None:
                return None

            return NamedType(node.typeName)

        return None

    def checkInitializer(
        self,
        node: VarDeclaration
    ):
        if isinstance(
            node.varValue,
            Uninitialized
        ):
            return

        compatible = self.isExpressionAssignable(
            node.varValue,
            node.varType
        )

        if compatible is None or compatible:
            return

        sourceType = self.inferExpressionType(
            node.varValue
        )

        sourceText = (
            self.typeText(sourceType)
            if sourceType is not None
            else "<unknown>"
        )

        self.report(
            node.varValue,
            (
                f"Cannot initialize variable "
                f"'{node.varName.name}' of type "
                f"'{self.typeText(node.varType)}' "
                f"with a value of type "
                f"'{sourceText}'."
            )
        )

    def visitVarDeclaration(
        self,
        node: VarDeclaration
    ):
        name = node.varName.name

        # Traverse the declared type. Named-type validation
        # will later happen through these visitors.
        self.visit(node.varType)

        targetScope = (
            self.globalScope
            if node.modifiers.isGlobal
            else self.currentScope
        )

        existing = targetScope.local(name)

        if existing is not None:
            if not node.modifiers.isNew:
                self.report(
                    node.varName,
                    (
                        f"Name '{name}' is already "
                        f"declared in this scope."
                    )
                )

                # Still inspect the initializer so unknown
                # identifiers are not hidden by this error.
                if not isinstance(
                    node.varValue,
                    Uninitialized
                ):
                    self.visit(
                        node.varValue,
                        expectedType=node.varType
                    )

                return

            if not isinstance(
                existing,
                VariableSymbol
            ):
                self.report(
                    node.varName,
                    (
                        f"Cannot redeclare non-variable "
                        f"'{name}' using 'new'."
                    )
                )

                return

        if not isinstance(
            node.varValue,
            Uninitialized
        ):
            # Visit before replacing the existing symbol.
            # This preserves:
            #
            # int value = 5;
            # new str value = str(value);
            self.visit(
                node.varValue,
                expectedType=node.varType
            )

            self.checkInitializer(node)

        symbol = VariableSymbol(
            name=name,
            declaredType=node.varType,
            isConst=node.modifiers.isConst,
            initialized=(
                not isinstance(node.varValue, Uninitialized)
                or (
                    isinstance(node.varType, ArrayType)
                    and node.varType.isHeterogeneous
                )
            ),
            declaration=node
        )

        targetScope.define(symbol)

    def visitIdentifier(self, node: Identifier):
        symbol = self.currentScope.resolve(
            node.name
        )

        if symbol is None:
            if node.name == "self":
                self.report(
                    node,
                    (
                        "'self' can only be used inside an "
                        "instance method."
                    )
                )
                return

            self.report(
                node,
                f"Unknown identifier '{node.name}'."
            )
            return

        if isinstance(symbol, AmbiguousEnumMemberSymbol):
            self.report(
                node,
                (
                    f"Enum member name '{node.name}' is ambiguous; "
                    f"use a qualified enum member."
                )
            )
            return

        if (
            isinstance(symbol, VariableSymbol)
            and not symbol.initialized
        ):
            self.report(
                node,
                (
                    f"Variable '{node.name}' may be "
                    f"uninitialized when used."
                )
            )

    def visitFunctionDeclaration(
        self,
        node: FunctionDeclaration
    ):
        name = node.name.name

        for parameter in node.parameters:
            if parameter.name.name == "self":
                self.report(
                    parameter.name,
                    (
                        "The reserved 'self' parameter can only "
                        "be declared by a struct instance method."
                    )
                )
        existing = self.currentScope.local(name)

        if existing is not None:
            self.report(
                node.name,
                (
                    f"Name '{name}' is already declared "
                    f"in this scope."
                )
            )
            return

        self.currentScope.define(
            FunctionSymbol(
                name=name,
                declaration=node
            )
        )

        self.analyzeCallableBody(node)

    def callableDisplayName(
        self,
        node: FunctionDeclaration,
        methodOwner: StructDeclaration | None = None
    ) -> str:
        if methodOwner is None:
            return node.name.name

        return (
            f"{methodOwner.name.name}."
            f"{node.name.name}"
        )

    def analyzeCallableBody(
        self,
        node: FunctionDeclaration,
        methodOwner: StructDeclaration | None = None,
        instanceMethod: bool = False
    ):
        name = self.callableDisplayName(
            node,
            methodOwner
        )
        callableKind = (
            "Method"
            if methodOwner is not None
            else "Function"
        )

        self.visit(node.returnType)

        # Analyze the function against the current outer state,
        # but do not let assignments in its body mutate that state
        # merely because the function was declared.
        outerStates = self.activeVariableStates()

        try:
            with self.scope(
                f"{callableKind.lower()} {name}"
            ):
                with self.functionContext(
                    node,
                    methodOwner=methodOwner
                ):
                    sawDefaultParameter = False

                    for parameter in node.parameters:
                        self.visit(parameter.paramType)

                        hasDefault = not isinstance(
                            parameter.defaultValue,
                            Uninitialized
                        )

                        if hasDefault:
                            sawDefaultParameter = True

                            if parameter.name.name == "self":
                                self.report(
                                    parameter.defaultValue,
                                    (
                                        "The reserved 'self' parameter "
                                        "cannot have a default value."
                                    )
                                )

                            self.visit(
                                parameter.defaultValue,
                                expectedType=parameter.paramType
                            )
                            compatible = self.isExpressionAssignable(
                                parameter.defaultValue,
                                parameter.paramType
                            )

                            if compatible is False:
                                valueType = self.inferExpressionType(
                                    parameter.defaultValue
                                )
                                valueText = (
                                    self.typeText(valueType)
                                    if valueType is not None
                                    else "<unknown>"
                                )
                                self.report(
                                    parameter.defaultValue,
                                    (
                                        f"Default value for parameter "
                                        f"'{parameter.name.name}' must "
                                        f"have type "
                                        f"'{self.typeText(parameter.paramType)}', "
                                        f"got '{valueText}'."
                                    )
                                )
                        elif sawDefaultParameter:
                            self.report(
                                parameter.name,
                                (
                                    f"Required parameter "
                                    f"'{parameter.name.name}' cannot "
                                    f"follow a parameter with a default "
                                    f"value."
                                )
                            )

                        self.defineParameter(
                            parameter,
                            isConst=(
                                instanceMethod
                                and parameter.name.name == "self"
                            )
                        )

                    self.predeclareTypes(
                        node.body.statements
                    )

                    self.predeclareFunctions(
                        node.body.statements
                    )

                    for statement in node.body.statements:
                        self.visit(statement)

                    if (
                        not self.isPrimitive(
                            node.returnType,
                            Type.NIL
                        )
                        and not self.blockDefinitelyReturns(
                            node.body
                        )
                    ):
                        self.report(
                            node.name,
                            (
                                f"{callableKind} '{name}' must return "
                                f"a value of type "
                                f"'{self.typeText(node.returnType)}' "
                                f"on every path."
                            )
                        )
        finally:
            self.restoreVariableStates(
                outerStates
            )


    def defineParameter(
        self,
        node: Parameter,
        isConst: bool = False
    ):
        name = node.name.name
        existing = self.currentScope.local(name)

        if existing is not None:
            self.report(
                node.name,
                f"Duplicate parameter '{name}'."
            )

            return

        self.currentScope.define(
            VariableSymbol(
                name=name,
                declaredType=node.paramType,
                isConst=isConst,
                initialized=True,
                declaration=node
            )
        )


    def visitParameter(self, node: Parameter):
        # Parameters are handled by defineParameter().
        pass

    def isIndexAssignableType(
        self,
        typeNode: TypeNode
    ) -> bool:
        if isinstance(
            typeNode,
            (ListType, ArrayType, DictType)
        ):
            return True

        if isinstance(typeNode, UnionType):
            return all(
                self.isIndexAssignableType(member)
                for member in typeNode.members
            )

        return False

    def checkAssignmentTarget(
        self,
        target: Node
    ) -> AssignmentTargetInfo | None:
        if isinstance(target, Identifier):
            symbol = self.currentScope.resolve(
                target.name
            )

            if symbol is None:
                self.report(
                    target,
                    (
                        f"Cannot assign to unknown identifier "
                        f"'{target.name}'."
                    )
                )
                return None

            if isinstance(symbol, EnumMemberSymbol):
                self.report(
                    target,
                    (
                        f"Cannot assign to enum member "
                        f"'{symbol.enumDeclaration.name.name}."
                        f"{symbol.name}'; enum members are constant."
                    )
                )
                return None

            if isinstance(symbol, AmbiguousEnumMemberSymbol):
                self.report(
                    target,
                    (
                        f"Enum member name '{target.name}' is "
                        f"ambiguous; use a qualified enum member."
                    )
                )
                return None

            if not isinstance(symbol, VariableSymbol):
                self.report(
                    target,
                    (
                        f"Cannot assign to non-variable "
                        f"'{target.name}'."
                    )
                )
                return None

            if symbol.isConst:
                self.report(
                    target,
                    (
                        f"Cannot reassign const variable "
                        f"'{target.name}'."
                    )
                )
                return None

            return AssignmentTargetInfo(
                valueType=symbol.declaredType,
                variable=symbol,
                description=(
                    f"variable '{symbol.name}'"
                )
            )

        if isinstance(target, IndexAccess):
            # Perform ordinary collection/index validation.
            self.visitIndexAccess(target)

            collectionType = self.inferExpressionType(
                target.target
            )

            if collectionType is None:
                return AssignmentTargetInfo(
                    valueType=None,
                    description="indexed element"
                )

            if not self.isCollectionType(
                collectionType
            ):
                # visitIndexAccess() already reported this.
                return None

            if not self.isIndexAssignableType(
                collectionType
            ):
                self.report(
                    target,
                    (
                        f"Cannot assign through an index of "
                        f"collection type "
                        f"'{self.typeText(collectionType)}' "
                        f"because it is immutable."
                    )
                )
                return None

            return AssignmentTargetInfo(
                valueType=(
                    self.dictIndexedValueType(collectionType)
                    or self.indexedCollectionType(
                        collectionType,
                        target.index
                    )
                ),
                description="indexed element"
            )

        if isinstance(target, MemberAccess):
            typeOwner, ambiguous = self.qualifiedTypeMemberTarget(
                target.target,
                target.member.name,
                forCall=False
            )

            if ambiguous:
                self.reportQualifiedMemberAmbiguity(target)
                return None

            if isinstance(typeOwner, EnumDeclaration):
                member = self.enumMember(
                    typeOwner,
                    target.member.name
                )

                if member is None:
                    self.visitMemberAccess(target)
                else:
                    self.report(
                        target.member,
                        (
                            f"Cannot assign to enum member "
                            f"'{typeOwner.name.name}."
                            f"{target.member.name}'; enum members "
                            f"are constant."
                        )
                    )

                return None

            if isinstance(typeOwner, StructDeclaration):
                self.visitMemberAccess(target)
                return None

            self.visitMemberAccess(target)
            targetType = self.inferExpressionType(
                target.target
            )

            if targetType is None:
                return AssignmentTargetInfo(
                    valueType=None,
                    description=(
                        f"field '{target.member.name}'"
                    )
                )

            fields = self.memberFields(
                targetType,
                target.member.name
            )

            if fields is None:
                # visitMemberAccess() already reported the error.
                return None

            if any(
                field.modifiers.isConst
                for field in fields
            ):
                self.report(
                    target.member,
                    (
                        f"Cannot assign to const struct field "
                        f"'{target.member.name}'."
                    )
                )
                return None

            destinationTypes = tuple(
                field.fieldType
                for field in fields
            )

            return AssignmentTargetInfo(
                valueType=self.uniqueUnion(
                    list(destinationTypes)
                ),
                description=(
                    f"field '{target.member.name}'"
                ),
                destinationTypes=destinationTypes
            )

        self.report(
            target,
            "Invalid assignment target."
        )
        return None


    def visitVarAssign(
        self,
        node: VarAssign
    ):
        targetInfo = self.checkAssignmentTarget(
            node.target
        )

        self.visit(
            node.value,
            expectedType=(
                targetInfo.valueType
                if targetInfo is not None
                else None
            )
        )

        if targetInfo is None:
            return

        if targetInfo.variable is not None:
            # Keep considering the target initialized even if
            # the value later produces a type diagnostic. This
            # avoids cascading uninitialized errors.
            targetInfo.variable.initialized = True

        destinationType = targetInfo.valueType

        if destinationType is None:
            return

        destinationTypes = (
            targetInfo.destinationTypes
            if targetInfo.destinationTypes is not None
            else (destinationType,)
        )

        enumCheckApplies, enumCompatible, resolvedEnumType = (
            self.resolveEnumConstantForAll(
                node.value,
                list(destinationTypes)
            )
        )

        if enumCheckApplies:
            if enumCompatible is None:
                return

            if enumCompatible:
                return

            sourceType = (
                resolvedEnumType
                if resolvedEnumType is not None
                else self.inferExpressionType(node.value)
            )
            sourceText = (
                self.typeText(sourceType)
                if sourceType is not None
                else "<unknown>"
            )
            self.report(
                node.value,
                (
                    f"Cannot assign a value of type "
                    f"'{sourceText}' to "
                    f"{targetInfo.description} of type "
                    f"'{self.typeText(destinationType)}'."
                )
            )
            return

        resolvedSourceType: TypeNode | None = None

        # A contextual anonymous literal must resolve to exactly one
        # nominal struct type. After resolution, that one concrete
        # type must be assignable to every possible union-member field
        # type—not merely to the struct members of the union.
        if (
            isinstance(node.value, StructLiteral)
            and node.value.typeName is None
        ):
            combinedDestination = self.uniqueUnion(
                list(destinationTypes)
            )
            candidates = self.structLiteralCandidates(
                combinedDestination
            )

            if len(candidates) != 1:
                # Reuse the existing ambiguity/unresolved diagnostic
                # machinery. The earlier visit may already have
                # reported it; the result cache prevents duplicates.
                self.isExpressionAssignable(
                    node.value,
                    combinedDestination
                )
                return

            declaration = candidates[0]

            if not self.validateStructLiteral(
                node.value,
                declaration
            ):
                return

            resolvedSourceType = NamedType(
                declaration.name
            )

            compatibilities = [
                self.isAssignable(
                    resolvedSourceType,
                    possibleType
                )
                for possibleType in destinationTypes
            ]
        else:
            compatibilities = [
                self.isExpressionAssignable(
                    node.value,
                    possibleType
                )
                for possibleType in destinationTypes
            ]

        if all(
            compatible is True
            for compatible in compatibilities
        ):
            return

        if not any(
            compatible is False
            for compatible in compatibilities
        ):
            return

        sourceType = (
            resolvedSourceType
            if resolvedSourceType is not None
            else self.inferExpressionType(node.value)
        )

        sourceText = (
            self.typeText(sourceType)
            if sourceType is not None
            else "<unknown>"
        )

        self.report(
            node.value,
            (
                f"Cannot assign a value of type "
                f"'{sourceText}' to "
                f"{targetInfo.description} of type "
                f"'{self.typeText(destinationType)}'."
            )
        )


    def visitCompoundAssign(
        self,
        node: CompoundAssign
    ):
        targetInfo = self.checkAssignmentTarget(
            node.target
        )

        self.visit(node.value)

        if targetInfo is None:
            return

        if (
            targetInfo.variable is not None
            and not targetInfo.variable.initialized
        ):
            self.report(
                node.target,
                (
                    f"Variable "
                    f"'{targetInfo.variable.name}' may be "
                    f"uninitialized before compound assignment."
                )
            )
            return

        targetType = targetInfo.valueType
        valueType = self.inferExpressionType(
            node.value
        )

        if targetType is None or valueType is None:
            return

        operator = OPERATOR_TEXT[node.op]
        destinationTypes = (
            targetInfo.destinationTypes
            if targetInfo.destinationTypes is not None
            else (targetType,)
        )

        for possibleType in destinationTypes:
            resultType = self.inferBinaryResult(
                node.op,
                possibleType,
                valueType
            )

            if resultType is None:
                self.report(
                    node,
                    (
                        f"Operator '{operator}' cannot be "
                        f"applied to values of type "
                        f"'{self.typeText(possibleType)}' and "
                        f"'{self.typeText(valueType)}'."
                    )
                )
                return

            if self.isAssignable(
                resultType,
                possibleType
            ):
                continue

            self.report(
                node,
                (
                    f"Compound assignment '{operator}=' produces "
                    f"a value of type "
                    f"'{self.typeText(resultType)}', which cannot "
                    f"be assigned back to "
                    f"{targetInfo.description} of type "
                    f"'{self.typeText(possibleType)}'."
                )
            )
            return

    def requireExpressionType(
        self,
        expression: Node,
        requiredType: TypeNode,
        context: str
    ):
        actualType = self.inferExpressionType(
            expression
        )

        # The expression visitor is responsible for errors such as
        # unknown names and invalid operators. Do not obscure those
        # diagnostics with a second, speculative context error.
        if actualType is None:
            return

        if self.sameType(actualType, requiredType):
            return

        self.report(
            expression,
            (
                f"{context} must have type "
                f"'{self.typeText(requiredType)}', got "
                f"'{self.typeText(actualType)}'."
            )
        )

    def visitExpressionStatement(
        self,
        node: ExpressionStatement
    ):
        self.visit(node.expression)


    def visitBinaryOp(self, node: BinaryOp):
        self.visit(node.left)
        self.visit(node.right)

        leftType = self.inferExpressionType(
            node.left
        )
        rightType = self.inferExpressionType(
            node.right
        )

        if leftType is None or rightType is None:
            return

        if self.inferBinaryResult(
            node.op,
            leftType,
            rightType
        ) is not None:
            return

        self.report(
            node,
            (
                f"Operator '{OPERATOR_TEXT[node.op]}' cannot be "
                f"applied to values of type "
                f"'{self.typeText(leftType)}' and "
                f"'{self.typeText(rightType)}'."
            )
        )


    def visitUnaryOp(self, node: UnaryOp):
        self.visit(node.right)

        operandType = self.inferExpressionType(
            node.right
        )

        if operandType is None:
            return

        if self.inferUnaryResult(
            node.op,
            operandType
        ) is not None:
            return

        self.report(
            node,
            (
                f"Operator '{OPERATOR_TEXT[node.op]}' cannot be "
                f"applied to a value of type "
                f"'{self.typeText(operandType)}'."
            )
        )

    def callArgumentValue(self, argument: Node) -> Node:
        return (
            argument.value
            if isinstance(argument, NamedArgument)
            else argument
        )

    def parameterSignatures(
        self,
        parameters: list[Parameter]
    ) -> list[ParameterSignature]:
        return [
            ParameterSignature(
                name=parameter.name.name,
                paramType=parameter.paramType,
                hasDefault=not isinstance(
                    parameter.defaultValue,
                    Uninitialized
                )
            )
            for parameter in parameters
        ]

    def builtinParameterSignatures(
        self,
        symbol: BuiltinFunctionSymbol
    ) -> list[ParameterSignature]:
        return [
            ParameterSignature(
                name=name,
                paramType=paramType,
                hasDefault=index >= symbol.minimumArguments
            )
            for index, (name, paramType) in enumerate(
                zip(
                    symbol.parameterNames,
                    symbol.parameterTypes
                )
            )
        ]

    def bindCallArguments(
        self,
        arguments: list[Node],
        parameters: list[ParameterSignature]
    ) -> tuple[
        dict[int, ParameterSignature],
        list[tuple[str, int | None, str | None]]
    ]:
        bindings: dict[int, ParameterSignature] = {}
        boundParameterIndexes: set[int] = set()
        problems: list[tuple[str, int | None, str | None]] = []
        sawNamedArgument = False
        seenNamedArguments: set[str] = set()
        nextPositionalIndex = 0
        reportedTooMany = False

        parameterIndexes = {
            parameter.name: index
            for index, parameter in enumerate(parameters)
        }

        for argumentIndex, argument in enumerate(arguments):
            if isinstance(argument, NamedArgument):
                sawNamedArgument = True
                name = argument.name.name

                if name in seenNamedArguments:
                    problems.append((
                        "duplicate_named",
                        argumentIndex,
                        name
                    ))
                    continue

                seenNamedArguments.add(name)
                parameterIndex = parameterIndexes.get(name)

                if parameterIndex is None:
                    problems.append((
                        "unknown_named",
                        argumentIndex,
                        name
                    ))
                    continue

                if parameterIndex in boundParameterIndexes:
                    problems.append((
                        "multiple_values",
                        argumentIndex,
                        name
                    ))
                    continue

                boundParameterIndexes.add(parameterIndex)
                bindings[argumentIndex] = parameters[parameterIndex]
                continue

            if sawNamedArgument:
                problems.append((
                    "positional_after_named",
                    argumentIndex,
                    None
                ))

            while nextPositionalIndex in boundParameterIndexes:
                nextPositionalIndex += 1

            if nextPositionalIndex >= len(parameters):
                if not reportedTooMany:
                    problems.append((
                        "too_many",
                        argumentIndex,
                        None
                    ))
                    reportedTooMany = True
                continue

            boundParameterIndexes.add(nextPositionalIndex)
            bindings[argumentIndex] = parameters[nextPositionalIndex]
            nextPositionalIndex += 1

        for parameterIndex, parameter in enumerate(parameters):
            if (
                parameterIndex not in boundParameterIndexes
                and not parameter.hasDefault
            ):
                problems.append((
                    "missing_required",
                    None,
                    parameter.name
                ))

        return bindings, problems

    def callableArgumentExpectation(
        self,
        parameters: list[ParameterSignature]
    ) -> str:
        minimum = sum(
            not parameter.hasDefault
            for parameter in parameters
        )
        maximum = len(parameters)

        if minimum == maximum:
            return f"{minimum} argument(s)"

        return (
            f"between {minimum} and {maximum} argument(s)"
        )

    def reportCallBindingProblems(
        self,
        node: FunctionCall,
        parameters: list[ParameterSignature],
        problems: list[tuple[str, int | None, str | None]],
        callableKind: str,
        callableName: str
    ):
        missing = [
            name
            for code, _, name in problems
            if code == "missing_required" and name is not None
        ]
        nonMissingProblems = [
            problem
            for problem in problems
            if problem[0] != "missing_required"
        ]

        for code, argumentIndex, name in nonMissingProblems:
            argument = (
                node.arguments[argumentIndex]
                if argumentIndex is not None
                else node
            )

            if code == "positional_after_named":
                message = (
                    "Positional arguments cannot follow named "
                    "arguments."
                )
            elif code == "too_many":
                message = (
                    f"{callableKind} '{callableName}' expects "
                    f"{self.callableArgumentExpectation(parameters)}, "
                    f"got {len(node.arguments)}."
                )
            elif code == "unknown_named":
                message = (
                    f"{callableKind} '{callableName}' has no "
                    f"parameter named '{name}'."
                )
            else:
                message = (
                    f"Call to {callableKind.lower()} "
                    f"'{callableName}' provides parameter "
                    f"'{name}' more than once."
                )

            self.report(argument, message)

        if missing:
            missingText = ", ".join(
                f"'{name}'"
                for name in missing
            )
            self.report(
                node,
                (
                    f"{callableKind} '{callableName}' expects "
                    f"{self.callableArgumentExpectation(parameters)}, "
                    f"got {len(node.arguments)}; missing required "
                    f"parameter(s) {missingText}."
                )
            )

    def checkCallableArguments(
        self,
        node: FunctionCall,
        parameterLists: list[list[ParameterSignature]],
        callableKind: str,
        callableName: str,
        receiverType: TypeNode | None = None
    ):
        bindingResults = [
            self.bindCallArguments(
                node.arguments,
                parameters
            )
            for parameters in parameterLists
        ]

        for argumentIndex, argument in enumerate(node.arguments):
            destinationTypes = [
                bindings[argumentIndex].paramType
                for bindings, _ in bindingResults
                if argumentIndex in bindings
            ]
            expectedType = (
                self.uniqueUnion(destinationTypes)
                if len(destinationTypes) == len(parameterLists)
                and destinationTypes
                else None
            )
            self.visit(
                self.callArgumentValue(argument),
                expectedType=expectedType
            )

        if len(parameterLists) == 1:
            bindings, problems = bindingResults[0]
            self.reportCallBindingProblems(
                node,
                parameterLists[0],
                problems,
                callableKind,
                callableName
            )
        else:
            bindings = {}

            if any(problems for _, problems in bindingResults):
                receiverText = (
                    self.typeText(receiverType)
                    if receiverType is not None
                    else "<unknown>"
                )
                self.report(
                    node,
                    (
                        f"Arguments to method '{callableName}' are "
                        f"not valid for every possible receiver in "
                        f"'{receiverText}'."
                    )
                )

        for argumentIndex, argument in enumerate(node.arguments):
            if not all(
                argumentIndex in bindings
                for bindings, _ in bindingResults
            ):
                continue

            destinationTypes = [
                bindings[argumentIndex].paramType
                for bindings, _ in bindingResults
            ]
            value = self.callArgumentValue(argument)
            compatible, sourceType = self.expressionAssignableToAll(
                value,
                destinationTypes
            )

            if compatible is None or compatible:
                continue

            expectedType = self.uniqueUnion(destinationTypes)
            sourceText = (
                self.typeText(sourceType)
                if sourceType is not None
                else "<unknown>"
            )
            argumentDisplay = (
                f"'{argument.name.name}'"
                if isinstance(argument, NamedArgument)
                else str(argumentIndex + 1)
            )

            if len(parameterLists) == 1:
                message = (
                    f"Argument {argumentDisplay} to "
                    f"{callableKind.lower()} '{callableName}' must "
                    f"have type '{self.typeText(expectedType)}', "
                    f"got '{sourceText}'."
                )
            else:
                ownerText = (
                    self.typeText(receiverType)
                    if receiverType is not None
                    else "<unknown>"
                )
                message = (
                    f"Argument {argumentDisplay} to method "
                    f"'{callableName}' on '{ownerText}' must be "
                    f"accepted as type "
                    f"'{self.typeText(expectedType)}' by every "
                    f"possible receiver, got '{sourceText}'."
                )

            self.report(value, message)

    def methodCallParameters(
        self,
        method: FunctionDeclaration,
        instanceMethod: bool
    ) -> list[Parameter]:
        return (
            method.parameters[1:]
            if instanceMethod
            else method.parameters
        )

    def expressionAssignableToAll(
        self,
        expression: Node,
        destinationTypes: list[TypeNode]
    ) -> tuple[bool | None, TypeNode | None]:
        (
            enumCheckApplies,
            enumCompatible,
            resolvedEnumType
        ) = self.resolveEnumConstantForAll(
            expression,
            destinationTypes
        )

        if enumCheckApplies:
            if enumCompatible is None:
                return None, resolvedEnumType

            if not enumCompatible:
                return False, resolvedEnumType

            return True, resolvedEnumType

        combinedDestination = self.uniqueUnion(
            destinationTypes
        )

        if (
            isinstance(expression, StructLiteral)
            and expression.typeName is None
        ):
            candidates = self.structLiteralCandidates(
                combinedDestination
            )

            if len(candidates) != 1:
                self.isExpressionAssignable(
                    expression,
                    combinedDestination
                )
                return None, None

            declaration = candidates[0]

            if not self.validateStructLiteral(
                expression,
                declaration
            ):
                return None, None

            sourceType = NamedType(declaration.name)
            return (
                all(
                    self.isAssignable(
                        sourceType,
                        destinationType
                    )
                    for destinationType in destinationTypes
                ),
                sourceType
            )

        compatibilities = [
            self.isExpressionAssignable(
                expression,
                destinationType
            )
            for destinationType in destinationTypes
        ]

        if all(
            compatible is True
            for compatible in compatibilities
        ):
            return True, self.inferExpressionType(expression)

        if any(
            compatible is False
            for compatible in compatibilities
        ):
            return False, self.inferExpressionType(expression)

        return None, self.inferExpressionType(expression)

    def checkMethodCallArguments(
        self,
        node: FunctionCall,
        methods: list[
            tuple[StructDeclaration, FunctionDeclaration]
        ],
        instanceMethod: bool,
        receiverType: TypeNode | None = None
    ):
        parameterLists = [
            self.parameterSignatures(
                self.methodCallParameters(
                    method,
                    instanceMethod
                )
            )
            for _, method in methods
        ]
        methodName = node.callee.member.name
        methodDisplay = (
            f"{methods[0][0].name.name}.{methodName}"
            if len(methods) == 1
            else methodName
        )
        self.checkCallableArguments(
            node,
            parameterLists,
            callableKind="Method",
            callableName=methodDisplay,
            receiverType=receiverType
        )

    def visitStructMethodCall(
        self,
        node: FunctionCall
    ):
        callee = node.callee
        methodName = callee.member.name
        structBuiltinName = STRUCT_BUILTIN_METHOD_CANONICAL.get(methodName)
        typeOwner, ambiguous = self.qualifiedTypeMemberTarget(
            callee.target,
            methodName,
            forCall=True
        )

        if ambiguous:
            self.reportQualifiedMemberAmbiguity(callee)

            for argument in node.arguments:
                self.visit(argument)

            return

        if isinstance(typeOwner, EnumDeclaration):
            for argument in node.arguments:
                self.visit(argument)

            member = self.enumMember(
                typeOwner,
                methodName
            )

            if member is None:
                self.report(
                    callee.member,
                    (
                        f"Enum '{typeOwner.name.name}' has no "
                        f"member named '{methodName}'."
                    )
                )
            else:
                self.report(
                    callee.member,
                    (
                        f"Enum member '{typeOwner.name.name}."
                        f"{methodName}' is not callable."
                    )
                )

            return

        staticOwner = (
            typeOwner
            if isinstance(typeOwner, StructDeclaration)
            else None
        )

        if staticOwner is not None:
            if structBuiltinName == "new":
                parameters = [
                    ParameterSignature(
                        name=field.name.name,
                        paramType=field.fieldType,
                        hasDefault=not isinstance(field.defaultValue, Uninitialized),
                    )
                    for field in staticOwner.fields
                ]
                self.checkCallableArguments(
                    node,
                    [parameters],
                    callableKind="Constructor",
                    callableName=f"{staticOwner.name.name}.new",
                )
                return
            method = self.structMethod(
                staticOwner,
                methodName,
                instanceMethod=False
            )

            if method is None:
                for argument in node.arguments:
                    self.visit(argument)

                instanceMethod = self.structMethod(
                    staticOwner,
                    methodName,
                    instanceMethod=True
                )

                if instanceMethod is not None:
                    self.report(
                        callee.member,
                        (
                            f"Instance method "
                            f"'{staticOwner.name.name}.{methodName}' "
                            f"must be called on a "
                            f"'{staticOwner.name.name}' value."
                        )
                    )
                else:
                    self.report(
                        callee.member,
                        (
                            f"Struct '{staticOwner.name.name}' has "
                            f"no static method named "
                            f"'{methodName}'."
                        )
                    )

                return

            self.checkMethodCallArguments(
                node,
                [(staticOwner, method)],
                instanceMethod=False
            )
            return

        self.visit(callee.target)
        targetType = self.inferExpressionType(
            callee.target
        )

        if targetType is None:
            for argument in node.arguments:
                self.visit(argument)

            if isinstance(callee.target, Identifier):
                symbol = self.currentScope.resolve(
                    callee.target.name
                )

                if (
                    symbol is not None
                    and not isinstance(symbol, VariableSymbol)
                ):
                    self.report(
                        callee.target,
                        (
                            f"Cannot call a method on non-value "
                            f"'{callee.target.name}'."
                        )
                    )

            return

        if isinstance(targetType, ModuleType):
            symbol = self.moduleValueSymbol(targetType, methodName)
            if isinstance(symbol, FunctionSymbol):
                self.checkCallableArguments(
                    node,
                    [self.parameterSignatures(symbol.declaration.parameters)],
                    callableKind="Function",
                    callableName=f"{targetType.moduleName}.{methodName}"
                )
                return

            for argument in node.arguments:
                self.visit(self.callArgumentValue(argument))

            if symbol is not None:
                self.report(
                    callee.member,
                    f"Module member '{targetType.moduleName}.{methodName}' is not callable."
                )
            elif targetType.record.typeSymbol(methodName) is not None:
                self.report(
                    callee.member,
                    f"Import type '{methodName}' with 'from {targetType.moduleName} import {methodName}' before using it."
                )
            else:
                self.report(
                    callee.member,
                    f"Module '{targetType.moduleName}' has no exported name '{methodName}'."
                )
            return

        if (
            isinstance(targetType, PrimitiveType)
            and targetType.value == Type.PYOBJECT
        ):
            for argument in node.arguments:
                self.visit(self.callArgumentValue(argument))
            return

        integerMethod = INTEGER_METHOD_CANONICAL.get(methodName)
        if isinstance(targetType, PrimitiveType) and targetType.value == Type.INT and integerMethod:
            anyType = PrimitiveType(Type.ANY)
            parameters = (
                [ParameterSignature("value", PrimitiveType(Type.INT), False)]
                if integerMethod in ("gt", "lt")
                else [
                    ParameterSignature("lower", anyType, False),
                    ParameterSignature("upper", anyType, False),
                ]
            )
            self.checkCallableArguments(
                node,
                [parameters],
                callableKind="Method",
                callableName=methodName,
                receiverType=targetType,
            )
            return

        stringMethod = STRING_METHOD_CANONICAL.get(methodName)
        if (
            isinstance(targetType, PrimitiveType)
            and targetType.value == Type.STR
            and stringMethod
        ):
            signature = self.stringMethodSignature(methodName)
            self.checkCallableArguments(
                node,
                [list(signature.parameters)],
                callableKind="Method",
                callableName=methodName,
                receiverType=targetType,
            )
            return

        if isinstance(targetType, PrimitiveType) and targetType.value == Type.FILE:
            signature = self.fileMethodSignature(methodName)
            if signature is None:
                for argument in node.arguments:
                    self.visit(self.callArgumentValue(argument))
                self.report(callee.member, f"File has no method named '{methodName}'.")
                return
            self.checkCallableArguments(
                node,
                [list(signature.parameters)],
                callableKind="Method",
                callableName=methodName,
                receiverType=targetType,
            )
            return

        if isinstance(targetType, NamedType):
            declaration = self.structDeclaration(targetType)
            if declaration is not None and structBuiltinName in ("copy", "resembles"):
                parameters = (
                    []
                    if structBuiltinName == "copy"
                    else [ParameterSignature(
                        "ᚢᚦᚢ" if methodName == "ᚱᛁᛋᛖᛗᛒᚢᛚ" else "other",
                        targetType,
                        False
                    )]
                )
                self.checkCallableArguments(
                    node,
                    [parameters],
                    callableKind="Method",
                    callableName=methodName,
                    receiverType=targetType,
                )
                return

        if self.isCollectionType(targetType):
            collectionMethods = self.collectionMethodSignatures(
                targetType,
                methodName
            )

            if collectionMethods is None:
                for argument in node.arguments:
                    self.visit(argument)

                if isinstance(targetType, UnionType):
                    self.report(
                        callee.member,
                        (
                            f"Collection method '{methodName}' is "
                            f"not available on every type in union "
                            f"'{self.typeText(targetType)}'."
                        )
                    )
                else:
                    self.report(
                        callee.member,
                        (
                            f"Collection type "
                            f"'{self.typeText(targetType)}' has no "
                            f"method named '{methodName}'."
                        )
                    )

                return

            self.checkCallableArguments(
                node,
                [
                    list(method.parameters)
                    for method in collectionMethods
                ],
                callableKind="Method",
                callableName=methodName,
                receiverType=targetType
            )
            return

        methods = self.memberMethods(
            targetType,
            methodName
        )

        if methods is None:
            for argument in node.arguments:
                self.visit(argument)

            if self.memberFields(
                targetType,
                methodName
            ) is not None:
                self.report(
                    callee.member,
                    f"Struct field '{methodName}' is not callable."
                )
                return

            if isinstance(targetType, NamedType):
                declaration = self.structDeclaration(
                    targetType
                )
                staticMethod = (
                    self.structMethod(
                        declaration,
                        methodName,
                        instanceMethod=False
                    )
                    if declaration is not None
                    else None
                )

                if staticMethod is not None:
                    self.report(
                        callee.member,
                        (
                            f"Static method "
                            f"'{declaration.name.name}.{methodName}' "
                            f"must be called through struct type "
                            f"'{declaration.name.name}'."
                        )
                    )
                    return

                if declaration is not None:
                    self.report(
                        callee.member,
                        (
                            f"Struct '{declaration.name.name}' has "
                            f"no instance method named "
                            f"'{methodName}'."
                        )
                    )
                    return

            if isinstance(targetType, UnionType):
                self.report(
                    callee.member,
                    (
                        f"Instance method '{methodName}' is not "
                        f"available on every type in union "
                        f"'{self.typeText(targetType)}'."
                    )
                )
                return

            self.report(
                callee.member,
                (
                    f"Cannot call method '{methodName}' on a "
                    f"value of type '{self.typeText(targetType)}'."
                )
            )
            return

        self.checkMethodCallArguments(
            node,
            methods,
            instanceMethod=True,
            receiverType=targetType
        )


    def visitFunctionCall(self, node: FunctionCall):
        if isinstance(node.callee, MemberAccess):
            self.visitStructMethodCall(node)
            return

        self.visit(node.callee)

        symbol = (
            self.currentScope.resolve(node.callee.name)
            if isinstance(node.callee, Identifier)
            else None
        )

        if not isinstance(node.callee, Identifier):
            for argument in node.arguments:
                self.visit(self.callArgumentValue(argument))
            return

        if symbol is None:
            # visitIdentifier() already reported the unknown name.
            for argument in node.arguments:
                self.visit(self.callArgumentValue(argument))
            return

        if isinstance(symbol, BuiltinFunctionSymbol):
            self.checkCallableArguments(
                node,
                [self.builtinParameterSignatures(symbol)],
                callableKind="Builtin",
                callableName=symbol.name
            )
            mutatingTypes = {
                "to_int": PrimitiveType(Type.INT),
                "ᛏᚣ_ᛁᚾᛏ": PrimitiveType(Type.INT),
                "to_char": PrimitiveType(Type.CHAR),
                "ᛏᚣ_ᚳᚻᚪᚱ": PrimitiveType(Type.CHAR),
                "to_str": PrimitiveType(Type.STR),
                "ᛏᚣ_ᛋᛏᚱ": PrimitiveType(Type.STR),
                "to_float": PrimitiveType(Type.FLOAT),
                "ᛏᚣ_ᚠᛚᚩᛏ": PrimitiveType(Type.FLOAT),
                "to_bool": PrimitiveType(Type.BOOL),
                "ᛏᚣ_ᛒᚣᛚ": PrimitiveType(Type.BOOL),
                "to_list": ListType(PrimitiveType(Type.ANY)),
                "ᛏᚣ_ᛚᛁᛋᛏ": ListType(PrimitiveType(Type.ANY)),
                "to_arr": ArrayType(PrimitiveType(Type.ANY), 0),
                "ᛏᚣ_ᚪᚱ": ArrayType(PrimitiveType(Type.ANY), 0),
            }
            narrowedType = mutatingTypes.get(symbol.name)
            if narrowedType is not None and node.arguments:
                target = self.callArgumentValue(node.arguments[0])
                if isinstance(target, Identifier):
                    targetSymbol = self.currentScope.resolve(target.name)
                    if isinstance(targetSymbol, VariableSymbol):
                        targetSymbol.declaredType = narrowedType
                        targetSymbol.initialized = True
            return

        if not isinstance(symbol, FunctionSymbol):
            if (
                isinstance(symbol, VariableSymbol)
                and isinstance(symbol.declaredType, PrimitiveType)
                and symbol.declaredType.value == Type.PYOBJECT
            ):
                for argument in node.arguments:
                    self.visit(self.callArgumentValue(argument))
                return
            for argument in node.arguments:
                self.visit(self.callArgumentValue(argument))
            self.report(
                node.callee,
                f"'{node.callee.name}' is not callable."
            )
            return

        self.checkCallableArguments(
            node,
            [self.parameterSignatures(
                symbol.declaration.parameters
            )],
            callableKind="Function",
            callableName=symbol.name
        )

    def visitNamedArgument(self, node: NamedArgument):
        self.visit(node.value)


    def visitMemberAccess(self, node: MemberAccess):
        typeOwner, ambiguous = self.qualifiedTypeMemberTarget(
            node.target,
            node.member.name,
            forCall=False
        )

        if ambiguous:
            self.reportQualifiedMemberAmbiguity(node)
            return

        if isinstance(typeOwner, EnumDeclaration):
            if self.enumMember(
                typeOwner,
                node.member.name
            ) is not None:
                return

            self.report(
                node.member,
                (
                    f"Enum '{typeOwner.name.name}' has no member "
                    f"named '{node.member.name}'."
                )
            )
            return

        staticOwner = (
            typeOwner
            if isinstance(typeOwner, StructDeclaration)
            else None
        )

        if staticOwner is not None:
            method = self.structMethod(
                staticOwner,
                node.member.name,
                instanceMethod=False
            )

            if method is not None:
                self.report(
                    node.member,
                    (
                        f"Static method "
                        f"'{staticOwner.name.name}."
                        f"{node.member.name}' must be called."
                    )
                )
                return

            self.report(
                node.member,
                (
                    f"Struct '{staticOwner.name.name}' has no "
                    f"static method named '{node.member.name}'."
                )
            )
            return

        self.visit(node.target)

        targetType = self.inferExpressionType(
            node.target
        )

        if targetType is None:
            return

        if isinstance(targetType, ModuleType):
            symbol = self.moduleValueSymbol(
                targetType,
                node.member.name
            )
            if isinstance(symbol, FunctionSymbol):
                self.report(
                    node.member,
                    f"Function '{targetType.moduleName}.{node.member.name}' must be called."
                )
            elif symbol is None:
                if targetType.record.typeSymbol(node.member.name) is not None:
                    self.report(
                        node.member,
                        f"Import type '{node.member.name}' with 'from {targetType.moduleName} import {node.member.name}' before using it."
                    )
                else:
                    self.report(
                        node.member,
                        f"Module '{targetType.moduleName}' has no exported name '{node.member.name}'."
                    )
            return

        if (
            isinstance(targetType, PrimitiveType)
            and targetType.value == Type.PYOBJECT
        ):
            return

        collectionMethods = self.collectionMethodSignatures(
            targetType,
            node.member.name
        )

        if collectionMethods is not None:
            self.report(
                node.member,
                (
                    f"Collection method '{node.member.name}' must "
                    f"be called."
                )
            )
            return

        if self.isCollectionType(targetType):
            if isinstance(targetType, UnionType):
                message = (
                    f"Collection member '{node.member.name}' is not "
                    f"available on every type in union "
                    f"'{self.typeText(targetType)}'."
                )
            else:
                message = (
                    f"Collection type '{self.typeText(targetType)}' "
                    f"has no method named '{node.member.name}'."
                )

            self.report(node.member, message)
            return

        if self.memberFields(
            targetType,
            node.member.name
        ) is not None:
            return

        if self.memberMethods(
            targetType,
            node.member.name
        ) is not None:
            self.report(
                node.member,
                (
                    f"Instance method '{node.member.name}' must "
                    f"be called."
                )
            )
            return

        # Do not visit node.member as a lexical identifier. It is
        # resolved against the target struct rather than local scope.
        self.reportInvalidMemberAccess(
            node,
            targetType
        )


    def visitIndexAccess(self, node: IndexAccess):
        self.visit(node.target)
        self.visit(node.index)

        targetType = self.inferExpressionType(
            node.target
        )

        if (
            isinstance(targetType, PrimitiveType)
            and targetType.value == Type.PYOBJECT
        ):
            return

        dictionaries = (
            self.dictTypes(targetType)
            if targetType is not None
            else None
        )
        if dictionaries is not None:
            keyTypes = [dictionary.keyType for dictionary in dictionaries]
            compatible, indexType = self.expressionAssignableToAll(
                node.index,
                keyTypes
            )
            if compatible is False:
                actual = (
                    self.typeText(indexType)
                    if indexType is not None
                    else "<unknown>"
                )
                expected = self.typeText(self.uniqueUnion(keyTypes))
                self.report(
                    node.index,
                    f"Dictionary key must have type '{expected}', got '{actual}'."
                )
            if (
                indexType is not None
                and not self.isHashableDictKeyType(indexType)
            ):
                self.report(
                    node.index,
                    f"Dictionary key value has unhashable type "
                    f"'{self.typeText(indexType)}'."
                )
            return

        indexType = self.inferExpressionType(
            node.index
        )

        if (
            indexType is not None
            and not self.sameType(
                indexType,
                PrimitiveType(Type.INT)
            )
        ):
            self.report(
                node.index,
                (
                    f"Collection index must have type 'int', "
                    f"got '{self.typeText(indexType)}'."
                )
            )

        if (
            targetType is not None
            and not self.isCollectionType(targetType)
        ):
            self.report(
                node.target,
                (
                    f"Cannot index a value of type "
                    f"'{self.typeText(targetType)}'."
                )
            )

        if (
            isinstance(targetType, ArrayType)
            and targetType.isHeterogeneous
            and self.constantInteger(node.index) is not None
            and self.arrayIndexedType(targetType, node.index) is None
        ):
            self.report(
                node.index,
                (
                    f"Heterogeneous array index is outside its "
                    f"{targetType.capacity}-slot schema."
                )
            )


    def visitSliceAccess(self, node: SliceAccess):
        self.visit(node.target)
        self.visit(node.start)
        self.visit(node.end)

        if node.start is not None:
            self.requireExpressionType(
                node.start,
                PrimitiveType(Type.INT),
                "Slice start"
            )

        if node.end is not None:
            self.requireExpressionType(
                node.end,
                PrimitiveType(Type.INT),
                "Slice end"
            )

        targetType = self.inferExpressionType(
            node.target
        )

        if (
            isinstance(targetType, PrimitiveType)
            and targetType.value == Type.PYOBJECT
        ):
            return

        if targetType is not None and self.dictTypes(targetType) is not None:
            self.report(
                node.target,
                "Dictionary values cannot be sliced."
            )
            return

        if (
            targetType is not None
            and not self.isCollectionType(targetType)
        ):
            self.report(
                node.target,
                (
                    f"Cannot slice a value of type "
                    f"'{self.typeText(targetType)}'."
                )
            )

        if (
            isinstance(targetType, ArrayType)
            and targetType.isHeterogeneous
            and self.heterogeneousSliceType(
                targetType,
                node.start,
                node.end
            ) is None
        ):
            self.report(
                node,
                "Heterogeneous array slice bounds must be constant "
                "non-negative integers."
            )

    def visitLiteral(self, node: Literal):
        if node.litType != Type.CHAR:
            return

        try:
            value = literal_eval(node.litValue)
        except (ValueError, SyntaxError):
            value = None

        if self.constantValueMatchesType(
            PrimitiveType(Type.CHAR),
            value
        ):
            return

        self.invalidLiteralValues[id(node)] = value

        if id(node) in self.invalidLiteralDiagnostics:
            return

        self.report(
            node,
            (
                "Character literal must decode to exactly one "
                "character."
            )
        )
        self.invalidLiteralDiagnostics.add(id(node))


    def visitUninitialized(
        self,
        node: Uninitialized
    ):
        pass


    def visitCompositeString(
        self,
        node: CompositeString
    ):
        for component in node.components:
            self.visit(component)


    def visitstringComponent(
        self,
        node: stringComponent
    ):
        # Every Thorn value may be interpolated. The runtime will
        # stringify evaluation results implicitly, so semantic
        # analysis only validates the embedded evaluation itself.
        self.visit(node.value)


    def structDeclaration(
        self,
        name: str | NamedType
    ) -> StructDeclaration | None:
        if isinstance(name, NamedType):
            if isinstance(name.resolvedDeclaration, StructDeclaration):
                return name.resolvedDeclaration
            name = name.name.name
        symbol = self.currentScope.resolveType(name)

        if (
            symbol is not None
            and isinstance(
                symbol.declaration,
                StructDeclaration
            )
        ):
            return symbol.declaration

        return None

    def enumDeclaration(
        self,
        name: str
    ) -> EnumDeclaration | None:
        symbol = self.currentScope.resolveType(name)

        if (
            symbol is not None
            and isinstance(
                symbol.declaration,
                EnumDeclaration
            )
        ):
            return symbol.declaration

        return None

    def enumMember(
        self,
        declaration: EnumDeclaration,
        name: str
    ) -> EnumMemberDeclaration | None:
        for member in declaration.members:
            if member.name.name == name:
                return member

        return None

    def valueExposesMember(
        self,
        target: Node,
        memberName: str,
        forCall: bool
    ) -> bool:
        if not isinstance(target, Identifier):
            return False

        symbol = self.currentScope.resolve(target.name)

        if not isinstance(symbol, VariableSymbol):
            return False

        if self.collectionMethodSignatures(
            symbol.declaredType,
            memberName
        ) is not None:
            return True

        if self.memberMethods(
            symbol.declaredType,
            memberName
        ) is not None:
            return True

        return (
            not forCall
            and self.memberFields(
                symbol.declaredType,
                memberName
            ) is not None
        )

    def qualifiedTypeMemberTarget(
        self,
        target: Node,
        memberName: str,
        forCall: bool
    ) -> tuple[NamedTypeDeclaration | None, bool]:
        if not isinstance(target, Identifier):
            return None, False

        typeSymbol = self.currentScope.resolveType(target.name)
        declaration = (
            typeSymbol.declaration
            if typeSymbol is not None
            else None
        )

        if not isinstance(
            declaration,
            (EnumDeclaration, StructDeclaration)
        ):
            return None, False

        if isinstance(declaration, EnumDeclaration):
            typeExposesMember = (
                not forCall
                and self.enumMember(
                    declaration,
                    memberName
                ) is not None
            )
        else:
            typeExposesMember = self.structMethod(
                declaration,
                memberName,
                instanceMethod=False
            ) is not None

        valueExposesMember = self.valueExposesMember(
            target,
            memberName,
            forCall
        )

        if typeExposesMember and valueExposesMember:
            return declaration, True

        if typeExposesMember:
            return declaration, False

        if valueExposesMember:
            return None, False

        # Preserve type-specific diagnostics when neither namespace can
        # actually provide the requested member.
        return declaration, False

    def reportQualifiedMemberAmbiguity(
        self,
        node: MemberAccess
    ):
        diagnosticKey = id(node)

        if diagnosticKey in self.qualifiedMemberDiagnostics:
            return

        targetName = (
            node.target.name
            if isinstance(node.target, Identifier)
            else self.typeText(
                self.inferExpressionType(node.target)
            )
        )
        self.report(
            node,
            (
                f"Qualified member '{targetName}."
                f"{node.member.name}' is ambiguous between the "
                f"type and value namespaces."
            )
        )
        self.qualifiedMemberDiagnostics.add(diagnosticKey)

    def structField(
        self,
        declaration: StructDeclaration,
        name: str
    ) -> StructFieldDeclaration | None:
        for field in declaration.fields:
            if field.name.name == name:
                return field

        return None

    def isInstanceStructMethod(
        self,
        owner: StructDeclaration,
        method: FunctionDeclaration
    ) -> bool:
        if not method.parameters:
            return False

        receiver = method.parameters[0]

        return (
            receiver.name.name == "self"
            and self.sameType(
                receiver.paramType,
                NamedType(owner.name)
            )
        )

    def structMethod(
        self,
        declaration: StructDeclaration,
        name: str,
        instanceMethod: bool
    ) -> FunctionDeclaration | None:
        for method in declaration.methods:
            if (
                method.name.name == name
                and self.isInstanceStructMethod(
                    declaration,
                    method
                ) == instanceMethod
            ):
                return method

        return None

    def memberMethods(
        self,
        targetType: TypeNode,
        memberName: str
    ) -> list[tuple[StructDeclaration, FunctionDeclaration]] | None:
        if isinstance(targetType, NamedType):
            declaration = self.structDeclaration(
                targetType
            )

            if declaration is None:
                return None

            method = self.structMethod(
                declaration,
                memberName,
                instanceMethod=True
            )

            if method is None:
                return None

            return [(declaration, method)]

        if isinstance(targetType, UnionType):
            methods = []

            # Just like field access, an instance method is safe on a
            # union only when every possible receiver exposes it.
            for member in targetType.members:
                memberMethods = self.memberMethods(
                    member,
                    memberName
                )

                if memberMethods is None:
                    return None

                methods.extend(memberMethods)

            return methods

        return None

    def memberFields(
        self,
        targetType: TypeNode,
        memberName: str
    ) -> list[StructFieldDeclaration] | None:
        if isinstance(targetType, NamedType):
            declaration = self.structDeclaration(
                targetType
            )

            if declaration is None:
                return None

            field = self.structField(
                declaration,
                memberName
            )

            return [field] if field is not None else None

        if isinstance(targetType, UnionType):
            fields = []

            # A member is safe on a union only when every possible
            # runtime struct exposes it.
            for member in targetType.members:
                memberFields = self.memberFields(
                    member,
                    memberName
                )

                if memberFields is None:
                    return None

                fields.extend(memberFields)

            return fields

        return None

    def memberType(
        self,
        targetType: TypeNode,
        memberName: str
    ) -> TypeNode | None:
        fields = self.memberFields(
            targetType,
            memberName
        )

        if fields is None:
            return None

        return self.uniqueUnion([
            field.fieldType
            for field in fields
        ])

    def reportInvalidMemberAccess(
        self,
        node: MemberAccess,
        targetType: TypeNode
    ):
        memberName = node.member.name

        if isinstance(targetType, NamedType):
            typeName = targetType.name.name
            declaration = self.structDeclaration(targetType)

            if declaration is None:
                self.report(
                    node.member,
                    (
                        f"Type '{typeName}' does not expose "
                        f"struct fields."
                    )
                )
                return

            self.report(
                node.member,
                (
                    f"Struct '{typeName}' has no field "
                    f"named '{memberName}'."
                )
            )
            return

        if isinstance(targetType, UnionType):
            for member in targetType.members:
                if self.memberFields(
                    member,
                    memberName
                ) is None:
                    self.report(
                        node.member,
                        (
                            f"Member '{memberName}' is not "
                            f"available on every type in union "
                            f"'{self.typeText(targetType)}'."
                        )
                    )
                    return

        self.report(
            node.member,
            (
                f"Cannot access member '{memberName}' on "
                f"a value of type "
                f"'{self.typeText(targetType)}'."
            )
        )

    def validateStructLiteral(
        self,
        literal: StructLiteral,
        declaration: StructDeclaration
    ) -> bool:
        key = (id(literal), declaration.name.name)

        if key in self.structLiteralResults:
            return self.structLiteralResults[key]

        valid = True
        declaredFields: dict[
            str,
            StructFieldDeclaration
        ] = {}

        # Duplicate declarations are diagnosed by the declaration
        # visitor. The first field remains canonical for literals.
        for field in declaration.fields:
            declaredFields.setdefault(
                field.name.name,
                field
            )

        initializedFields: dict[
            str,
            StructFieldInitializer
        ] = {}

        for initializer in literal.fields:
            name = initializer.name.name
            field = declaredFields.get(name)

            # Field declarations supply the nominal context for nested
            # anonymous struct literals and collection elements.
            self.visit(
                initializer.value,
                expectedType=(
                    field.fieldType
                    if field is not None
                    else None
                )
            )

            if name in initializedFields:
                self.report(
                    initializer.name,
                    (
                        f"Field '{name}' is initialized more "
                        f"than once in struct literal "
                        f"'{declaration.name.name}'."
                    )
                )
                valid = False
                continue

            initializedFields[name] = initializer

            if field is None:
                self.report(
                    initializer.name,
                    (
                        f"Struct '{declaration.name.name}' has "
                        f"no field named '{name}'."
                    )
                )
                valid = False
                continue

            compatible = self.isExpressionAssignable(
                initializer.value,
                field.fieldType
            )

            if compatible is True:
                continue

            valid = False

            # None means a nested expression already produced a
            # more specific diagnostic or could not be inferred.
            if compatible is None:
                continue

            valueType = self.inferExpressionType(
                initializer.value
            )
            valueText = (
                self.typeText(valueType)
                if valueType is not None
                else "<unknown>"
            )

            self.report(
                initializer.value,
                (
                    f"Field '{name}' of struct "
                    f"'{declaration.name.name}' must have type "
                    f"'{self.typeText(field.fieldType)}', got "
                    f"'{valueText}'."
                )
            )

        for name, field in declaredFields.items():
            if (
                name not in initializedFields
                and isinstance(
                    field.defaultValue,
                    Uninitialized
                )
            ):
                self.report(
                    literal,
                    (
                        f"Missing required field '{name}' for "
                        f"struct '{declaration.name.name}'."
                    )
                )
                valid = False

        self.structLiteralResults[key] = valid
        return valid

    def structLiteralCandidates(
        self,
        expectedType: TypeNode | None
    ) -> list[StructDeclaration]:
        if expectedType is None:
            return []

        members = (
            expectedType.members
            if isinstance(expectedType, UnionType)
            else [expectedType]
        )
        candidates: list[StructDeclaration] = []

        for member in members:
            if not isinstance(member, NamedType):
                continue

            declaration = self.structDeclaration(
                member
            )

            if (
                declaration is not None
                and all(
                    declaration is not candidate
                    for candidate in candidates
                )
            ):
                candidates.append(declaration)

        return candidates

    def reportAmbiguousStructLiteral(
        self,
        literal: StructLiteral
    ):
        cacheKey = (id(literal), "<ambiguous>")

        if cacheKey in self.structLiteralResults:
            return

        self.report(
            literal,
            (
                "Anonymous struct literal is ambiguous; "
                "use an explicit struct name."
            )
        )
        self.structLiteralResults[cacheKey] = False

    def reportUnresolvedStructLiteral(
        self,
        literal: StructLiteral
    ):
        cacheKey = (id(literal), "<unresolved>")

        if cacheKey in self.structLiteralResults:
            return

        self.report(
            literal,
            (
                "Cannot infer the type of this anonymous struct "
                "literal; use an explicit struct name."
            )
        )
        self.structLiteralResults[cacheKey] = False

    def visitUnresolvedStructLiteralFields(
        self,
        literal: StructLiteral
    ):
        # Continue validating child expressions after the literal's
        # missing context has been diagnosed.
        for initializer in literal.fields:
            self.visit(initializer.value)

    def isStructLiteralAssignable(
        self,
        literal: StructLiteral,
        destinationType: TypeNode
    ) -> bool | None:
        if literal.typeName is not None:
            sourceType = NamedType(literal.typeName)

            if not self.isAssignable(
                sourceType,
                destinationType
            ):
                return False

            declaration = self.structDeclaration(
                literal.typeName.name
            )

            if declaration is None:
                return None

            return (
                True
                if self.validateStructLiteral(
                    literal,
                    declaration
                )
                else None
            )

        if isinstance(destinationType, NamedType):
            declaration = self.structDeclaration(
                destinationType
            )

            if declaration is None:
                return None

            return (
                True
                if self.validateStructLiteral(
                    literal,
                    declaration
                )
                else None
            )

        if isinstance(destinationType, UnionType):
            candidates = self.structLiteralCandidates(
                destinationType
            )

            if len(candidates) == 1:
                return (
                    True
                    if self.validateStructLiteral(
                        literal,
                        candidates[0]
                    )
                    else None
                )

            if len(candidates) > 1:
                self.reportAmbiguousStructLiteral(literal)
                return None

        # Anonymous struct literals are contextual expressions. A
        # non-struct destination cannot give them nominal identity.
        self.reportUnresolvedStructLiteral(literal)
        return None

    def visitStructLiteral(self, node: StructLiteral):
        if node.typeName is None:
            candidates = self.structLiteralCandidates(
                self.currentExpectedType
            )

            if len(candidates) == 1:
                self.validateStructLiteral(
                    node,
                    candidates[0]
                )
                return

            if len(candidates) > 1:
                self.reportAmbiguousStructLiteral(node)
            else:
                self.reportUnresolvedStructLiteral(node)

            self.visitUnresolvedStructLiteralFields(node)
            return

        name = node.typeName.name
        symbol = self.currentScope.resolveType(name)

        if symbol is None:
            self.report(
                node.typeName,
                f"Unknown struct type '{name}'."
            )
            self.visitUnresolvedStructLiteralFields(node)
            return

        if not isinstance(
            symbol.declaration,
            StructDeclaration
        ):
            self.report(
                node.typeName,
                f"Type '{name}' is not a struct."
            )
            self.visitUnresolvedStructLiteralFields(node)
            return

        self.validateStructLiteral(
            node,
            symbol.declaration
        )

    def visitStructFieldInitializer(
        self,
        node: StructFieldInitializer
    ):
        self.visit(
            node.value,
            expectedType=self.currentExpectedType
        )

    def collectionLiteralElementType(
        self,
        literal: ListLiteral | ArrayLiteral | SetLiteral,
        expectedType: TypeNode | None
    ) -> TypeNode | None:
        if expectedType is None:
            return None

        members = (
            expectedType.members
            if isinstance(expectedType, UnionType)
            else [expectedType]
        )
        elementTypes: list[TypeNode] = []

        for member in members:
            matches = (
                isinstance(literal, ListLiteral)
                and isinstance(member, ListType)
            ) or (
                isinstance(literal, ArrayLiteral)
                and isinstance(member, ArrayType)
            ) or (
                isinstance(literal, SetLiteral)
                and isinstance(member, SetType)
            )

            if matches:
                elementTypes.append(
                    self.collectionElementType(member)
                    if isinstance(member, ArrayType)
                    else member.elementType
                )

        if not elementTypes:
            return None

        return self.uniqueUnion(elementTypes)


    def visitListLiteral(self, node: ListLiteral):
        elementType = self.collectionLiteralElementType(
            node,
            self.currentExpectedType
        )

        for element in node.elements:
            self.visit(element, expectedType=elementType)


    def visitArrayLiteral(self, node: ArrayLiteral):
        expectedMembers = (
            self.currentExpectedType.members
            if isinstance(self.currentExpectedType, UnionType)
            else [self.currentExpectedType]
        )
        expectedArrays = [
            member
            for member in expectedMembers
            if isinstance(member, ArrayType)
        ]

        for index, element in enumerate(node.elements):
            positionalTypes: list[TypeNode] = []
            for arrayType in expectedArrays:
                if arrayType.isHeterogeneous:
                    slots = arrayType.slotTypes or []
                    if index < len(slots):
                        positionalTypes.append(slots[index])
                else:
                    positionalTypes.append(arrayType.elementType)
            expectedType = (
                self.uniqueUnion(positionalTypes)
                if positionalTypes
                else None
            )
            self.visit(element, expectedType=expectedType)


    def visitSetLiteral(self, node: SetLiteral):
        elementType = self.collectionLiteralElementType(
            node,
            self.currentExpectedType
        )

        for element in node.elements:
            self.visit(element, expectedType=elementType)

    def expectedDictTypes(
        self,
        expectedType: TypeNode | None
    ) -> list[DictType]:
        if expectedType is None:
            return []
        members = (
            expectedType.members
            if isinstance(expectedType, UnionType)
            else [expectedType]
        )
        return [member for member in members if isinstance(member, DictType)]

    def visitDictLiteral(self, node: DictLiteral):
        dictionaries = self.expectedDictTypes(self.currentExpectedType)
        keyType = (
            self.uniqueUnion([dictionary.keyType for dictionary in dictionaries])
            if dictionaries
            else None
        )
        valueType = (
            self.uniqueUnion([dictionary.valueType for dictionary in dictionaries])
            if dictionaries
            else None
        )
        for entry in node.entries:
            self.visit(entry.key, expectedType=keyType)
            self.visit(entry.value, expectedType=valueType)
            actualKeyType = self.inferExpressionType(entry.key)
            if (
                actualKeyType is not None
                and not self.isHashableDictKeyType(actualKeyType)
            ):
                self.report(
                    entry.key,
                    f"Dictionary key value has unhashable type "
                    f"'{self.typeText(actualKeyType)}'."
                )

    def visitDictEntry(self, node: DictEntry):
        self.visit(node.key)
        self.visit(node.value)

    def visitCollectionConversion(self, node: CollectionConversion):
        if isinstance(node.elementType, NamedType):
            name = node.elementType.name.name
            typeSymbol = self.currentScope.resolveType(name)
            valueSymbol = self.currentScope.resolve(name)
            if typeSymbol is None and isinstance(valueSymbol, VariableSymbol):
                self.report(
                    node.elementType.name,
                    (
                        f"Conversion '{node.collectionKind}' requires an "
                        f"element type as its first argument; '{name}' names "
                        f"a value. Write {node.collectionKind}(T, {name}), "
                        f"where T is the desired element type."
                    ),
                )
            else:
                self.visit(node.elementType)
        else:
            self.visit(node.elementType)
        anyType = PrimitiveType(Type.ANY)
        parameters = [ParameterSignature("value", anyType, True)]
        if node.collectionKind == "arr":
            parameters.append(ParameterSignature(
                "capacity",
                PrimitiveType(Type.INT),
                True
            ))
        self.checkCallableArguments(
            node,
            [parameters],
            callableKind="Conversion",
            callableName=node.collectionKind,
        )

    def visitDictConversion(self, node: DictConversion):
        self.visit(node.keyType)
        self.visit(node.valueType)
        self.validateDictKeyType(node.keyType)
        self.checkCallableArguments(
            node,
            [[ParameterSignature("value", PrimitiveType(Type.ANY), True)]],
            callableKind="Conversion",
            callableName="dict",
        )

    def visitIfStatement(
        self,
        node: IfStatement
    ):
        self.visit(node.condition)
        self.requireExpressionType(
            node.condition,
            PrimitiveType(Type.BOOL),
            "If condition"
        )

        baseline = self.activeVariableStates()
        pathStates = []

        self.visit(node.thenBranch)
        if not self.blockDefinitelyReturns(
            node.thenBranch
        ):
            pathStates.append(
                self.activeVariableStates()
            )
        self.restoreVariableStates(baseline)

        for branch in node.elsifBranches:
            self.visit(branch.condition)
            self.requireExpressionType(
                branch.condition,
                PrimitiveType(Type.BOOL),
                "Elsif condition"
            )
            self.visit(branch.body)
            if not self.blockDefinitelyReturns(
                branch.body
            ):
                pathStates.append(
                    self.activeVariableStates()
                )
            self.restoreVariableStates(baseline)

        if node.elseBranch is not None:
            self.visit(node.elseBranch)
            if not self.blockDefinitelyReturns(
                node.elseBranch
            ):
                pathStates.append(
                    self.activeVariableStates()
                )
            self.restoreVariableStates(baseline)
        else:
            # The entire conditional can be skipped.
            pathStates.append(baseline)

        if pathStates:
            self.mergeVariableStates(pathStates)


    def visitElseIfBranch(
        self,
        node: ElseIfBranch
    ):
        self.visit(node.condition)
        self.requireExpressionType(
            node.condition,
            PrimitiveType(Type.BOOL),
            "Elsif condition"
        )
        self.visit(node.body)


    def visitWhileStatement(
        self,
        node: WhileStatement
    ):
        self.visit(node.condition)
        self.requireExpressionType(
            node.condition,
            PrimitiveType(Type.BOOL),
            "While condition"
        )

        baseline = self.activeVariableStates()
        with self.loopContext():
            self.visit(node.body)
        # A while body may execute zero times. Its declarations stay
        # visible in the function, but its writes are not definite.
        self.restoreVariableStates(baseline)


    def visitUntilStatement(
        self,
        node: UntilStatement
    ):
        # Thorn checks an until condition after executing its body.
        with self.loopContext():
            self.visit(node.body)
        self.visit(node.condition)
        self.requireExpressionType(
            node.condition,
            PrimitiveType(Type.BOOL),
            "Until condition"
        )


    def visitForStatement(
        self,
        node: ForStatement
    ):
        self.visit(node.start)
        self.requireExpressionType(
            node.start,
            PrimitiveType(Type.INT),
            "For-loop start"
        )
        self.visit(node.end)
        self.requireExpressionType(
            node.end,
            PrimitiveType(Type.INT),
            "For-loop end"
        )

        baseline = self.activeVariableStates()
        iterator = VariableSymbol(
            name=node.iterator.name,
            declaredType=PrimitiveType(Type.INT),
            isConst=False,
            initialized=True,
            declaration=node.iterator
        )

        with self.temporarySymbol(iterator):
            with self.loopContext():
                self.visit(node.body)

        # A for body may execute zero times.
        self.restoreVariableStates(baseline)


    def visitForeachStatement(
        self,
        node: ForeachStatement
    ):
        self.visit(node.collection)

        collectionType = self.inferExpressionType(
            node.collection
        )

        if (
            collectionType is not None
            and self.isCollectionType(collectionType)
        ):
            iteratorType = self.collectionElementType(
                collectionType
            )
        elif (
            isinstance(collectionType, PrimitiveType)
            and collectionType.value == Type.PYOBJECT
        ):
            iteratorType = PrimitiveType(Type.PYOBJECT)
        else:
            iteratorType = None

            if collectionType is not None:
                self.report(
                    node.collection,
                    (
                        f"Foreach requires a collection, got "
                        f"'{self.typeText(collectionType)}'."
                    )
                )

        baseline = self.activeVariableStates()
        iterator = VariableSymbol(
            name=node.iterator.name,
            declaredType=iteratorType,
            isConst=False,
            initialized=True,
            declaration=node.iterator
        )

        with self.temporarySymbol(iterator):
            with self.loopContext():
                self.visit(node.body)

        # A foreach body may execute zero times.
        self.restoreVariableStates(baseline)


    def visitBreakStatement(self, node: BreakStatement):
        if self.loopDepth == 0:
            self.report(
                node,
                "Break statement cannot appear outside a loop."
            )


    def visitContinueStatement(self, node: ContinueStatement):
        if self.loopDepth == 0:
            self.report(
                node,
                "Continue statement cannot appear outside a loop."
            )


    def blockDefinitelyReturns(
        self,
        block: Block
    ) -> bool:
        return any(
            self.statementDefinitelyReturns(statement)
            for statement in block.statements
        )

    def statementDefinitelyReturns(
        self,
        statement: Node
    ) -> bool:
        if isinstance(statement, ReturnStatement):
            return True

        if isinstance(statement, IfStatement):
            if statement.elseBranch is None:
                return False

            return (
                self.blockDefinitelyReturns(
                    statement.thenBranch
                )
                and all(
                    self.blockDefinitelyReturns(branch.body)
                    for branch in statement.elsifBranches
                )
                and self.blockDefinitelyReturns(
                    statement.elseBranch
                )
            )

        # An until body executes at least once because its
        # condition is checked after the body.
        if isinstance(statement, UntilStatement):
            return self.blockDefinitelyReturns(
                statement.body
            )

        return False


    def visitReturnStatement(
        self,
        node: ReturnStatement
    ):
        if self.currentFunction is None:
            self.visit(node.value)
            self.report(
                node,
                "Return statement cannot appear outside a function."
            )
            return

        returnType = self.currentFunction.returnType
        callableName = self.callableDisplayName(
            self.currentFunction,
            self.currentMethodOwner
        )
        callableKind = (
            "method"
            if self.currentMethodOwner is not None
            else "function"
        )
        callableKindTitle = callableKind.title()

        if self.isPrimitive(returnType, Type.NIL):
            if node.value is not None:
                self.visit(node.value)
                self.report(
                    node.value,
                    (
                        f"Nil {callableKind} '{callableName}' cannot "
                        f"return a value."
                    )
                )

            return

        if node.value is None:
            self.report(
                node,
                (
                    f"{callableKindTitle} '{callableName}' must return "
                    f"a value of type "
                    f"'{self.typeText(returnType)}'."
                )
            )
            return

        self.visit(
            node.value,
            expectedType=returnType
        )

        compatible = self.isExpressionAssignable(
            node.value,
            returnType
        )

        if compatible is None or compatible:
            return

        valueType = self.inferExpressionType(
            node.value
        )
        valueText = (
            self.typeText(valueType)
            if valueType is not None
            else "<unknown>"
        )

        self.report(
            node.value,
            (
                f"{callableKindTitle} '{callableName}' must return "
                f"a value of type "
                f"'{self.typeText(returnType)}', got "
                f"'{valueText}'."
            )
        )

    def visitPrimitiveType(
        self,
        node: PrimitiveType
    ):
        pass

    def visitModuleType(self, node: ModuleType):
        pass


    def visitNamedType(self, node: NamedType):
        name = node.name.name
        symbol = self.currentScope.resolveType(name)

        if symbol is None:
            self.report(
                node.name,
                f"Unknown type '{name}'."
            )
            return

        node.resolvedDeclaration = symbol.declaration


    def visitNamedTypeDeclaration(
        self,
        node: NamedTypeDeclaration
    ):
        # Registration happens in predeclareTypes(). Concrete type
        # declarations will override this visitor to analyze fields,
        # members, enum values, and similar declaration contents.
        pass

    def visitEnumDeclaration(
        self,
        node: EnumDeclaration
    ):
        self.validateEnumDeclaration(node)

    def visitEnumMemberDeclaration(
        self,
        node: EnumMemberDeclaration
    ):
        # Enum members are validated together so implicit values can
        # depend on the preceding declaration.
        pass

    def validateEnumDeclaration(
        self,
        node: EnumDeclaration
    ):
        declarationId = id(node)

        if declarationId in self.validatedEnumDeclarations:
            return

        self.validatedEnumDeclarations.add(declarationId)
        self.visit(node.baseType)

        if not (
            isinstance(node.baseType, PrimitiveType)
            and node.baseType.value in ENUM_BACKING_TYPES
        ):
            allowedTypes = ", ".join(
                self.typeText(PrimitiveType(primitive))
                for primitive in ENUM_BACKING_TYPES
            )
            self.report(
                node.baseType,
                (
                    f"Enum '{node.name.name}' must use one of "
                    f"{allowedTypes} as its backing type."
                )
            )
            return

        if not node.members:
            self.report(
                node,
                f"Enum '{node.name.name}' must declare at least one member."
            )
            return

        seenNames: set[str] = set()
        seenValues: dict[
            tuple[str, object],
            EnumMemberDeclaration
        ] = {}
        previousInteger: int | None = None
        previousValueValid = True

        for member in node.members:
            name = member.name.name

            if name in seenNames:
                self.report(
                    member.name,
                    (
                        f"Enum '{node.name.name}' declares member "
                        f"'{name}' more than once."
                    )
                )
            else:
                seenNames.add(name)

            constant: tuple[TypeNode, object] | None = None

            if isinstance(member.value, Uninitialized):
                if not self.isPrimitive(
                    node.baseType,
                    Type.INT
                ):
                    self.report(
                        member,
                        (
                            f"Enum member '{node.name.name}.{name}' "
                            f"must declare a value because only "
                            f"int-backed enums can auto-increment."
                        )
                    )
                    previousValueValid = False
                    continue

                if not previousValueValid:
                    self.report(
                        member,
                        (
                            f"Cannot auto-increment enum member "
                            f"'{node.name.name}.{name}' because the "
                            f"previous value is not a valid integer "
                            f"constant."
                        )
                    )
                    continue

                nextValue = (
                    0
                    if previousInteger is None
                    else previousInteger + 1
                )
                constant = (
                    PrimitiveType(Type.INT),
                    nextValue
                )
            else:
                constant = self.constantExpressionValue(
                    member.value
                )

                if constant is None:
                    if id(member.value) in self.invalidLiteralValues:
                        self.visit(
                            member.value,
                            expectedType=node.baseType
                        )
                        previousValueValid = False
                        previousInteger = None
                        continue

                    invalidResult = self.invalidConstantResults.get(
                        id(member.value)
                    )

                    if invalidResult is not None:
                        resultType, resultValue = invalidResult
                        self.report(
                            member.value,
                            (
                                f"Enum member '{node.name.name}."
                                f"{name}' has a constant expression "
                                f"whose value {resultValue!r} cannot "
                                f"be represented as inferred type "
                                f"'{self.typeText(resultType)}'."
                            )
                        )
                    else:
                        self.report(
                            member.value,
                            (
                                f"Enum member '{node.name.name}."
                                f"{name}' must use a compile-time "
                                f"constant value."
                            )
                        )
                    previousValueValid = False
                    previousInteger = None
                    continue

                self.visit(
                    member.value,
                    expectedType=node.baseType
                )
                compatible = self.isExpressionAssignable(
                    member.value,
                    node.baseType
                )

                if compatible is False:
                    valueType = self.inferExpressionType(
                        member.value
                    )
                    valueText = (
                        self.typeText(valueType)
                        if valueType is not None
                        else "<unknown>"
                    )
                    self.report(
                        member.value,
                        (
                            f"Enum member '{node.name.name}.{name}' "
                            f"must have backing type "
                            f"'{self.typeText(node.baseType)}', got "
                            f"'{valueText}'."
                        )
                    )
                    previousValueValid = False
                    previousInteger = None
                    continue

                if compatible is None:
                    previousValueValid = False
                    previousInteger = None
                    continue

            constantType, constantValue = constant
            member.hasResolvedValue = True
            member.resolvedType = constantType
            member.resolvedValue = constantValue
            valueKey = (
                self.typeText(constantType),
                constantValue
            )

            if valueKey in seenValues:
                first = seenValues[valueKey]
                self.report(
                    member,
                    (
                        f"Enum '{node.name.name}' assigns value "
                        f"{constantValue!r} to both "
                        f"'{first.name.name}' and '{name}'."
                    )
                )
            else:
                seenValues[valueKey] = member

            if self.isPrimitive(
                constantType,
                Type.INT
            ):
                previousInteger = constantValue
                previousValueValid = True
            else:
                previousInteger = None
                previousValueValid = False


    def visitStructDeclaration(
        self,
        node: StructDeclaration
    ):
        seenFields: set[str] = set()

        for field in node.fields:
            name = field.name.name

            if name in seenFields:
                self.report(
                    field.name,
                    (
                        f"Struct '{node.name.name}' declares "
                        f"field '{name}' more than once."
                    )
                )
            else:
                seenFields.add(name)

            self.visit(field)

        seenMethods: set[str] = set()

        for method in node.methods:
            name = method.name.name

            if name in seenMethods:
                self.report(
                    method.name,
                    (
                        f"Struct '{node.name.name}' declares "
                        f"method '{name}' more than once."
                    )
                )
            else:
                seenMethods.add(name)

            if name in seenFields:
                self.report(
                    method.name,
                    (
                        f"Struct '{node.name.name}' cannot use "
                        f"'{name}' as both a field and a method."
                    )
                )

            self.visitStructMethodDeclaration(
                node,
                method
            )

    def visitStructMethodDeclaration(
        self,
        owner: StructDeclaration,
        method: FunctionDeclaration
    ):
        selfParameters = [
            (index, parameter)
            for index, parameter in enumerate(method.parameters)
            if parameter.name.name == "self"
        ]
        instanceMethod = self.isInstanceStructMethod(
            owner,
            method
        )

        for index, parameter in selfParameters:
            if index != 0:
                self.report(
                    parameter.name,
                    (
                        "The reserved 'self' parameter must be "
                        "the first parameter of an instance method."
                    )
                )

        if selfParameters and not instanceMethod:
            firstIndex, firstSelf = selfParameters[0]

            if firstIndex == 0:
                self.report(
                    firstSelf.paramType,
                    (
                        f"The 'self' parameter of method "
                        f"'{owner.name.name}.{method.name.name}' "
                        f"must have type '{owner.name.name}'."
                    )
                )

        self.analyzeCallableBody(
            method,
            methodOwner=owner,
            instanceMethod=instanceMethod
        )


    def visitStructFieldDeclaration(
        self,
        node: StructFieldDeclaration
    ):
        self.visit(node.fieldType)

        if node.modifiers.isNew:
            self.report(
                node.modifiers,
                "Struct fields cannot use the 'new' modifier."
            )

        if node.modifiers.isGlobal:
            self.report(
                node.modifiers,
                "Struct fields cannot use the 'global' modifier."
            )

        if isinstance(node.defaultValue, Uninitialized):
            return

        self.visit(
            node.defaultValue,
            expectedType=node.fieldType
        )
        compatible = self.isExpressionAssignable(
            node.defaultValue,
            node.fieldType
        )

        if compatible is None or compatible:
            return

        valueType = self.inferExpressionType(
            node.defaultValue
        )
        valueText = (
            self.typeText(valueType)
            if valueType is not None
            else "<unknown>"
        )

        self.report(
            node.defaultValue,
            (
                f"Default value for struct field "
                f"'{node.name.name}' must have type "
                f"'{self.typeText(node.fieldType)}', got "
                f"'{valueText}'."
            )
        )


    def visitListType(self, node: ListType):
        self.visit(node.elementType)


    def visitArrayType(self, node: ArrayType):
        if node.isHeterogeneous:
            for slotType in node.slotTypes or []:
                self.visit(slotType)
            return
        self.visit(node.elementType)


    def visitSetType(self, node: SetType):
        self.visit(node.elementType)

    def isHashableDictKeyType(self, typeNode: TypeNode) -> bool:
        if isinstance(typeNode, UnionType):
            return all(
                self.isHashableDictKeyType(member)
                for member in typeNode.members
            )
        if isinstance(typeNode, PrimitiveType):
            return typeNode.value in (
                Type.INT,
                Type.FLOAT,
                Type.STR,
                Type.CHAR,
                Type.BOOL,
                Type.NIL,
                Type.ANY,
                Type.PYOBJECT,
            )
        if isinstance(typeNode, NamedType):
            symbol = self.currentScope.resolveType(typeNode.name.name)
            # Unknown names receive their own diagnostic from visitNamedType().
            return symbol is None or isinstance(symbol.declaration, EnumDeclaration)
        return False

    def validateDictKeyType(self, keyType: TypeNode):
        if not self.isHashableDictKeyType(keyType):
            self.report(
                keyType,
                f"Dictionary key type '{self.typeText(keyType)}' is not hashable."
            )

    def visitDictType(self, node: DictType):
        self.visit(node.keyType)
        self.visit(node.valueType)
        self.validateDictKeyType(node.keyType)


    def visitDeclarationModifiers(
        self,
        node: DeclarationModifiers
    ):
        pass

    def installBuiltins(self):
        anyType = PrimitiveType(Type.ANY)
        strType = PrimitiveType(Type.STR)

        signatures = {
            # `print` accepts any output value. The optional second
            # positional argument is the string terminator.
            "print": (
                PrimitiveType(Type.NIL),
                (anyType, strType),
                ("output", "end"),
                1,
                2
            ),
            "input": (
                PrimitiveType(Type.STR),
                (strType,),
                ("preview",),
                0,
                1
            ),
            "index": (
                PrimitiveType(Type.INT),
                (anyType,),
                ("value",),
                1,
                1
            ),
            "int": (
                PrimitiveType(Type.INT),
                (anyType,),
                ("value",),
                0,
                1
            ),
            "str": (
                PrimitiveType(Type.STR),
                (anyType,),
                ("value",),
                0,
                1
            ),
            "float": (
                PrimitiveType(Type.FLOAT),
                (anyType,),
                ("value",),
                0,
                1
            ),
            "char": (
                PrimitiveType(Type.CHAR),
                (anyType,),
                ("value",),
                0,
                1
            ),
            "bool": (
                PrimitiveType(Type.BOOL),
                (anyType,),
                ("value",),
                1,
                1
            ),
            **{
                name: (
                    PrimitiveType(Type.BOOL),
                    (anyType,),
                    ("value",),
                    1,
                    1
                )
                for name in (
                    "is_int", "is_char", "is_str", "is_float", "is_bool",
                    "is_list", "is_arr", "is_set", "is_dict", "is_empty", "is_full"
                )
            },
            **{
                name: (
                    PrimitiveType(Type.NIL),
                    (anyType,),
                    ("value",),
                    1,
                    1
                )
                for name in (
                    "to_int", "to_char", "to_str", "to_float", "to_bool",
                    "to_list"
                )
            },
            "to_arr": (
                PrimitiveType(Type.NIL),
                (anyType, PrimitiveType(Type.INT)),
                ("value", "capacity"),
                1,
                2
            ),
            "open": (
                PrimitiveType(Type.FILE),
                (strType, strType, strType),
                ("path", "mode", "encoding"),
                1,
                3
            ),
            "pyimport": (
                PrimitiveType(Type.PYOBJECT),
                (strType,),
                ("module",),
                1,
                1
            )
        }

        for canonicalName, aliases in BUILTIN_ALIASES.items():
            (
                returnType,
                parameterTypes,
                parameterNames,
                minimumArguments,
                maximumArguments
            ) = signatures[canonicalName]

            for alias in aliases:
                aliasParameterNames = parameterNames
                if canonicalName == "open" and alias == "ᚩᛈᛖᚾ":
                    aliasParameterNames = (
                        "ᛈᚫᚦ",
                        "ᛗᚩᛞ",
                        "ᛖᚾᚳᚩᛞᛁᛝ",
                    )
                if canonicalName == "pyimport" and alias == "ᛈᛠᛁᛗᛈᛟᚱᛏ":
                    aliasParameterNames = ("ᛗᚫᚷᚻᚣᛚ",)
                self.globalScope.define(
                    BuiltinFunctionSymbol(
                        name=alias,
                        returnType=returnType,
                        parameterTypes=parameterTypes,
                        parameterNames=aliasParameterNames,
                        minimumArguments=minimumArguments,
                        maximumArguments=maximumArguments
                    )
                )

    def declareType(
        self,
        declaration: NamedTypeDeclaration
    ) -> TypeSymbol | None:
        name = declaration.name.name
        localExisting = self.currentScope.localType(name)
        existing = self.currentScope.resolveType(name)

        if existing is not None:
            if localExisting is not None:
                message = (
                    f"Type '{name}' is already "
                    f"declared in this scope."
                )
            else:
                message = (
                    f"Type '{name}' cannot shadow a type "
                    f"declared in an outer scope."
                )

            self.report(declaration.name, message)
            return None

        symbol = TypeSymbol(
            name=name,
            declaration=declaration,
            kind=declaration.kind
        )

        self.currentScope.defineType(symbol)
        return symbol

    def statementsInCurrentScope(
        self,
        statements: list[Node]
    ):
        """
        Yield every instruction belonging to the current lexical
        scope, including instructions nested inside control-flow
        blocks. Stop at function declarations because their bodies
        create separate scopes.
        """
        for statement in statements:
            yield statement

            if isinstance(statement, FunctionDeclaration):
                continue

            blocks: list[Block] = []

            if isinstance(statement, IfStatement):
                blocks.append(statement.thenBranch)
                blocks.extend(
                    branch.body
                    for branch in statement.elsifBranches
                )

                if statement.elseBranch is not None:
                    blocks.append(statement.elseBranch)

            elif isinstance(
                statement,
                (
                    WhileStatement,
                    UntilStatement,
                    ForStatement,
                    ForeachStatement
                )
            ):
                blocks.append(statement.body)

            for block in blocks:
                yield from self.statementsInCurrentScope(
                    block.statements
                )

    def predeclareTypes(
        self,
        statements: list[Node]
    ):
        declarations = [
            statement
            for statement in self.statementsInCurrentScope(
                statements
            )
            if isinstance(
                statement,
                NamedTypeDeclaration
            )
        ]
        declaredEnums: list[EnumDeclaration] = []

        # All type names must exist before enum backing types and values
        # are validated, so this deliberately runs as three passes.
        for declaration in declarations:
            symbol = self.declareType(declaration)

            if (
                symbol is not None
                and isinstance(declaration, EnumDeclaration)
            ):
                declaredEnums.append(declaration)

        for declaration in declaredEnums:
            self.declareEnumMembers(declaration)

        for declaration in declaredEnums:
            self.validateEnumDeclaration(declaration)

    def declareEnumMembers(
        self,
        declaration: EnumDeclaration
    ):
        seen: set[str] = set()

        for member in declaration.members:
            name = member.name.name

            if name in seen:
                # The declaration validator emits the enum-specific
                # duplicate diagnostic and keeps the first canonical.
                continue

            seen.add(name)
            existing = self.currentScope.local(name)

            symbol = EnumMemberSymbol(
                name=name,
                declaredType=NamedType(declaration.name),
                declaration=member,
                enumDeclaration=declaration
            )

            if isinstance(existing, EnumMemberSymbol):
                self.currentScope.define(
                    AmbiguousEnumMemberSymbol(
                        name=name,
                        members=[existing, symbol]
                    )
                )
                continue

            if isinstance(
                existing,
                AmbiguousEnumMemberSymbol
            ):
                existing.members.append(symbol)
                continue

            if existing is not None:
                self.report(
                    member.name,
                    (
                        f"Enum member '{declaration.name.name}."
                        f"{name}' conflicts with value name "
                        f"'{name}' already declared in this scope."
                    )
                )
                continue

            self.currentScope.define(symbol)

    def predeclareFunctions(
        self,
        statements: list[Node]
    ):
        for statement in self.statementsInCurrentScope(
            statements
        ):
            if not isinstance(
                statement,
                FunctionDeclaration
            ):
                continue

            name = statement.name.name

            # Keep the first declaration. Later duplicates
            # will be reported during normal analysis.
            if (
                name
                not in self.currentScope.predeclaredFunctions
            ):
                self.currentScope.predeclaredFunctions[name] = (
                    FunctionSymbol(
                        name=name,
                        declaration=statement
                    )
                )

    def visitUnionType(self, node: UnionType):
        for member in node.members:
            self.visit(member)
