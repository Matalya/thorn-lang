from __future__ import annotations

import ast
import builtins as python_builtins
import importlib
from collections.abc import Callable

from th_ast import *
from runtime import (
    Cell,
    Environment,
    ReturnSignal,
    ThornFunction,
    ThornArray,
    ThornCollection,
    ThornList,
    ThornRuntimeError,
    ThornSet,
    ThornStruct,
    ThornStructType,
    ThornEnumType,
    ThornEnumValue,
    ThornFile,
    ThornPyObject,
    thorn_to_python,
    python_to_thorn,
    python_collection_item_to_thorn,
    UNINITIALIZED,
    format_value,
)


class Interpreter:
    """Tree-walking interpreter for Thorn's core language."""

    def __init__(
        self,
        *,
        output: Callable[[str], None] | None = None,
        input_function: Callable[[str], str] | None = None,
    ):
        self.globals = Environment(name="global")
        self.environment = self.globals
        self.current_return_type = None
        self.output = output or (lambda text: print(text, end=""))
        self.input_function = input_function or input
        self.foreach_index = None
        self.foreach_value = UNINITIALIZED
        self.open_files = []
        self._install_builtins()

    def _install_builtins(self):
        builtins = {
            ("print", "ᛈᚱᛁᚾᛏ"): self._builtin_print,
            ("input", "ᛁᚾᛈᚣᛏ"): lambda preview="": self.input_function(preview),
            ("index", "ᛁᚾᛞᛖᛉ"): self._builtin_index,
            ("str", "ᛋᛏᚱ", "ᛥᚱ"): lambda value="": format_value(value),
            ("int", "ᛁᚾᛏ"): lambda value=0: int(thorn_to_python(value)),
            ("float", "ᚠᛚᚩᛏ"): lambda value=0.0: float(thorn_to_python(value)),
            ("bool", "ᛒᚣᛚ"): lambda value=False: bool(thorn_to_python(value)),
            ("char", "ᚳᚻᚪᚱ"): self._builtin_char,
            ("is_int", "ᛁᛋ_ᛁᚾᛏ"): lambda value: type(value) is int,
            ("is_char", "ᛁᛋ_ᚳᚻᚪᚱ"): lambda value: isinstance(value, str) and len(value) == 1,
            ("is_str", "ᛁᛋ_ᛋᛏᚱ"): lambda value: isinstance(value, str),
            ("is_float", "ᛁᛋ_ᚠᛚᚩᛏ"): lambda value: isinstance(value, float),
            ("is_bool", "ᛁᛋ_ᛒᚣᛚ"): lambda value: isinstance(value, bool),
            ("is_list", "ᛁᛋ_ᛚᛁᛋᛏ"): lambda value: isinstance(value, ThornList) and not isinstance(value, ThornArray),
            ("is_arr", "ᛁᛋ_ᚪᚱ"): lambda value: isinstance(value, ThornArray),
            ("is_set", "ᛁᛋ_ᛋᛖᛏ"): lambda value: isinstance(value, ThornSet),
            ("is_empty", "ᛁᛋ_ᛖᛗᛈᛏᛁ"): self._builtin_is_empty,
            ("is_full", "ᛁᛋ_ᚠᚣᛚ"): self._builtin_is_full,
            ("open", "ᚩᛈᛖᚾ"): self._builtin_open,
            ("pyimport", "ᛈᛠᛁᛗᛈᛟᚱᛏ"): self._builtin_pyimport,
        }
        for aliases, function in builtins.items():
            for alias in aliases:
                self.globals.declare(alias, function, constant=True)

    def _builtin_print(self, output, end="\n"):
        self.output(format_value(output) + end)
        return None

    def _builtin_char(self, value=""):
        if value == "":
            return "\0"
        if type(value) is int:
            return chr(value)
        text = str(value)
        if len(text) != 1:
            raise ThornRuntimeError("Character conversion requires exactly one character")
        return text

    def _builtin_index(self, value):
        if self.foreach_index is None or not (
            value is self.foreach_value or value == self.foreach_value
        ):
            raise ThornRuntimeError("index() requires the current foreach item")
        return self.foreach_index

    def _builtin_is_empty(self, value):
        if not isinstance(value, ThornCollection):
            raise ThornRuntimeError("is_empty() requires a collection")
        return len(value) == 0

    def _builtin_is_full(self, value):
        if not isinstance(value, ThornArray):
            raise ThornRuntimeError("is_full() requires an array")
        return value.length() == value.capacity()

    def _builtin_open(self, *args, **kwargs):
        aliases = {
            "ᛈᚫᚦ": "path",
            "ᛗᚩᛞ": "mode",
            "ᛖᚾᚳᚩᛞᛁᛝ": "encoding",
        }
        normalized = {aliases.get(name, name): value for name, value in kwargs.items()}
        names = ("path", "mode", "encoding")
        if len(args) > len(names):
            raise ThornRuntimeError("open() accepts at most three arguments")
        for name, value in zip(names, args):
            if name in normalized:
                raise ThornRuntimeError(f"open() received '{name}' more than once")
            normalized[name] = value
        if "path" not in normalized:
            raise ThornRuntimeError("open() requires a path")
        path = normalized["path"]
        mode = normalized.get("mode", "r")
        encoding = normalized.get("encoding", "utf-8")
        if "b" in mode:
            raise ThornRuntimeError(
                "binary file modes are unavailable until Thorn has a bytes type"
            )
        try:
            handle = python_builtins.open(path, mode, encoding=encoding)
        except (OSError, ValueError, UnicodeError) as error:
            raise ThornRuntimeError(f"cannot open file '{path}': {error}") from error
        file = ThornFile(handle, path)
        self.open_files.append(file)
        return file

    def _builtin_pyimport(self, *args, **kwargs):
        aliases = {"ᛗᚫᚷᚻᚣᛚ": "module"}
        normalized = {aliases.get(name, name): value for name, value in kwargs.items()}
        if len(args) > 1:
            raise ThornRuntimeError("pyimport() accepts exactly one argument")
        if args:
            if "module" in normalized:
                raise ThornRuntimeError("pyimport() received 'module' more than once")
            normalized["module"] = args[0]
        if "module" not in normalized:
            raise ThornRuntimeError("pyimport() requires a module")
        unknown = set(normalized) - {"module"}
        if unknown:
            name = next(iter(unknown))
            raise ThornRuntimeError(f"pyimport() has no parameter named '{name}'")
        module = normalized["module"]
        try:
            return ThornPyObject(importlib.import_module(module))
        except Exception as error:
            raise ThornRuntimeError(
                f"Python {type(error).__name__}: {error}"
            ) from error

    def run(self, program: Program):
        # Functions are visible throughout their containing scope.
        self._predeclare_declarations(program.statements)
        result = None
        try:
            for statement in program.statements:
                result = self.execute(statement)
            return result
        finally:
            for file in self.open_files:
                file.close()

    def _predeclare_functions(self, statements):
        for statement in statements:
            if isinstance(statement, FunctionDeclaration):
                if statement.name.name not in self.environment.cells:
                    self.environment.declare(
                        statement.name.name,
                        ThornFunction(statement, self.environment),
                        constant=True,
                    )

    def _predeclare_declarations(self, statements):
        scoped_statements = list(self._scope_statements(statements))
        for statement in scoped_statements:
            if isinstance(statement, StructDeclaration):
                if statement.name.name not in self.environment.types:
                    struct_type = ThornStructType(statement, self.environment)
                    self.environment.declare_type(statement.name.name, struct_type)
                    # Type names are also values for static member access.
                    if statement.name.name not in self.environment.cells:
                        self.environment.declare(statement.name.name, struct_type, constant=True)
            elif isinstance(statement, EnumDeclaration):
                if statement.name.name not in self.environment.types:
                    enum_type = ThornEnumType(statement)
                    self.environment.declare_type(statement.name.name, enum_type)
                    if statement.name.name not in self.environment.cells:
                        self.environment.declare(statement.name.name, enum_type, constant=True)
                    for member in statement.members:
                        value = ThornEnumValue(
                            enum_type, member.name.name, member.resolvedValue
                        )
                        enum_type.members[member.name.name] = value
                        if member.name.name not in self.environment.cells:
                            self.environment.declare(
                                member.name.name, value, constant=True
                            )
            elif isinstance(statement, VarDeclaration) and not statement.modifiers.isNew:
                target = self.globals if statement.modifiers.isGlobal else self.environment
                if statement.varName.name not in target.cells:
                    target.declare(
                        statement.varName.name,
                        UNINITIALIZED,
                        constant=statement.modifiers.isConst,
                        declared_type=statement.varType,
                    )
        self._predeclare_functions(scoped_statements)

    def _scope_statements(self, statements):
        for statement in statements:
            yield statement
            if isinstance(statement, FunctionDeclaration):
                continue
            blocks = []
            if isinstance(statement, IfStatement):
                blocks.append(statement.thenBranch)
                blocks.extend(branch.body for branch in statement.elsifBranches)
                if statement.elseBranch is not None:
                    blocks.append(statement.elseBranch)
            elif isinstance(statement, (WhileStatement, UntilStatement, ForStatement, ForeachStatement)):
                blocks.append(statement.body)
            for block in blocks:
                yield from self._scope_statements(block.statements)

    def execute(self, node):
        method = getattr(self, f"execute_{type(node).__name__}", None)
        if method is None:
            raise ThornRuntimeError(
                f"Runtime support for {type(node).__name__} is not implemented", node
            )
        try:
            return method(node)
        except ThornRuntimeError as error:
            if error.span is None:
                error.span = getattr(node, "span", None)
            raise

    def evaluate(self, node):
        return self.execute(node)

    def evaluate_as(self, node, expected_type):
        if isinstance(expected_type, UnionType) and isinstance(node, StructLiteral):
            supplied = {field.name.name for field in node.fields}
            candidates = []
            for member in expected_type.members:
                if not isinstance(member, NamedType):
                    continue
                runtime_type = self.environment.resolve_type(member.name.name)
                if not isinstance(runtime_type, ThornStructType):
                    continue
                fields = runtime_type.declaration.fields
                declared = {field.name.name for field in fields}
                required = {
                    field.name.name
                    for field in fields
                    if isinstance(field.defaultValue, Uninitialized)
                }
                if required <= supplied <= declared:
                    candidates.append(runtime_type)
            if len(candidates) == 1:
                return self._instantiate_struct(candidates[0], node)
        if isinstance(node, StructLiteral) and isinstance(expected_type, NamedType):
            runtime_type = self.environment.resolve_type(expected_type.name.name)
            if isinstance(runtime_type, ThornStructType):
                return self._instantiate_struct(runtime_type, node)
        if isinstance(node, ListLiteral) and isinstance(expected_type, ListType):
            return ThornList(
                (self.evaluate_as(item, expected_type.elementType) for item in node.elements),
                expected_type.elementType,
            )
        if isinstance(node, ArrayLiteral) and isinstance(expected_type, ArrayType):
            return ThornArray(
                (self.evaluate_as(item, expected_type.elementType) for item in node.elements),
                expected_type.capacity,
                lambda message: self.output(f"warning: {message}\n"),
                expected_type.elementType,
            )
        if isinstance(node, SetLiteral) and isinstance(expected_type, SetType):
            return ThornSet(
                (self.evaluate_as(item, expected_type.elementType) for item in node.elements),
                expected_type.elementType,
            )
        value = self.evaluate(node)
        if isinstance(expected_type, NamedType):
            runtime_type = self.environment.resolve_type(expected_type.name.name)
            if isinstance(runtime_type, ThornEnumType) and not isinstance(value, ThornEnumValue):
                return runtime_type.from_raw(value)
        return value

    def execute_Literal(self, node: Literal):
        if node.litType == Type.NIL:
            return None
        if node.litType == Type.BOOL:
            return node.litValue.lower() == "true"
        if node.litType == Type.INT:
            return int(node.litValue)
        if node.litType == Type.FLOAT:
            return float(node.litValue)
        if node.litType in (Type.STR, Type.CHAR):
            # Lexer-produced literals retain their quotes. Text pieces created
            # by the composite-string parser are already decoded strings.
            if not (
                len(node.litValue) >= 2
                and node.litValue[0] in ('"', "'")
                and node.litValue[-1] == node.litValue[0]
            ):
                return node.litValue
            try:
                return ast.literal_eval(node.litValue)
            except (SyntaxError, ValueError):
                return node.litValue[1:-1]
        raise ThornRuntimeError(f"Unknown literal type '{node.litType}'", node)

    def execute_Identifier(self, node: Identifier):
        try:
            return self.environment.read(node.name)
        except ThornRuntimeError as error:
            error.span = node.span
            raise

    def execute_Uninitialized(self, node: Uninitialized):
        return UNINITIALIZED

    def execute_CompositeString(self, node: CompositeString):
        parts = []
        for component in node.components:
            value = self.evaluate(component.value)
            parts.append(value if isinstance(value, str) else format_value(value))
        return "".join(parts)

    def execute_UnaryOp(self, node: UnaryOp):
        right = self.evaluate(node.right)
        if node.op == Op.NEG:
            return -right
        if node.op == Op.NOT:
            return not right
        raise ThornRuntimeError(f"Unknown unary operator '{node.op.name}'", node)

    def execute_BinaryOp(self, node: BinaryOp):
        left = self.evaluate(node.left)
        if node.op == Op.AND:
            return left and self.evaluate(node.right)
        if node.op == Op.OR:
            return left or self.evaluate(node.right)
        right = self.evaluate(node.right)
        operations = {
            Op.POWER: lambda: left ** right,
            Op.MULT: lambda: left * right,
            Op.DIV: lambda: left / right,
            Op.MOD: lambda: left % right,
            Op.FLOOR_DIV: lambda: left // right,
            Op.ADD: lambda: left + right,
            Op.SUB: lambda: left - right,
            Op.EQUALS: lambda: left == right,
            Op.NOT_EQUAL: lambda: left != right,
            Op.LESS_THAN: lambda: left < right,
            Op.MORE_THAN: lambda: left > right,
            Op.LESS_EQUAL: lambda: left <= right,
            Op.MORE_EQUAL: lambda: left >= right,
            Op.XOR: lambda: bool(left) ^ bool(right),
        }
        try:
            return operations[node.op]()
        except KeyError:
            raise ThornRuntimeError(f"Unknown binary operator '{node.op.name}'", node)
        except (ArithmeticError, TypeError, ValueError) as error:
            raise ThornRuntimeError(str(error), node) from error

    def execute_VarDeclaration(self, node: VarDeclaration):
        target = self.globals if node.modifiers.isGlobal else self.environment
        value = (
            UNINITIALIZED
            if isinstance(node.varValue, Uninitialized)
            else self.evaluate_as(node.varValue, node.varType)
        )
        if isinstance(node.varType, ArrayType) and isinstance(value, ThornArray):
            # Capacity written on a declaration initializes a fresh literal,
            # but never resizes an array value that already exists elsewhere.
            if isinstance(node.varValue, ArrayLiteral):
                value = ThornArray(
                    value.values,
                    node.varType.capacity,
                    value.warning,
                    node.varType.elementType,
                )
        name = node.varName.name
        if node.modifiers.isNew:
            target.cells[name] = Cell(value, node.modifiers.isConst, node.varType)
        elif name in target.cells:
            target.cells[name].value = value
            target.cells[name].declared_type = node.varType
        else:
            target.declare(
                name, value, constant=node.modifiers.isConst,
                declared_type=node.varType
            )
        return None

    def execute_VarAssign(self, node: VarAssign):
        value = self.evaluate_as(node.value, self._target_type(node.target))
        self._assign_target(node.target, value)
        return value

    def _target_type(self, target):
        if isinstance(target, Identifier):
            return self.environment.resolve_cell(target.name).declared_type
        if isinstance(target, MemberAccess):
            owner = self.evaluate(target.target)
            if isinstance(owner, ThornStruct):
                return owner.fields[target.member.name].declared_type
        if isinstance(target, IndexAccess):
            collection = self.evaluate(target.target)
            if isinstance(collection, ThornCollection):
                return collection.element_type
        return None

    def execute_CompoundAssign(self, node: CompoundAssign):
        current = self.evaluate(node.target)
        synthetic = BinaryOp(Literal(Type.INT, "0"), node.op, Literal(Type.INT, "0"))
        synthetic.left, synthetic.right = _Value(current), _Value(self.evaluate(node.value))
        value = self.execute_BinaryOp(synthetic)
        self._assign_target(node.target, value)
        return value

    def _assign_target(self, target, value):
        if isinstance(target, Identifier):
            return self.environment.assign(target.name, value)
        if isinstance(target, IndexAccess):
            collection = self.evaluate(target.target)
            index = self.evaluate(target.index)
            if isinstance(collection, ThornPyObject):
                try:
                    collection.value[thorn_to_python(index)] = thorn_to_python(value)
                except Exception as error:
                    raise ThornRuntimeError(
                        f"Python {type(error).__name__}: {error}", target
                    ) from error
            else:
                collection[index] = value
            return value
        if isinstance(target, MemberAccess):
            owner = self.evaluate(target.target)
            if isinstance(owner, ThornStruct):
                return owner.assign(target.member.name, value)
            if isinstance(owner, ThornPyObject):
                try:
                    setattr(owner.value, target.member.name, thorn_to_python(value))
                    return value
                except Exception as error:
                    raise ThornRuntimeError(
                        f"Python {type(error).__name__}: {error}", target
                    ) from error
        raise ThornRuntimeError("Invalid assignment target", target)

    def execute__Value(self, node):
        return node.value

    def execute_ExpressionStatement(self, node: ExpressionStatement):
        return self.evaluate(node.expression)

    def execute_Block(self, node: Block):
        self._predeclare_declarations(node.statements)
        result = None
        for statement in node.statements:
            result = self.execute(statement)
        return result

    def execute_IfStatement(self, node: IfStatement):
        if self.evaluate(node.condition):
            return self.execute(node.thenBranch)
        for branch in node.elsifBranches:
            if self.evaluate(branch.condition):
                return self.execute(branch.body)
        if node.elseBranch is not None:
            return self.execute(node.elseBranch)
        return None

    def execute_WhileStatement(self, node: WhileStatement):
        while self.evaluate(node.condition):
            self.execute(node.body)

    def execute_UntilStatement(self, node: UntilStatement):
        while True:
            self.execute(node.body)
            if self.evaluate(node.condition):
                break

    def execute_ForStatement(self, node: ForStatement):
        start, end = self.evaluate(node.start), self.evaluate(node.end)
        cell = self.environment.cells.get(node.iterator.name)
        if cell is None:
            cell = self.environment.declare(node.iterator.name)
        for value in range(start, end):
            cell.value = value
            self.execute(node.body)

    def execute_ForeachStatement(self, node: ForeachStatement):
        cell = self.environment.cells.get(node.iterator.name)
        if cell is None:
            cell = self.environment.declare(node.iterator.name)
        old_index, old_value = self.foreach_index, self.foreach_value
        try:
            collection = self.evaluate(node.collection)
            iterable = collection.value if isinstance(collection, ThornPyObject) else collection
            for index, value in enumerate(iterable):
                if isinstance(collection, ThornPyObject):
                    value = python_to_thorn(value)
                self.foreach_index, self.foreach_value = index, value
                cell.value = value
                self.execute(node.body)
        finally:
            self.foreach_index, self.foreach_value = old_index, old_value

    def execute_FunctionDeclaration(self, node: FunctionDeclaration):
        return None

    def execute_StructDeclaration(self, node: StructDeclaration):
        return None

    def execute_EnumDeclaration(self, node: EnumDeclaration):
        enum_type = self.environment.resolve_type(node.name.name)
        if enum_type.members:
            return None
        for member in node.members:
            value = ThornEnumValue(enum_type, member.name.name, member.resolvedValue)
            enum_type.members[member.name.name] = value
            # Unqualified member names are installed unless another enum has
            # already claimed that value-namespace name.
            if member.name.name not in self.environment.cells:
                self.environment.declare(member.name.name, value, constant=True)
        return None

    def execute_StructLiteral(self, node: StructLiteral):
        if node.typeName is None:
            raise ThornRuntimeError(
                "Anonymous struct literal requires a runtime type context", node
            )
        struct_type = self.environment.resolve_type(node.typeName.name)
        return self._instantiate_struct(struct_type, node)

    def _instantiate_struct(self, struct_type, literal):
        instance = ThornStruct(struct_type)
        supplied = {field.name.name: field.value for field in literal.fields}
        previous = self.environment
        field_environment = Environment(struct_type.closure, f"{struct_type.name} initializer")
        self.environment = field_environment
        try:
            field_environment.declare("self", instance, constant=True)
            field_environment.declare("ᛋᛖᛚᚠ", instance, constant=True)
            for field in struct_type.declaration.fields:
                name = field.name.name
                if name in supplied:
                    value = self.evaluate_as(supplied[name], field.fieldType)
                elif not isinstance(field.defaultValue, Uninitialized):
                    value = self.evaluate_as(field.defaultValue, field.fieldType)
                else:
                    value = UNINITIALIZED
                instance.fields[name] = Cell(
                    value, field.modifiers.isConst, field.fieldType
                )
                field_environment.declare(
                    name, value, declared_type=field.fieldType
                )
        finally:
            self.environment = previous
        return instance

    def execute_FunctionCall(self, node: FunctionCall):
        if isinstance(node.callee, Identifier) and node.callee.name in _MUTATING_CONVERSIONS:
            return self._mutating_conversion(node)
        callee = self.evaluate(node.callee)
        if isinstance(callee, ThornPyObject):
            return self._call_python(callee, node.arguments, node)
        if isinstance(callee, ThornFunction):
            return self._call_function(callee, node.arguments, node)
        if isinstance(callee, _BoundThornMethod):
            return callee.call(node.arguments, node)
        positional, named = self._evaluate_arguments(node.arguments)
        if (
            isinstance(node.callee, MemberAccess)
            and node.callee.member.name == "ᚱᛁᛋᛖᛗᛒᚢᛚ"
            and "ᚢᚦᚢ" in named
        ):
            named["other"] = named.pop("ᚢᚦᚢ")
        try:
            return callee(*positional, **named)
        except (TypeError, ValueError) as error:
            raise ThornRuntimeError(str(error), node) from error

    def _call_python(self, callee, arguments, node):
        if not callable(callee.value):
            raise ThornRuntimeError(
                f"Python object of type '{callee.python_type_name}' is not callable",
                node,
            )
        positional, named = self._evaluate_arguments(arguments)
        try:
            result = callee.value(
                *(thorn_to_python(value) for value in positional),
                **{name: thorn_to_python(value) for name, value in named.items()},
            )
            return python_to_thorn(result)
        except Exception as error:
            raise ThornRuntimeError(
                f"Python {type(error).__name__}: {error}", node
            ) from error

    def _mutating_conversion(self, node):
        canonical = _MUTATING_CONVERSIONS[node.callee.name]
        if not node.arguments:
            raise ThornRuntimeError(f"{canonical}() requires a value", node)
        first = node.arguments[0]
        target = first.value if isinstance(first, NamedArgument) else first
        current = self.evaluate(target)
        if canonical == "to_int":
            converted = int(current)
        elif canonical == "to_char":
            converted = self._builtin_char(current)
        elif canonical == "to_str":
            converted = format_value(current)
        elif canonical == "to_float":
            converted = float(current)
        elif canonical == "to_bool":
            converted = bool(current)
        elif canonical == "to_list":
            converted = self._convert_list(current)
        else:
            capacity = None
            if len(node.arguments) > 1:
                argument = node.arguments[1]
                capacity = self.evaluate(
                    argument.value if isinstance(argument, NamedArgument) else argument
                )
            values = self._conversion_values(current)
            converted = ThornArray(
                values,
                len(values) if capacity is None else capacity,
                lambda message: self.output(f"warning: {message}\n"),
            )
        self._assign_target(target, converted)
        return None

    def _conversion_values(self, value, elementType=None):
        if isinstance(value, ThornPyObject):
            try:
                return [
                    (
                        ThornPyObject(item)
                        if (
                            isinstance(elementType, PrimitiveType)
                            and elementType.value == Type.PYOBJECT
                        )
                        else python_collection_item_to_thorn(item)
                    )
                    for item in value.value
                ]
            except TypeError as error:
                raise ThornRuntimeError(
                    f"Python object of type '{value.python_type_name}' is not iterable"
                ) from error
            except Exception as error:
                raise ThornRuntimeError(
                    f"Python {type(error).__name__}: {error}"
                ) from error
        if isinstance(value, ThornCollection):
            return list(value.values)
        if isinstance(value, str):
            return list(value)
        return [value]

    def _convert_list(self, value):
        return ThornList(self._conversion_values(value))

    def execute_CollectionConversion(self, node: CollectionConversion):
        positional, named = self._evaluate_arguments(node.arguments)
        parameterNames = (
            ("value", "capacity")
            if node.collectionKind == "arr"
            else ("value",)
        )
        if len(positional) > len(parameterNames):
            raise ThornRuntimeError(
                f"{node.collectionKind}() accepts at most "
                f"{len(parameterNames)} value argument(s)",
                node,
            )
        supplied = dict(named)
        for name, value in zip(parameterNames, positional):
            if name in supplied:
                raise ThornRuntimeError(
                    f"{node.collectionKind}() received '{name}' more than once",
                    node,
                )
            supplied[name] = value
        unknown = set(supplied) - set(parameterNames)
        if unknown:
            name = next(iter(unknown))
            raise ThornRuntimeError(
                f"{node.collectionKind}() has no parameter named '{name}'",
                node,
            )

        if "value" in supplied:
            values = self._conversion_values(
                supplied["value"],
                node.elementType,
            )
        else:
            values = []

        converted = [
            self._collection_conversion_element(value, node.elementType, node)
            for value in values
        ]

        if node.collectionKind == "list":
            return ThornList(converted, node.elementType)
        if node.collectionKind == "set":
            return ThornSet(converted, node.elementType)

        capacity = supplied.get("capacity", len(converted))
        if type(capacity) is not int:
            raise ThornRuntimeError("Array capacity must be an integer", node)
        return ThornArray(
            converted,
            capacity,
            lambda message: self.output(f"warning: {message}\n"),
            node.elementType,
        )

    def _collection_conversion_element(self, value, expectedType, node):
        if isinstance(expectedType, UnionType):
            for member in expectedType.members:
                try:
                    return self._collection_conversion_element(value, member, node)
                except ThornRuntimeError:
                    pass
            raise ThornRuntimeError(
                f"Collection element {format_value(value)} does not match "
                f"type '{self._runtime_type_text(expectedType)}'",
                node,
            )

        if isinstance(expectedType, NamedType):
            runtimeType = self.environment.resolve_type(expectedType.name.name)
            if isinstance(runtimeType, ThornEnumType):
                if isinstance(value, ThornEnumValue):
                    if value.enum_type is runtimeType:
                        return value
                else:
                    try:
                        return runtimeType.from_raw(value)
                    except ThornRuntimeError:
                        pass
            elif (
                isinstance(runtimeType, ThornStructType)
                and isinstance(value, ThornStruct)
                and value.struct_type is runtimeType
            ):
                return value
            raise ThornRuntimeError(
                f"Collection element {format_value(value)} does not match "
                f"type '{expectedType.name.name}'",
                node,
            )

        if isinstance(expectedType, ListType):
            matches = isinstance(value, ThornList) and not isinstance(value, ThornArray)
            if matches:
                for item in value.values:
                    self._collection_conversion_element(
                        item, expectedType.elementType, node
                    )
        elif isinstance(expectedType, ArrayType):
            matches = isinstance(value, ThornArray)
            if matches:
                for item in value.values:
                    self._collection_conversion_element(
                        item, expectedType.elementType, node
                    )
        elif isinstance(expectedType, SetType):
            matches = isinstance(value, ThornSet)
            if matches:
                for item in value.values:
                    self._collection_conversion_element(
                        item, expectedType.elementType, node
                    )
        elif isinstance(expectedType, PrimitiveType):
            expected = expectedType.value
            if expected == Type.ANY:
                return value
            if expected == Type.INT:
                matches = type(value) is int
            elif expected == Type.FLOAT:
                matches = type(value) in (int, float)
            elif expected == Type.BOOL:
                matches = type(value) is bool
            elif expected == Type.CHAR:
                matches = isinstance(value, str) and len(value) == 1
            elif expected == Type.STR:
                matches = isinstance(value, str)
            elif expected == Type.NIL:
                matches = value is None
            elif expected == Type.UNINITIALIZED:
                matches = value is UNINITIALIZED
            elif expected == Type.FILE:
                matches = isinstance(value, ThornFile)
            elif expected == Type.PYOBJECT:
                matches = isinstance(value, ThornPyObject)
            else:
                matches = False
        else:
            matches = False

        if matches:
            return value
        raise ThornRuntimeError(
            f"Collection element {format_value(value)} does not match "
            f"type '{self._runtime_type_text(expectedType)}'",
            node,
        )

    def _runtime_type_text(self, typeNode):
        if isinstance(typeNode, PrimitiveType):
            return str(typeNode.value)
        if isinstance(typeNode, NamedType):
            return typeNode.name.name
        if isinstance(typeNode, ListType):
            return f"list({self._runtime_type_text(typeNode.elementType)})"
        if isinstance(typeNode, ArrayType):
            return f"arr({self._runtime_type_text(typeNode.elementType)})"
        if isinstance(typeNode, SetType):
            return f"set({self._runtime_type_text(typeNode.elementType)})"
        if isinstance(typeNode, UnionType):
            return " | ".join(self._runtime_type_text(member) for member in typeNode.members)
        return "<unknown>"

    def execute_MemberAccess(self, node: MemberAccess):
        target = self.evaluate(node.target)
        if isinstance(target, ThornCollection):
            return target.method(node.member.name)
        if isinstance(target, ThornFile):
            return target.method(node.member.name)
        if isinstance(target, ThornPyObject):
            try:
                return python_to_thorn(getattr(target.value, node.member.name))
            except Exception as error:
                raise ThornRuntimeError(
                    f"Python {type(error).__name__}: {error}", node
                ) from error
        if type(target) is int:
            integer_methods = {
                "gt": lambda value: target > value,
                "ᚷᚦ": lambda value: target > value,
                "lt": lambda value: target < value,
                "ᛚᚦ": lambda value: target < value,
                "between": lambda lower, upper: self._between(target, lower, upper),
                "ᛒᛁᛏᚹᛁᛁᚾ": lambda lower, upper: self._between(target, lower, upper),
            }
            if node.member.name in integer_methods:
                return integer_methods[node.member.name]
        if isinstance(target, ThornEnumType):
            return target.member(node.member.name)
        if isinstance(target, ThornStruct):
            name = node.member.name
            if name in target.fields:
                return target.read(name)
            if name in ("copy", "ᚳᚪᛈᛁᛁ"):
                return target.copy
            if name in ("resembles", "ᚱᛁᛋᛖᛗᛒᚢᛚ"):
                return target.resembles
            method = self._struct_method(target.struct_type, name)
            if method is not None and self._is_instance_method(method):
                return _BoundThornMethod(self, ThornFunction(method, target.struct_type.closure), target)
        if isinstance(target, ThornStructType):
            if node.member.name in ("new", "ᚾᛁᚢ"):
                return lambda *args, **kwargs: self._construct_struct(
                    target, args, kwargs, node
                )
            method = self._struct_method(target, node.member.name)
            if method is not None and not self._is_instance_method(method):
                return ThornFunction(method, target.closure)
        raise ThornRuntimeError(
            f"Value has no member '{node.member.name}'", node
        )

    def _between(self, value, lower, upper):
        lower_exclusive = isinstance(lower, str)
        upper_exclusive = isinstance(upper, str)
        try:
            lower_value = int(lower)
            upper_value = int(upper)
        except (TypeError, ValueError) as error:
            raise ThornRuntimeError("between() boundaries must contain integers") from error
        above = value > lower_value if lower_exclusive else value >= lower_value
        below = value < upper_value if upper_exclusive else value <= upper_value
        return above and below

    def _struct_method(self, struct_type, name):
        for method in struct_type.declaration.methods:
            if method.name.name == name:
                return method
        return None

    def _is_instance_method(self, method):
        return bool(
            method.parameters
            and method.parameters[0].name.name in ("self", "ᛋᛖᛚᚠ")
        )

    def _construct_struct(self, struct_type, args, kwargs, node):
        fields = struct_type.declaration.fields
        if len(args) > len(fields):
            raise ThornRuntimeError("Too many struct constructor arguments", node)
        supplied = {}
        for index, value in enumerate(args):
            supplied[fields[index].name.name] = _Value(value)
        for name, value in kwargs.items():
            if name in supplied:
                raise ThornRuntimeError(f"Field '{name}' was supplied twice", node)
            supplied[name] = _Value(value)
        unknown = set(supplied) - {field.name.name for field in fields}
        if unknown:
            raise ThornRuntimeError(f"Unknown field '{next(iter(unknown))}'", node)
        literal = StructLiteral([
            StructFieldInitializer(Identifier(name), value)
            for name, value in supplied.items()
        ], struct_type.declaration.name)
        return self._instantiate_struct(struct_type, literal)

    def _evaluate_arguments(self, arguments):
        positional, named = [], {}
        for argument in arguments:
            if isinstance(argument, NamedArgument):
                named[argument.name.name] = self.evaluate(argument.value)
            else:
                positional.append(self.evaluate(argument))
        return positional, named

    def _call_function(self, function: ThornFunction, arguments, call_node):
        positional_nodes = [arg for arg in arguments if not isinstance(arg, NamedArgument)]
        named_nodes = {
            arg.name.name: arg.value
            for arg in arguments
            if isinstance(arg, NamedArgument)
        }
        parameters = function.declaration.parameters
        if len(positional_nodes) > len(parameters):
            raise ThornRuntimeError("Too many positional arguments", call_node)
        supplied_values = {}
        for index, argument in enumerate(positional_nodes):
            parameter = parameters[index]
            supplied_values[parameter.name.name] = self.evaluate_as(
                argument, parameter.paramType
            )
        parameter_by_name = {parameter.name.name: parameter for parameter in parameters}
        for name, argument in named_nodes.items():
            parameter = parameter_by_name.get(name)
            if parameter is None:
                raise ThornRuntimeError(f"Unknown named argument '{name}'", call_node)
            supplied_values[name] = self.evaluate_as(argument, parameter.paramType)
        previous = self.environment
        previous_return_type = self.current_return_type
        self.environment = Environment(function.closure, function.declaration.name.name)
        self.current_return_type = function.declaration.returnType
        try:
            for index, parameter in enumerate(parameters):
                name = parameter.name.name
                if name in supplied_values:
                    value = supplied_values[name]
                elif not isinstance(parameter.defaultValue, Uninitialized):
                    value = self.evaluate_as(parameter.defaultValue, parameter.paramType)
                else:
                    raise ThornRuntimeError(f"Missing argument '{name}'", call_node)
                self.environment.declare(
                    name, value, declared_type=parameter.paramType
                )
            self._predeclare_declarations(function.declaration.body.statements)
            try:
                self.execute(function.declaration.body)
            except ReturnSignal as signal:
                return signal.value
            except ThornRuntimeError as error:
                error.add_frame(
                    function.declaration.name.name,
                    getattr(call_node, "span", None),
                )
                raise
            return None
        finally:
            self.environment = previous
            self.current_return_type = previous_return_type

    def execute_ReturnStatement(self, node: ReturnStatement):
        value = (
            None
            if node.value is None
            else self.evaluate_as(node.value, self.current_return_type)
        )
        raise ReturnSignal(value)

    def execute_ListLiteral(self, node: ListLiteral):
        return ThornList(self.evaluate(element) for element in node.elements)

    def execute_ArrayLiteral(self, node: ArrayLiteral):
        return ThornArray(
            (self.evaluate(element) for element in node.elements),
            warning=lambda message: self.output(f"warning: {message}\n"),
        )

    def execute_SetLiteral(self, node: SetLiteral):
        return ThornSet(self.evaluate(element) for element in node.elements)

    def execute_IndexAccess(self, node: IndexAccess):
        target = self.evaluate(node.target)
        index = self.evaluate(node.index)
        if isinstance(target, ThornPyObject):
            try:
                return python_to_thorn(target.value[thorn_to_python(index)])
            except Exception as error:
                raise ThornRuntimeError(
                    f"Python {type(error).__name__}: {error}", node
                ) from error
        try:
            return target[index]
        except (IndexError, TypeError) as error:
            raise ThornRuntimeError(str(error), node) from error

    def execute_SliceAccess(self, node: SliceAccess):
        target = self.evaluate(node.target)
        start = None if node.start is None else self.evaluate(node.start)
        end = None if node.end is None else self.evaluate(node.end)
        if isinstance(target, ThornPyObject):
            try:
                return python_to_thorn(
                    target.value[slice(thorn_to_python(start), thorn_to_python(end))]
                )
            except Exception as error:
                raise ThornRuntimeError(
                    f"Python {type(error).__name__}: {error}", node
                ) from error
        if isinstance(target, ThornCollection):
            return target.sliced(start, end)
        return target[start:end]


