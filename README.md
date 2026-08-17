# ᚠᚢᚦᚩᚱᚳ — Futhorc
**A statically and strongly typed programming language with runic aliases and a bridge to Python's ecosystem.**

Futhorc is a general-purpose interpreted programming language built as an exploration of language design, parsing, static typing, and interpretation.

Its syntax is deliberately familiar:

```futhorc
int fibonacci(int n) {
    if (n <= 1) {
        return n;
    }

    return fibonacci(n - 1) + fibonacci(n - 2);
}

print(fibonacci(10));
```

But almost the entire language also has an alternative vocabulary based on the Anglo-Saxon Futhorc:

```futhorc
ᛁᚾᛏ fibonacci(ᛁᚾᛏ n) {
    ᛁᚠ (n <= 1) {
        ᚱᛁᛏᚢᚱᚾ n;
    }

    ᚱᛁᛏᚢᚱᚾ fibonacci(n - 1) + fibonacci(n - 2);
}

ᛈᚱᛁᚾᛏ(fibonacci(10));
```

The runic syntax is not a separate dialect or preprocessor. Both forms are Futhorc and can coexist in the same source file.

## Features
Futhorc includes:

- Static, strong typing
- Primitive, union, struct, and enum types
- Functions, recursion, default and named arguments
- `if` / `elsif` / `else` conditionals
- `while`, `until`, `for`, and `foreach` loops
- Mutable lists and arrays
- Immutable ordered sets
- Typed dictionaries
- Heterogeneous arrays with statically typed positional slots
- Composite strings
- Text file I/O
- Native modules and imports
- Python interoperability
- Source-positioned diagnostics
- Full ASCII and runic vocabularies

## A little Futhorc
```futhorc
struct Product {
    str name;
    float price;
    int stock = 0;

    nil restock(Product self, int amount) {
        self.stock += amount;
    }
}

Product apple = Product.new("Apple", 1.50);
apple.restock(10);

print(c"{apple.name}: {apple.stock} in stock");
```

Collections are explicitly typed:

```futhorc
list(int) numbers = [1, 2, 3, 4];

dict(str, int) scores = {
    "Alice" -> 95;
    "Bob" -> 87;
};

arr(int, str, bool) record = <42, "Futhorc", true>;
```

Futhorc also provides union types:

```futhorc
str | nil find_name(int id) {
    if (id == 42) {
        return "Arthur";
    }

    return nil;
}
```

## Python interoperability
Futhorc can import modules from the Python environment in which it runs:

```futhorc
import python "math" as math;

float root = float(math.sqrt(81.0));

print(c"sqrt(81) = {root}");
```

Python values cross the interoperability boundary as `pyobject`s. Explicit conversion establishes an ordinary statically typed Futhorc value.

This gives Futhorc access to Python's standard library and installed packages without making ordinary Futhorc code dynamically typed.

## Native modules
Every `.þ` or `.futhorc` source file is a module.

```futhorc
import tools;
import tools as t;

from tools import helper;
from tools import Result;
```

Imported Futhorc declarations preserve their static types across module boundaries.

## Running Futhorc
Futhorc's reference implementation is written in Python.

Install the project from the repository:

```bash
python -m pip install .
```

Or install it in editable mode for development:

```bash
python -m pip install -e .
```

Then run a Futhorc program with:

```bash
futhorc program.þ
```

Both `.þ` and `.futhorc` are recognized as Futhorc source files.

## Examples
The samples page (`examples.html`) contains complete Futhorc programs, ranging from Hello World and FizzBuzz to larger examples using collections, structs, files, and Python interoperability.

## Documentation
- [Language specification](futhorc%20specs.md)
- [Runic language specification](futhorc%20runic%20specs.md)
- [Example programs](examples/)

## Implementation
The reference implementation is written in Python and follows a traditional interpreter pipeline:

```text
source
  ↓
lexer
  ↓
parser
  ↓
abstract syntax tree
  ↓
semantic analysis
  ↓
tree-walking interpreter
```

Futhorc performs semantic analysis before execution, including static type checking and name resolution.

The implementation also deliberately uses Python as a runtime substrate where appropriate, including text I/O and interoperability with Python modules.

## Status
**Futhorc 1.0 represents the first complete version of the language.**

The core grammar and semantics are considered stable. Future development may include bug fixes, improved diagnostics and tooling, standard-library additions, and backwards-compatible language extensions.

Futhorc is a hobby language. It isn't intended to replace Python, Rust, C++, or any other established language.

It exists because programming languages are interesting things to build. And because programming in runes is cool.

## License
See [LICENSE](LICENSE) for licensing information.

## Ethics clause
Futhorc is offered freely and openly to all — but with an earnest request:
- You are **not** bestowed Futhorc in the service of hate, discrimination or violence.
*The Futhorc Programming Language is for everyone — and for everyone it must remain.*
