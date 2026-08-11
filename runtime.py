from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import copy


UNINITIALIZED = object()


class ThornRuntimeError(Exception):
    """An execution failure, optionally tied to an AST source span."""

    def __init__(self, message: str, node=None):
        super().__init__(message)
        self.message = message
        self.span = getattr(node, "span", None)
        self.frames: list[tuple[str, Any]] = []

    def add_frame(self, name, span):
        self.frames.append((name, span))


@dataclass
class Cell:
    value: Any = UNINITIALIZED
    constant: bool = False
    declared_type: Any = None

    @property
    def initialized(self) -> bool:
        return self.value is not UNINITIALIZED


class Environment:
    def __init__(self, parent: Environment | None = None, name: str = "scope"):
        self.parent = parent
        self.name = name
        self.cells: dict[str, Cell] = {}
        self.types: dict[str, Any] = {}

    @property
    def global_environment(self) -> Environment:
        environment = self
        while environment.parent is not None:
            environment = environment.parent
        return environment

    def declare(
        self, name: str, value=UNINITIALIZED, *, constant: bool = False,
        declared_type=None
    ) -> Cell:
        if name in self.cells:
            raise ThornRuntimeError(f"Name '{name}' is already declared in this scope")
        cell = Cell(value, constant, declared_type)
        self.cells[name] = cell
        return cell

    def resolve_cell(self, name: str) -> Cell:
        if name in self.cells:
            return self.cells[name]
        if self.parent is not None:
            return self.parent.resolve_cell(name)
        raise ThornRuntimeError(f"Unknown name '{name}'")

    def read(self, name: str):
        cell = self.resolve_cell(name)
        if not cell.initialized:
            raise ThornRuntimeError(f"Variable '{name}' is uninitialized")
        return cell.value

    def assign(self, name: str, value):
        cell = self.resolve_cell(name)
        if cell.constant and cell.initialized:
            raise ThornRuntimeError(f"Cannot assign to constant '{name}'")
        cell.value = value
        return value

    def declare_type(self, name: str, value):
        if name in self.types:
            raise ThornRuntimeError(f"Type '{name}' is already declared in this scope")
        self.types[name] = value

    def resolve_type(self, name: str):
        if name in self.types:
            return self.types[name]
        if self.parent is not None:
            return self.parent.resolve_type(name)
        raise ThornRuntimeError(f"Unknown type '{name}'")


@dataclass(frozen=True)
class ThornFunction:
    declaration: Any
    closure: Environment


@dataclass
class ThornStructType:
    declaration: Any
    closure: Environment

    @property
    def name(self):
        return self.declaration.name.name


class ThornStruct:
    def __init__(self, struct_type: ThornStructType):
        self.struct_type = struct_type
        self.fields: dict[str, Cell] = {}

    def read(self, name):
        if name not in self.fields:
            raise ThornRuntimeError(
                f"Struct '{self.struct_type.name}' has no field '{name}'"
            )
        cell = self.fields[name]
        if not cell.initialized:
            raise ThornRuntimeError(f"Field '{name}' is uninitialized")
        return cell.value

    def assign(self, name, value):
        if name not in self.fields:
            raise ThornRuntimeError(
                f"Struct '{self.struct_type.name}' has no field '{name}'"
            )
        cell = self.fields[name]
        if cell.constant and cell.initialized:
            raise ThornRuntimeError(f"Cannot assign to constant field '{name}'")
        cell.value = value
        return value

    def __eq__(self, other):
        return self is other

    def copy(self):
        return copy.deepcopy(self)

    def __deepcopy__(self, memo):
        existing = memo.get(id(self))
        if existing is not None:
            return existing
        result = ThornStruct(self.struct_type)
        memo[id(self)] = result
        result.fields = {
            name: Cell(
                copy.deepcopy(cell.value, memo) if cell.initialized else UNINITIALIZED,
                cell.constant,
                cell.declared_type,
            )
            for name, cell in self.fields.items()
        }
        return result

    def resembles(self, other):
        if not isinstance(other, ThornStruct) or self.struct_type.name != other.struct_type.name:
            return False
        if self.fields.keys() != other.fields.keys():
            return False
        return all(
            self.fields[name].initialized == other.fields[name].initialized
            and (
                not self.fields[name].initialized
                or self.fields[name].value == other.fields[name].value
            )
            for name in self.fields
        )