class _Value(Node):
    def __init__(self, value):
        self.value = value


_MUTATING_CONVERSIONS = {
    alias: canonical
    for canonical, aliases in {
        "to_int": ("to_int", "ᛏᚣ_ᛁᚾᛏ"),
        "to_char": ("to_char", "ᛏᚣ_ᚳᚻᚪᚱ"),
        "to_str": ("to_str", "ᛏᚣ_ᛋᛏᚱ"),
        "to_float": ("to_float", "ᛏᚣ_ᚠᛚᚩᛏ"),
        "to_bool": ("to_bool", "ᛏᚣ_ᛒᚣᛚ"),
        "to_list": ("to_list", "ᛏᚣ_ᛚᛁᛋᛏ"),
        "to_arr": ("to_arr", "ᛏᚣ_ᚪᚱ"),
    }.items()
    for alias in aliases
}


class _BoundThornMethod:
    def __init__(self, interpreter, function, receiver):
        self.interpreter = interpreter
        self.function = function
        self.receiver = receiver

    def call(self, arguments, call_node):
        declaration = self.function.declaration
        if not declaration.parameters:
            raise ThornRuntimeError("Instance method has no self parameter", call_node)
        self_argument = _Value(self.receiver)
        return self.interpreter._call_function(
            self.function, [self_argument, *arguments], call_node
        )
