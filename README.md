# The Futhorc Programming Language
ᚦhe result of a wild night between strong typing and ancient Anglo-Saxon runes.

---

## Description
**Futhorc** is a strongly and statically typed programming language that supports writing code in both modern ASCII and ancient Anglo-Saxon Futhorc runes. Designed to balance expressiveness with discipline, Futhorc allows you to write structured, type-safe programs that look like spells — whether you use `str` or `ᛋᛏᚱ`.

Futhorc blends the elegance of symbolic languages with the familiarity of C-style syntax, all while staying readable, logical, and fun to write. It's a language for those who still think computing is just a little bit magical.

> This project is still in active development, and you're here near the roots. Welcome.
---
## Features
- ✅ Statically and strongly typed
- ✅ Dual-script syntax: ASCII and Futhorc (ᚠᚢᚦᚩᚱᚳ)
- ✅ Full suite of primitive types: `int`, `float`, `char`, `str`, `bool`, `any`, `nil`
- ✅ Composite/interpolated strings (`c"{hello}, world"`)
- ✅ Collections: `list`, `arr`, `set`, and typed insertion-ordered `dict`
- ✅ Homogeneous arrays and fixed-schema heterogeneous arrays
- ✅ User-defined `struct`s and `enum`s
- ✅ Statically typed native modules with `import`, `from`, and `as`
- ✅ C-style control flow: `if`, `elsif`, `else`, `while`, `until`, `foreach`, `for`, `break`, `continue`
- ✅ Expression-based boolean and arithmetic operators, including symbolic runic equivalents
- ✅ Type conversion, introspection, and basic error signaling

Full grammar specs coming soon!

---
## Examples

### ASCII Version
```thorn
str greeting = "Hello, world!";
int i = 1 + 2 * 3;
if (i > 6) {
    print(greeting);
}
```
### Runic version
```thorn
ᛋᛏᚱ greeting = "Hello, world!";
ᛁᚾᛏ i = 1 + 2 * 3;
ᛁᚠ (i > 6) {
    ᛈᚱᛁᚾᛏ(greeting);
}
```
---
## Requirements

- Python 3.10+
- UTF-8 capable terminal (For proper rune display)
- A love for strong typing and strange symbols

---
## Contributing

Contributions and participation are warmly welcomed. Shoot up a message, file an issue or open up a PR. Forks are welcomed.

---
## License

The Futhorc Programming Language is provided under the MIT license. See [LICENSE](./LICENSE) for full terms.

---
## Ethics clause
Futhorc is offered freely and openly to all — but with an earnest request:
- You are **not** bestowed Futhorc in the service of hate, discrimination or violence.
- You are **not** to distribute the language, interpreter, core utilities or toolings comercially.
*The Futhorc Programming Language is for everyone — and for everyone it must remain.*