@dataclass(frozen=True)
class ThornEnumValue:
    enum_type: "ThornEnumType"
    name: str
    raw: Any

    def __str__(self):
        return f"{self.enum_type.name}.{self.name}"


class ThornEnumType:
    def __init__(self, declaration):
        self.declaration = declaration
        self.name = declaration.name.name
        self.members: dict[str, ThornEnumValue] = {}

    def member(self, name):
        if name not in self.members:
            raise ThornRuntimeError(f"Enum '{self.name}' has no member '{name}'")
        return self.members[name]

    def from_raw(self, raw):
        for member in self.members.values():
            if member.raw == raw:
                return member
        raise ThornRuntimeError(f"Value {raw!r} is not declared by enum '{self.name}'")


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


class ThornFile:
    def __init__(self, handle, path):
        self.handle = handle
        self.path = str(path)

    def method(self, name):
        canonical = FILE_METHOD_CANONICAL.get(name)
        if canonical is None:
            raise ThornRuntimeError(f"File has no method '{name}'")
        if canonical == "closed":
            return lambda: self.handle.closed
        function = getattr(self, canonical)
        parameter_aliases = {
            "ᛋᛠᛋ": "size",
            "ᚳᚪᚾᛏᛖᚾᛏ": "content",
            "ᛚᛠᚾᛋ": "lines",
            "ᚢᚠᛋᛖᛏ": "offset",
            "ᚩᚱᛁᚷᚻᛁᚾ": "origin",
        }

        def call(*args, **kwargs):
            normalized = {
                parameter_aliases.get(key, key): value
                for key, value in kwargs.items()
            }
            return function(*args, **normalized)

        return call

    def _call(self, operation, *args):
        try:
            return getattr(self.handle, operation)(*args)
        except (OSError, ValueError, UnicodeError) as error:
            raise ThornRuntimeError(
                f"cannot {operation} file '{self.path}': {error}"
            ) from error

    def read(self, size=None):
        return self._call("read") if size is None else self._call("read", size)

    def readline(self, size=None):
        return self._call("readline") if size is None else self._call("readline", size)

    def readlines(self):
        return ThornList(self._call("readlines"), None)

    def write(self, content):
        return self._call("write", content)

    def writelines(self, lines):
        values = lines.values if isinstance(lines, ThornCollection) else lines
        self._call("writelines", values)

    def flush(self):
        self._call("flush")

    def seek(self, offset, origin=0):
        return self._call("seek", offset, origin)

    def tell(self):
        return self._call("tell")

    def close(self):
        if not self.handle.closed:
            self._call("close")

    def readable(self):
        return self._call("readable")

    def writable(self):
        return self._call("writable")

    def seekable(self):
        return self._call("seekable")


class ThornPyObject:
    """A value owned by Python and intentionally dynamic in Thorn."""

    def __init__(self, value):
        self.value = value

    @property
    def python_type_name(self):
        value_type = type(self.value)
        return f"{value_type.__module__}.{value_type.__qualname__}"

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f"pyobject({self.value!r})"

    def __bool__(self):
        return bool(self.value)

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)


def thorn_to_python(value):
    if isinstance(value, ThornPyObject):
        return value.value
    if isinstance(value, ThornArray):
        return [thorn_to_python(item) for item in value.values]
    if isinstance(value, ThornList):
        return [thorn_to_python(item) for item in value.values]
    if isinstance(value, ThornSet):
        return tuple(thorn_to_python(item) for item in value.values)
    if isinstance(value, ThornEnumValue):
        return thorn_to_python(value.raw)
    if isinstance(value, ThornStruct):
        raise ThornRuntimeError(
            "Thorn structs cannot cross into Python until struct conversion is defined"
        )
    return value


def python_to_thorn(value):
    return ThornPyObject(value)


