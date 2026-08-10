from __future__ import annotations

import ast
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
        self._install_builtins()

    def _install_builtins(self):
        builtins = {
            ("print", "ᛈᚱᛁᚾᛏ"): self._builtin_print,
            ("input", "ᛁᚾᛈᚣᛏ"): lambda preview="": self.input_function(preview),
            ("index", "ᛁᚾᛞᛖᛉ"): self._builtin_index,
            ("str", "ᛋᛏᚱ", "ᛥᚱ"): lambda value="": format_value(value),
            ("int", "ᛁᚾᛏ"): lambda value=0: int(value),
            ("float", "ᚠᛚᚩᛏ"): lambda value=0.0: float(value),
            ("bool", "ᛒᚣᛚ"): lambda value=False: bool(value),
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

    def run(self, program: Program):
        # Functions are visible throughout their containing scope.
        self._predeclare_declarations(program.statements)
        result = None
        for statement in program.statements:
            result = self.execute(statement)
        return result

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
        if isinstance(node, StructLiteral) and isinstance(expected_type, NamedType):
            runtime_type = self.environment.resolve_type(expected_type.name.name)
            if isinstance(runtime_type, ThornStructType):
                return self._instantiate_struct(runtime_type, node)
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
                value = ThornArray(value.values, node.varType.capacity, value.warning)
        name = node.varName.name
        if node.modifiers.isNew:
            target.cells[name] = Cell(value, node.modifiers.isConst)
        elif name in target.cells:
            target.cells[name].value = value
        else:
            target.declare(name, value, constant=node.modifiers.isConst)
        return None

    def execute_VarAssign(self, node: VarAssign):
        value = self.evaluate(node.value)
        self._assign_target(node.target, value)
        return value

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
            collection[self.evaluate(target.index)] = value
            return value
        if isinstance(target, MemberAccess):
            owner = self.evaluate(target.target)
            if isinstance(owner, ThornStruct):
                return owner.assign(target.member.name, value)
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
            for index, value in enumerate(self.evaluate(node.collection)):
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
                instance.fields[name] = Cell(value, field.modifiers.isConst)
                field_environment.declare(name, value)
        finally:
            self.environment = previous
        return instance

    def execute_FunctionCall(self, node: FunctionCall):
        callee = self.evaluate(node.callee)
        if isinstance(callee, ThornFunction):
            return self._call_function(callee, node.arguments, node)
        if isinstance(callee, _BoundThornMethod):
            return callee.call(node.arguments, node)
        positional, named = self._evaluate_arguments(node.arguments)
        try:
            return callee(*positional, **named)
        except (TypeError, ValueError) as error:
            raise ThornRuntimeError(str(error), node) from error

    def execute_MemberAccess(self, node: MemberAccess):
        target = self.evaluate(node.target)
        if isinstance(target, ThornCollection):
            return target.method(node.member.name)
        if isinstance(target, ThornEnumType):
            return target.member(node.member.name)
        if isinstance(target, ThornStruct):
            name = node.member.name
            if name in target.fields:
                return target.read(name)
            if name == "copy":
                return target.copy
            if name == "resembles":
                return target.resembles
            method = self._struct_method(target.struct_type, name)
            if method is not None and self._is_instance_method(method):
                return _BoundThornMethod(self, ThornFunction(method, target.struct_type.closure), target)
        if isinstance(target, ThornStructType):
            if node.member.name == "new":
                return lambda *args, **kwargs: self._construct_struct(
                    target, args, kwargs, node
                )
            method = self._struct_method(target, node.member.name)
            if method is not None and not self._is_instance_method(method):
                return ThornFunction(method, target.closure)
        raise ThornRuntimeError(
            f"Value has no member '{node.member.name}'", node
        )

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
                self.environment.declare(name, value)
            self._predeclare_declarations(function.declaration.body.statements)
            try:
                self.execute(function.declaration.body)
            except ReturnSignal as signal:
                return signal.value
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
        try:
            return self.evaluate(node.target)[self.evaluate(node.index)]
        except (IndexError, TypeError) as error:
            raise ThornRuntimeError(str(error), node) from error

    def execute_SliceAccess(self, node: SliceAccess):
        target = self.evaluate(node.target)
        start = None if node.start is None else self.evaluate(node.start)
        end = None if node.end is None else self.evaluate(node.end)
        if isinstance(target, ThornCollection):
            return target.sliced(start, end)
        return target[start:end]


class _Value(Node):
    def __init__(self, value):
        self.value = value


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