def python_collection_item_to_thorn(value):
    if value is None or type(value) in (bool, int, float, str):
        return value
    return ThornPyObject(value)


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


COLLECTION_METHOD_ALIASES = {
    "append": ("append", "ᚢᛈᛖᚾᛞ"),
    "insert": ("insert", "ᛁᚾᛋᚢᚱᛏ"),
    "prepend": ("prepend", "ᛈᚱᛁᛈᛖᚾᛞ"),
    "replace_at": ("replace_at", "ᚱᛁᛈᛚᛠᛋ_ᚫᛏ"),
    "shorten": ("shorten", "ᛋᚻᛟᛏᛖᚾ"),
    "remove_at": ("remove_at", "ᚱᛁᛗᚣᚠ_ᚫᛏ"),
    "shave": ("shave", "ᛋᚻᛠᚠ"),
    "length": ("length", "ᛚᛖᛝᚦ"),
    "find_first": ("find_first", "ᚠᛠᚾᛞ_ᚠᚢᛋᛏ"),
    "find_nth": ("find_nth", "ᚠᛠᚾᛞ_ᚾᚦ"),
    "find_last": ("find_last", "ᚠᛠᚾᛞ_ᛚᚫᛋᛏ"),
    "locate": ("locate", "ᛚᚪᚳᛠᛏ"),
    "compress": ("compress", "ᚳᚢᛗᛈᚱᛖᛋ"),
    "copy": ("copy", "ᚳᚪᛈᛁᛁ"),
    "resize": ("resize", "ᚱᛁᛋᛠᛋ"),
    "capacity": ("capacity", "ᚳᚢᛈᛋᛁᛏᛁᛁ"),
    "fill": ("fill", "ᚠᛁᛚ"),
    "skintight": ("skintight", "ᛋᚳᛁᚾᛏᛠᛏ"),
    "shrink_to_fit": ("shrink_to_fit", "ᛋᚻᚱᛁᛝᚳ_ᛏᚣ_ᚠᛁᛏ"),
}
COLLECTION_METHOD_CANONICAL = {
    alias: canonical
    for canonical, aliases in COLLECTION_METHOD_ALIASES.items()
    for alias in aliases
}


class ThornCollection:
    kind = "collection"

    def __init__(self, values=(), element_type=None):
        self.values = list(values)
        self.element_type = element_type

    def __len__(self):
        return len(self.values)

    def __iter__(self):
        return iter(self.values)

    def __getitem__(self, index):
        try:
            return self.values[index]
        except IndexError as error:
            raise ThornRuntimeError(f"{self.kind} index {index} is out of range") from error

    def __eq__(self, other):
        return type(self) is type(other) and self.values == other.values

    def __deepcopy__(self, memo):
        existing = memo.get(id(self))
        if existing is not None:
            return existing
        result = type(self)((), self.element_type)
        memo[id(self)] = result
        result.values = copy.deepcopy(self.values, memo)
        return result

    def method(self, name: str):
        canonical = COLLECTION_METHOD_CANONICAL.get(name)
        if canonical is None or not hasattr(self, canonical):
            raise ThornRuntimeError(f"{self.kind} has no method '{name}'")
        return getattr(self, canonical)

    def length(self):
        return len(self.values)

    def find_first(self, item):
        try:
            return self.values.index(item)
        except ValueError:
            return None

    def find_nth(self, item, number):
        if number < 1:
            raise ThornRuntimeError("Occurrence number must be at least 1")
        seen = 0
        for index, value in enumerate(self.values):
            if value == item:
                seen += 1
                if seen == number:
                    return index
        return None

    def find_last(self, item):
        for index in range(len(self.values) - 1, -1, -1):
            if self.values[index] == item:
                return index
        return None

    def locate(self, index):
        return self[index]

    def copy(self):
        return copy.deepcopy(self)

    def sliced(self, start, end):
        return type(self)(self.values[slice(start, end)], self.element_type)


class ThornList(ThornCollection):
    kind = "list"

    def __setitem__(self, index, value):
        try:
            self.values[index] = value
        except IndexError as error:
            raise ThornRuntimeError(f"list index {index} is out of range") from error

    def append(self, item):
        self.values.append(item)

    def insert(self, item, index):
        if index < 0 or index > len(self.values):
            raise ThornRuntimeError(f"list insertion index {index} is out of range")
        self.values.insert(index, item)

    def prepend(self, item):
        self.values.insert(0, item)

    def replace_at(self, item, index):
        previous = self[index]
        self[index] = item
        return previous

    def _amount(self, amount):
        if amount < 0 or amount > len(self.values):
            raise ThornRuntimeError(f"Removal amount {amount} is out of range")

    def shorten(self, amount=1):
        self._amount(amount)
        if amount == 0:
            return ThornList()
        removed = self.values[-amount:]
        del self.values[-amount:]
        return ThornList(removed)

    def remove_at(self, index):
        self[index]
        return self.values.pop(index)

    def shave(self, amount=1):
        self._amount(amount)
        removed = self.values[:amount]
        del self.values[:amount]
        return ThornList(removed)

    def compress(self):
        self.values[:] = [value for value in self.values if value is not None]


class ThornArray(ThornList):
    kind = "array"

    def __init__(self, values=(), capacity=None, warning=None, element_type=None):
        super().__init__(values, element_type)
        self._capacity = len(self.values) if capacity is None else capacity
        self.warning = warning
        if self._capacity < 0:
            raise ThornRuntimeError("Array capacity cannot be negative")
        if len(self.values) > self._capacity:
            self.values = self.values[:self._capacity]
            self._warn("array initializer was truncated to fit its capacity")

    def _warn(self, message):
        if self.warning is not None:
            self.warning(message)

    def __deepcopy__(self, memo):
        existing = memo.get(id(self))
        if existing is not None:
            return existing
        result = ThornArray(
            (), self._capacity, self.warning, self.element_type
        )
        memo[id(self)] = result
        result.values = copy.deepcopy(self.values, memo)
        return result

    def _ensure_space(self):
        if len(self.values) >= self._capacity:
            raise ThornRuntimeError("Array is full")

    def append(self, item):
        self._ensure_space()
        self.values.append(item)

    def insert(self, item, index):
        self._ensure_space()
        super().insert(item, index)

    def prepend(self, item):
        self._ensure_space()
        self.values.insert(0, item)

    def capacity(self):
        return self._capacity

    def resize(self, new_size):
        if new_size < 0:
            raise ThornRuntimeError("Array capacity cannot be negative")
        if new_size < len(self.values):
            del self.values[new_size:]
            self._warn("reducing array capacity truncated occupied elements")
        self._capacity = new_size

    def fill(self, value):
        self.values.extend([value] * (self._capacity - len(self.values)))

    def skintight(self):
        self._warn(
            'using internal name "skintight"; consider "shrink_to_fit" instead, weirdo'
        )
        self._capacity = len(self.values)

    def shrink_to_fit(self):
        self._capacity = len(self.values)

    def copy(self):
        return copy.deepcopy(self)

    def sliced(self, start, end):
        values = self.values[slice(start, end)]
        return ThornArray(values, len(values), self.warning, self.element_type)


class ThornSet(ThornCollection):
    """Thorn sets are ordered immutable collections that retain duplicates."""

    kind = "set"

    def sliced(self, start, end):
        return ThornSet(self.values[slice(start, end)], self.element_type)


def format_value(value) -> str:
    if value is None:
        return "nil"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, ThornArray):
        return "<" + ", ".join(format_value(item) for item in value) + ">"
    if isinstance(value, ThornList):
        return "[" + ", ".join(format_value(item) for item in value) + "]"
    if isinstance(value, ThornSet):
        return "(" + ", ".join(format_value(item) for item in value) + ")"
    if isinstance(value, ThornEnumValue):
        return str(value)
    if isinstance(value, ThornStruct):
        fields = ", ".join(
            f"{name} = {format_value(cell.value)}"
            for name, cell in value.fields.items()
            if cell.initialized
        )
        return f"{value.struct_type.name} {{ {fields} }}"
    if isinstance(value, ThornPyObject):
        return str(value.value)
    return str(value)
