# links
https://valhyr.com/pages/rune-converter english to runes converter
https://www.harysdalvi.com/futhorc webapp runes keyboard

# Quick rundown
## Types
- `ᛁᚾᛏ`, `ᚠᛚᚩᛏ`, `ᚳᚻᚪᚱ`, `ᛋᛏᚱ`, `ᛒᚣᛚ`, `ᛖᚾᛁ`, `ᚾᛁᛚ`, `ᚢᚾᛁᚾᛁᛋᚻᚢᛚᛡᛋᛏ`
## Collections
- `ᛚᛁᛋᛏ(t) [1, 2, 3]`
- `ᚪᚱ(t, n) <1, 2, 3>`
- `ᚪᚱ(t1, t2 * count, ...) <value1, value2, ...>`
- `ᛋᛖᛏ(t) (1, 2, 3)`
- `ᛞᛁᚳᛏ(k, v) {key -> value;}`
- `ᛁᚾᚣᛗ(t) my_var = (NAME = ?value;)`
- `ᛋᛏᚱᚢᚳᛏ MyType = {?ᚳᛟᚾᛋᛏ type field = ?value;}`
## Operators
- `+`, `-`, `*`, `/`, `** ^`, `%`, `//`
- `==`, `!= ≠`, `>`, `<`, `>= ≥`, `<= ≤`
- `ᚾᛟᛏ`, `ᚫᚾᛞ`, `ᛟᚱ`, `ᛉᛟᚱ`
## Control flow
- `ᛁᚠ () {} ᛖᛚᛁᚠ () {} ᛖᛚᛋ {}`
- `ᚠᛟ (i ᚠᚱᛟᛗ a ᛏᚣ b) {}`
- `ᚠᛟᚱᛁᛁᚳᚻ (item ᛁᚾ collection) {}`
- `ᚹᛠᛚ () {}`
- `ᚢᚾᛏᛁᛚ () {}`
- `ᛒᚱᛠᚳ;`, `ᚳᚢᚾᛏᛁᚾᛄᚣ;`
## Assignment
- `?ᚾᛁᚢ ?ᚷᛚᚩᛒᚢᛚ ?ᚳᛟᚾᛋᛏ type my_var = value;`
## Returns
- `ᚱᛁᛏᚢᚱᚾ`

# Types:
- **integer**: `ᛁᚾᛏ` 1 2 5 67
- **character**: `ᚳᚻᚪᚱ` 'a' 'B' '1' '!'
- **string**: `ᛋᛏᚱ` "hello" "oh" "why me"
- **composite strings**: with a `ᚳ` prefix, you can put variables between curly brackets and they won't be treated as string literals. Example:
    ```
    ᛋᛏᚱ ah = "Hello"
    ᛈᚱᛁᚾᛏ("{ah}, world", end = " ")
    ᛈᚱᛁᚾᛏ(ᚳ"{ah}, world")
    >> {ah}, world Hello, world
    ```
  Literal portions of a composite string use the same escapes as ordinary strings, including `\n`, `\r`, `\t`, `\xNN`, and `\uNNNN`. Use `\{` and `\}` for braces that should be printed rather than interpreted as interpolation delimiters.
- **floating point number**: `ᚠᛚᚩᛏ` 1.0 2.5 0.30000002
- **boolean number**: `ᛒᚣᛚ` `ᛏᚱᚣ` `ᚠᛟᛚᛋ`
- **type-flexible**: `ᛖᚾᛁ`
- **null**, **none**, **nothing**: `ᚾᛁᛚ`
- **uninitialized**: `ᚢᚾᛁᚾᛁᛋᚻᚢᛚᛡᛋᛏ`
    - special meta-type to mark variables as uninitialized and enable special behavior and circumvent the type checker

## Boolean operations and truthiness:
Truthiness can only be accessed with the built-in `ᛒᚣᛚ()` function, that gets any data as its argument and returns its truthy value. Truthiness can otherwise not be accessed, and instead explicit boolean values must be used in logical operations.
- **Comparisons** like `==`, `<` and `>=` can take numeric values (`ᛁᚾᛏ`, `ᚠᛚᚩᛏ`), as well as boolean values `ᛏᚱᚣ` and `ᚠᛟᛚᛋ`.
- **Logic operators** like `ᚫᚾᛞ`, `ᛟᚱ` and `ᛉᛟᚱ` can only be performed on strict boolean values, or type-casted non-boolean values through the `ᛒᚣᛚ()` function.
  - `5 ᚫᚾᛞ ᚠᛟᛚᛋ` ❌
  - `ᛒᚣᛚ(5) ᚫᚾᛞ ᚠᛟᛚᛋ` ✅


## Collections:
- list: `ᛚᛁᛋᛏ(type)` [1, 2, 3] (mutable, dynamically resizable)
- array: `ᚪᚱ(t, n)` <1, 2, 3> (mutable, non-dynamically resizable)
- set: `ᛋᛖᛏ(t)` (1, 2, 3) (inmutable)
- dictionary: `ᛞᛁᚳᛏ(k, v)` `{key -> value;}` (mutable, dynamically resizable)
- item: `collection[n]`
- slicing: `collection[a:b]` (zero-index, b-exclusive)

- *mutable: can the items of the collection be changed/added upon?*
- *resizable: can the collection be dynamically resized with each insertion and deletion?\**
- *rebindable: can the variable be reassigned to something else?*
```
           |mutable|resizable|rebindable
ᛚᛁᛋᛏ       |   ✅  |   ✅   |   ✅
ᚪᚱ        |   ✅  |   ❌   |   ✅
ᛋᛖᛏ        |   ❌  |   ❌   |   ✅ 
ᛞᛁᚳᛏ       |   ✅  |   ✅   |   ✅
ᚳᛟᚾᛋᛏ ᛚᛁᛋᛏ |   ✅  |   ✅   |   ❌
ᚳᛟᚾᛋᛏ ᚪᚱ  |   ✅  |   ❌   |   ❌ 
ᚳᛟᚾᛋᛏ ᛋᛖᛏ  |   ❌  |   ❌   |   ❌
ᚳᛟᚾᛋᛏ ᛞᛁᚳᛏ |   ✅  |   ✅   |   ❌
```
\* arrays are not dynamically resizable, but they can be resized with the methods listed further down. The capacity is runtime allocation.
\* Futhorc sets are immutable, ordered collections that permit duplicate elements; they behave like immutable lists rather than mathematical sets.

## Dictionaries
Dictionaries are mutable, insertion-ordered collections of key-value pairs. Their type is `ᛞᛁᚳᛏ(K, V)`, where `K` is the key type and `V` is the value type. Dictionary literals use `->` between each key and value and semicolons between entries; the final semicolon is optional.

The ASCII type alias is `dict`. Dictionary method aliases are `length`, `get`, `has`, `remove`, `keys`, `values`, `items`, `clear`, and `copy` for `ᛚᛖᛝᚦ`, `ᚷᛖᛏ`, `ᚻᚫᛋ`, `ᚱᛁᛗᚣᚠ`, `ᚳᛁᛁᛋ`, `ᚠᚫᛚᛄᚣᛋ`, `ᛠᛏᛖᛗᛋ`, `ᚳᛚᛁᚢᚱ`, and `ᚳᚪᛈᛁ`, respectively.

```
ᛞᛁᚳᛏ(ᛋᛏᚱ | ᛁᚾᛏ, ᛁᚾᛏ) scores = {
    "Ada" -> 10;
    "Grace" -> 20;
    3 -> 30
};

ᛈᚱᛁᚾᛏ(scores["Ada"]); # 10
scores["Linus"] = 40; # creates a new entry
scores["Ada"] += 5;   # updates an existing entry
```

Direct indexing with a missing key is a runtime error. `ᚷᛖᛏ()` provides nullable or default-backed access. Dictionaries cannot be sliced. `ᚠᛟᚱᛁᛁᚳᚻ (key ᛁᚾ dictionary)` iterates keys in insertion order, and `ᛁᚾᛞᛖᛉ(key)` reports the key's insertion index within that iteration.

Keys must be hashable. Supported statically known key types are `ᛁᚾᛏ`, `ᚠᛚᚩᛏ`, `ᛋᛏᚱ`, `ᚳᚻᚪᚱ`, `ᛒᚣᛚ`, `ᚾᛁᛚ`, enum types, and `ᛈᛠᚪᛒᚷᚻᛖᚳᛏ`; unions of hashable types are also supported. `ᛖᚾᛁ` in key position means any value that is hashable at runtime, not literally every Futhorc value. Lists, arrays, sets, dictionaries, files, and structs are not valid keys. A `ᛈᛠᚪᛒᚷᚻᛖᚳᛏ` key is accepted only when its wrapped Python value is hashable.

Futhorc keeps key types distinct: `ᛏᚱᚣ`, `1`, and `1.0` may coexist as three different keys. Dictionary equality compares key-value contents and does not depend on insertion order. Reassigning an existing key does not move it to the end.

An empty dictionary may be written as `{}` when its declared variable type is a concrete `ᛞᛁᚳᛏ(K, V)`. The constructor `ᛞᛁᚳᛏ(K, V)` is unambiguous in every expression context and also creates an empty dictionary.

## Heterogeneous arrays
Heterogeneous arrays are fixed positional schemas: compact, unnamed structs whose fields are addressed by index. Every slot has its own declared type.

```
ᚪᚱ(ᛁᚾᛏ, ᛋᛏᚱ, ᛒᚣᛚ) data = <10, "hello">;

ᛁᚾᛏ number = data[0];
ᛋᛏᚱ greeting = data[1];
data[2] = ᛏᚱᚣ;
```

The schema above has capacity `3`, inferred from its three type entries. Initializers may occupy any prefix of the schema, including the empty prefix. Unoccupied slots retain their declared types but cannot be read until initialized. Assigning at `ᛚᛖᛝᚦ()` initializes the next slot; assigning beyond it is an error because heterogeneous arrays cannot contain gaps.

A type followed by `*` and a positive integer declares several consecutive slots of that type. Primitive, collection, enum, and struct types are all accepted:

```
ᚪᚱ(Person * 2, ᛁᚾᛏ, ᛋᛏᚱ * 3) record;
```

This expands to two `Person` slots, one `ᛁᚾᛏ` slot, and three `ᛋᛏᚱ` slots. Its capacity is inferred as `6`. An explicit final capacity is optional, but when supplied it must equal the expanded schema exactly:

```
ᚪᚱ(Person * 2, ᛁᚾᛏ, ᛋᛏᚱ * 3, 6) valid;
ᚪᚱ(Person * 2, ᛁᚾᛏ, ᛋᛏᚱ * 3, 5) invalid; # schema/capacity error
```

An uncounted type contributes exactly one slot. Counts must be positive. The `type * count` syntax is contextual to an array type, so names such as `Person3` remain ordinary, unambiguous type names.

A constant non-negative index has its precise positional type. A runtime-computed or negative index has the union of all types in the schema and is checked against the selected slot at runtime. Heterogeneous array schemas are part of static type identity: `ᚪᚱ(ᛁᚾᛏ, ᛋᛏᚱ)` and `ᚪᚱ(ᛋᛏᚱ, ᛁᚾᛏ)` are different types.

Operations that shift slots or alter capacity would invalidate the schema. Consequently, heterogeneous arrays support `ᛚᛖᛝᚦ`, `ᚳᚢᛈᛋᛁᛏᛁᛁ`, `ᚢᛈᛖᚾᛞ`, `ᚱᛁᛈᛚᛠᛋ_ᚫᛏ`, `ᛋᚻᛟᛏᛖᚾ`, search methods, `ᛚᚪᚳᛠᛏ`, `ᚳᚪᛈᛁ`, and `join` when every slot is textual. They do not support `ᚱᛁᛋᛠᛋ`, `ᛁᚾᛋᚢᚱᛏ`, `ᛈᚱᛁᛈᛖᚾᛞ`, `ᚱᛁᛗᚣᚠ_ᚫᛏ`, `ᛋᚻᛠᚠ`, `ᚳᚢᛗᛈᚱᛖᛋ`, `ᚠᛁᛚ`, `ᛋᚳᛁᚾᛏᛠᛏ`, or `ᛋᚻᚱᛁᛝᚳ_ᛏᚣ_ᚠᛁᛏ`. Slicing is supported when its bounds are constant non-negative integers and produces the corresponding sliced schema.

## Structs
Structs are named custom types that bundle an assortment of declared variable fields with their own types. A `ᛋᛏᚱᚢᚳᛏ` can hold data of any type. The basic structure is:
```
ᛋᛏᚱᚢᚳᛏ StructType {
  type field_name;
  type field_name = default_value;

  type func(StructType ᛋᛖᛚᚠ, type arg) {
    # func body
  }
}
```

Example:

### Declaration and instantiation
```
ᛋᛏᚱᚢᚳᛏ Person {
    ᛋᛏᚱ name;
    ᛁᚾᛏ age;
    ᛋᛏᚱ citizen;
    ᛁᚾᛏ height;
    ᚠᛚᚩᛏ weight;
    ᛚᛁᛋᛏ(ᛋᛏᚱ) interests;

    ᚾᛁᛚ grow_up(Person ᛋᛖᛚᚠ, ᛁᚾᛏ years) {
      ᛋᛖᛚᚠ.age += years;
    }

    Person whoIsOlder(Person a, Person b) {
      ᛁᚠ (a.age > b.age) {
        ᚱᛁᛏᚢᚱᚾ a;
      } ᛖᛚᛋ {
        ᚱᛁᛏᚢᚱᚾ b;
      }
    }
}

Person Lucas = {
    name = "Lucas";
    age = 17;
    citizen = "Argentine";
    height = 175;
    weight = 82.9;
    interests = ["rock", "pc gaming", "football", "girls"];
}

# in-line
func(Person {name = "Lucas"; ...})
```
Notice how the named type for the aggregated data isn't one of the contained field types but a custom-named one. This integration with the type checker is the biggest advantage structs offer.

A few ground rules to keep in consideration:
- Methods are implemented as syntax sugar over free functions. `Lucas.grow_up(5)` gets resolved to `Person::grow_up(Lucas, 5)`.
- An instance method is any function whose first parameter is `StructType ᛋᛖᛚᚠ`; the StructType is mandatory for consistency with the rest of the language, but `ᛋᛖᛚᚠ` is a reserved keyword. Otherwise, the function is considered a static method. For example, `whoIsOlder(Person a, Person b)` would be callable only as `Person.whoIsOlder(Lucas, Marcos)` instead of `Lucas.whoIsOlder(Lucas, Marcos)`.
- A bare `ᛋᛖᛚᚠ` parameter is invalid. Writing `ᚾᛁᛚ restock(ᛋᛖᛚᚠ, ᛁᚾᛏ amount) {}` produces a specific missing-type error suggesting the required form, such as `ᚾᛁᛚ restock(Product ᛋᛖᛚᚠ, ᛁᚾᛏ amount) {}`.
- Uninitialized fields with no default raises an error.
- Re-initializing fields (for example, if you defined `age` twice) raise an error
- Initializing fields not present in the definition raises an error.
- Struct literals behave as expressions and evaluate to the newly created object without requiring it to be bound to a variable.
### Accessing
```
ᛈᚱᛁᚾᛏ(Lucas.age)
ᛈᚱᛁᚾᛏ(Lucas.interests[1])
>> 17
pc gaming
```
## Printing
Printing a struct instance, interpolating it into a composite string, or converting it with `ᛋᛏᚱ()` uses a field-oriented representation:
```
StructType { fieldName = value, otherField = value }
```

Fields are printed in their declaration order. Values use their normal Futhorc display form recursively, so nested collections and structs are displayed within the containing struct. Strings are displayed without surrounding quotes.

```
ᛋᛏᚱᚢᚳᛏ Product {
    ᛋᛏᚱ name;
    ᚠᛚᚩᛏ price;
    ᛁᚾᛏ stock;
}

Product coffee = Product.ᚾᛁᚢ("Coffee", 4.5, 3);
ᛈᚱᛁᚾᛏ(coffee);

>> Product { name = Coffee, price = 4.5, stock = 3 }
```
### Default, constant and mandatory fields
```
ᛁᚾᚣᛗ Clearance = (
    LEVEL_ONE;
    LEVEL_TWO;
    LEVEL_THREE;
    LEVEL_FOUR;
    MAXIMUM_LEVEL;
)
ᛋᛏᚱᚢᚳᛏ Employee {
    ᛋᛏᚱ name;
    ᚳᛟᚾᛋᛏ ᛁᚾᛏ id;
    Clearance clearance = LEVEL_ONE;
    ᚳᛟᚾᛋᛏ ᛋᛏᚱ manual = EMPLOYEE_MANUAL;
}
Employee johnSmith = {
    name = "John Smith";
    id = 25684978
}
```

The ID cannot be changed because it's a security measure, so it's assigned as a constant. This constant, in turn, is initialized upon instanciation. Clearance level is assumed to be the lowest possible unless stated otherwise. Finally, all employees must carry the employee manual, so it is assigned automatically and cannot be reassigned.
## Built-in functions and equality
All structs come with several important functions that enable certain functionalities. 
- `StructType StructType.ᚾᛁᚢ(*args)`: creates a new instance of the struct
- `StructType structInstance.ᚳᚪᛈᛁ()`: creates a deep copy of the struct's instance
- `ᛒᚣᛚ structInstanceA.ᚱᛁᛋᛖᛗᛒᚢᛚ(StructType ᚢᚦᚢ)`: makes a deep comparison of the contents of A and B.
```
ᛋᛏᚱᚢᚳᛏ Sample {
  ᛁᚾᛏ sample;
}

Sample a = Sample.ᚾᛁᚢ(1)
Sample b = a
Sample c = a.ᚳᚪᛈᛁ()

ᛈᚱᛁᚾᛏ(a == b)         # ᛏᚱᚣ
ᛈᚱᛁᚾᛏ(a == c)         # ᚠᛟᛚᛋ
ᛈᚱᛁᚾᛏ(a.ᚱᛁᛋᛖᛗᛒᛚᛋ(c)) # ᛏᚱᚣ
```
- Equality of structs is based on memory identity (Like Python's `is` keyword).

## Enumerations
Enumerations (Abbreviated as enums) are a closed collection of discrete data instances related by their custom named type.
```
ᛁᚾᚣᛗ(ᛁᚾᛏ) Directions = (
    UP = 0;
    DOWN = 1;
    LEFT = 2;
    RIGHT = 3;
)
```
All of them have a unified type of int so they don't need to have it specified inline.

Enums support auto-incremented values. To do this, you have to not define a value on all fields, and they'll be initialized with + 1 from the previous one. By default the first field will start at 0, but you can define the initial value instead. Enums are always constants and cannot be reassigned, even with the `ᚾᛁᚢ` keyword.
```
ᛁᚾᚣᛗ(ᛁᚾᛏ) Positions = (
    FIRST = 1;
    SECOND; #2
    THIRD; #3
    FOURTH; #4
    FIFTH; #5
)

ᛁᚾᚣᛗ(ᛁᚾᛏ) Weather = (
    SUNNY; #0
    RAINY; #1
    STORMY; #2
)

ᛁᚾᚣᛗ(ᛋᛏᚱ) Color = (
    YELLOW = "yellow";
    BLACK = "black";
    GREEN = "green";
    RED = "red";
    BLUE = "blue"
)
```
In a similar vein, enums create a custom type whose valid values can be checked up against the known valid values specified at the enum definition. This way: `Weather CLOUDY = 3;` will result in an error, becaus even though it's an int as specified, it's an invalid value for the `Weather` type.

# Operators
## Arithmetic operators:
- `+`: addition
- `-`: substraction
- `*`: multiplication
- `/`: division
- `**` (`^`): exponentiation
- `%`: modulo, division reminder
- `//`: integer division, floored division

## Boolean operators:
- `==`: equals (No type coercion)
- `!=` (`≠`): does not equal (No type coercion)
- `>`: greater than
- `<`: less than
- `>=` (`≥`): greater or equal than
- `<=` (`≤`): less or equal than
```
      i|o i|o
`ᚾᛟᛏ` 1|0 0|1
       A|B|AB A|B|AB A|B|AB A|B|AB
`ᚫᚾᛞ`  0|0|0; 1|0|0; 0|1|0; 1|1|1
`ᛟᚱ`   0|0|0; 1|0|1; 0|1|1; 1|1|1
`ᛉᛟᚱ`  0|0|0; 1|0|1; 0|1|1; 1|1|0
```

# Flow control:
- `ᛁᚠ(cond){} ᛖᛚᛁᚠ(cond) {} ᛖᛚᛋ{}`
- `ᚹᛠᛚ(star/cont_cond){}` (checks bef exe)
- `ᚢᚾᛏᛁᛚ(stop_cond){}` (checks aft exe)
- `ᚠᛟ (i ᚠᚱᛟᛗ a ᛏᚣ b){}` (b-exclusive)
- `ᚠᛟᚱᛁᛁᚳᚻ(item ᛁᚾ collection){}`
- ⚠️ each item is an object with its index attached. It's not identical to `ᚠᛟ (i ᚠᚱᛟᛗ 0 ᛏᚣ ᛚᛖᛝᚦ(collection)){collection[i]}` as that simply returns the item. The object behaves otherwise like its value, except that certain functions like `ᛁᚾᛞᛖᛉ()` can extract and return the index
- `ᛒᚱᛠᚳ;` immediately exits the nearest enclosing loop.
- `ᚳᚢᚾᛏᛁᚾᛄᚣ;` skips the rest of the current iteration of the nearest enclosing loop. In an `ᚢᚾᛏᛁᛚ` loop, its stop condition is still evaluated before the next iteration.

`ᛒᚱᛠᚳ` and `ᚳᚢᚾᛏᛁᚾᛄᚣ` may only appear lexically inside a loop in the same function or method. A function declared inside a loop cannot use them to control that outer loop.

Their ASCII aliases are `break` and `continue`, respectively.

# Functions:
- `f(x)`: function `f(x)` call
- `t f(x){}`: function `f(x)` definition, with a return of type t
- `ᚱᛁᛏᚢᚱᚾ [expression]`: return statement


# Variable declarations:
- `ᛁᚾᛏ i = 5;`
- `ᚳᚻᚪᚱ c = 'c';`
- `ᛋᛏᚱ hello = "hello";`
- `ᛚᛁᛋᛏ(ᛁᚾᛏ) int_list = [1, 2, 3];`
- `ᛚᛁᛋᛏ(ᚳᚻᚪᚱ) char_list = ['h','e','l','l','o'];`
- `ᚪᚱ(ᛋᛏᚱ, 3) names = <"john", "sarah", "arthur">;`
- `ᛋᛖᛏ(ᛁᚾᛏ) magic_numbers = (35, 55, 75)`
- `ᚳᛟᚾᛋᛏ`: prevents the variable from being reassigned (Though mutable collections can still be edited)
```
ᛁᚾᛏ x;
ᛋᛏᚱ x; # this errors
```
- `ᚷᛚᚩᛒᚢᛚ`: places the variable in the global scope instead of the current local scope.
```
ᚾᛁᛚ f(){
    a += 1;
#  b += 1;
    ᛁᚾᛏ b = 6;
    ᛈᚱᛁᚾᛏ(ᚳ"b: {b}");
    ᚷᛚᚩᛒᚢᛚ ᛁᚾᛏ c = 7;
}

ᚷᛚᚩᛒᚢᛚ ᛁᚾᛏ a = 4
ᛁᚾᛏ b = 5
f()  # a becomes 5, b would error @ line 3 if it wasn't commented
ᛈᚱᛁᚾᛏ(ᚳ"{a}, {c}")
>> b: 6
5, 7
```
- the order of all three assignment keywords is `ᚾᛁᚢ ᚷᛚᚩᛒᚢᛚ ᚳᛟᚾᛋᛏ ᛁᚾᛏ var_name`.
- `ᚾᛁᚢ`: allows the programmer to redeclare variables.
```
ᛁᚾᛏ x = 5;
ᛋᛏᚱ x = "hi" # errors
ᚾᛁᚢ ᛋᛏᚱ x = "hi" # all good
```
## Scope
Futhorc uses function-level lexical scope. Function bodies create local scopes; control-flow bodies do not. Variables declared within control-flow bodies are added to the nearest containing function scope, or to the global scope when no function contains them. Their initialization remains conditional on whether execution reaches the declaration.
## `ᛖᚾᛁ`
`ᛖᚾᛁ` is close to TypeScript's `unknown`. In practice, a function with a return type of `ᛖᚾᛁ` can only be assigned to variables with a type of `ᛖᚾᛁ`, but `ᛖᚾᛁ` can take on any type. However, performing operations on an `ᛖᚾᛁ`-tagged variable requires you to narrow it down via conversion or type-checking using `is_*` functions.

# File handling
Futhorc provides Python-backed text file handling through the built-in `ᚠᛠᛚ` type. Python supplies buffering, newline conversion, character encoding, seeking, and operating-system integration, while Futhorc supplies static types and source-positioned runtime diagnostics.

Files are opened with `ᚩᛈᛖᚾ()`. Relative paths are resolved from the process working directory; absolute paths are used directly. The default encoding is UTF-8.

Printing a `ᚠᛠᛚ`, interpolating it into a composite string, or converting it with `ᛋᛏᚱ()` displays its supplied path, mode, and closed state:
```
File { path = examples/notes.txt, mode = r, closed = false }
```

Supported text modes are:
- `"r"`: read an existing file.
- `"w"`: write a file, truncating existing contents.
- `"a"`: append to the end of a file.
- `"x"`: create a new file and fail if it already exists.
- `"r+"`, `"w+"`, and `"a+"`: corresponding modes that permit both reading and writing.

Binary modes such as `"rb"` and `"wb"` are not supported because Futhorc does not yet have a `bytes` type.

Files should be closed explicitly with `ᚳᛚᚩᛋ()` when no longer needed. The interpreter also closes every remaining open file when program execution ends, including when execution ends because of a runtime error.

`ᛏᛖᛚ()` returns an opaque text-stream position. In particular, it is not guaranteed to equal a character count or UTF-8 byte count. A position returned by `ᛏᛖᛚ()` can safely be passed back to `ᛋᛁᛁᚳ()`.

Opening failures, permission errors, invalid operations, encoding failures, and operations on closed files produce Futhorc runtime errors. File contents are exchanged explicitly as strings and lists of strings.

# Native modules
Each `.futhorc` or `.þ` source file is a module. Native imports preserve Futhorc's static types across file boundaries:
```
ᛁᛗᛈᛟᚱᛏ tools;
ᛁᛗᛈᛟᚱᛏ tools ᚫᛋ t;
ᚠᚱᛟᛗ tools ᛁᛗᛈᛟᚱᛏ helper;
ᚠᚱᛟᛗ tools ᛁᛗᛈᛟᚱᛏ helper ᚫᛋ h;
```

`ᛁᛗᛈᛟᚱᛏ tools;` binds the module object as the constant `tools`. `ᛁᛗᛈᛟᚱᛏ tools ᚫᛋ t;` chooses another binding name. A `ᚠᚱᛟᛗ` import binds one exported value or type directly; `ᚫᛋ` can rename it. Imported variables, functions, structs, and enums retain their declared types, so calls, assignments, member access, and nominal struct identity are still checked statically.

Module names are single identifiers and resolve to files directly inside the entry source file's directory. For example, `ᛁᛗᛈᛟᚱᛏ people;` searches for `people.þ` and `people.futhorc`. It is an error when neither candidate exists or when both exist. Dots retain their ordinary member-access meaning and are not translated into filesystem separators; use `ᚠᚱᛟᛗ world ᛁᛗᛈᛟᚱᛏ people;` to import the exported member `people` from module `world`. Native imports require execution from a source file because an in-memory source string without a path has no module root.

Every top-level variable, function, struct, enum, enum member, or imported binding is exported. Module objects expose exported values and functions through member access, such as `tools.answer` or `tools.calculate()`. Import types directly with `from tools import Result;` before using them in declarations or constructors.

A module has its own global environment and is initialized on its first executed import. The initialized module is cached, so importing it again does not rerun its top-level statements. `ᚠᚱᛟᛗ` imports capture the exported value when the import statement executes, while member access reads through the module environment. Circular imports are rejected with the import chain in the diagnostic. The English aliases are `import`, `from`, and `as`.

# Python interoperability
Futhorc can access modules from the Python environment running the interpreter. Python interoperability is an explicitly dynamic boundary: ordinary Futhorc remains statically typed, while foreign modules, callables, attributes, and results use the `ᛈᛠᚪᛒᚷᚻᛖᚳᛏ` type.

Runic aliases are `ᛈᛠᚪᛒᚷᚻᛖᚳᛏ` for `pyobject`, `ᛈᛠᛁᛗᛈᛟᚱᛏ` for `pyimport`, and `ᛗᚫᚷᚻᚣᛚ` for its `module` parameter. The native import-statement aliases are `ᛁᛗᛈᛟᚱᛏ`, `ᛈᛠᚦᚣᚾ`, and `ᚫᛋ` for `import`, `python`, and `as` respectively.

Python modules can be imported with a native runic statement:
```
ᛁᛗᛈᛟᚱᛏ ᛈᛠᚦᚣᚾ "math" ᚫᛋ math;
```
This is syntactic sugar for a statically typed `ᛈᛠᚪᛒᚷᚻᛖᚳᛏ` declaration initialized through `ᛈᛠᛁᛗᛈᛟᚱᛏ()`:
```
ᛈᛠᚪᛒᚷᚻᛖᚳᛏ math = ᛈᛠᛁᛗᛈᛟᚱᛏ("math");
```
The module name must be a string literal and `ᚫᛋ` must provide a normal Futhorc identifier. The binding follows ordinary Futhorc declaration and function-level scope rules. Importing a missing module produces the same source-positioned runtime error as `ᛈᛠᛁᛗᛈᛟᚱᛏ()`.

`ᛈᛠᛁᛗᛈᛟᚱᛏ()` uses Python's normal module discovery rules and therefore sees the standard library and packages installed in the active Python environment. A `ᛈᛠᚪᛒᚷᚻᛖᚳᛏ` supports dynamic member access, calls with positional or named arguments, indexing, slicing, and iteration through `ᚠᛟᚱᛁᛁᚳᚻ`. Each such operation has static result type `ᛈᛠᚪᛒᚷᚻᛖᚳᛏ`; programs use explicit Futhorc conversions such as `ᛁᚾᛏ()`, `ᚠᛚᚩᛏ()`, `ᛋᛏᚱ()`, `ᛒᚣᛚ()`, or `ᛏᚣ_ᛚᛁᛋᛏ()` when they need an ordinary Futhorc value.

Futhorc primitives cross into Python as their corresponding Python primitives. Lists and arrays cross as copied Python lists, sets cross as copied Python tuples, dictionaries cross as copied Python dictionaries, and enums cross as their backing values. Mutating a copied collection in Python does not mutate the original Futhorc collection. If distinct Futhorc keys would collide under Python equality, such as `ᛏᚱᚣ` and `1`, conversion raises a runtime error rather than silently losing an entry. Struct conversion and callbacks from Python into Futhorc functions are not yet defined.

Python exceptions are converted into source-positioned Futhorc runtime errors containing the Python exception class and message. Python interoperability is not sandboxed: imported modules have the same filesystem, network, process, and native-extension privileges as the interpreter.

# Built-ins:
\* This documentation uses `?value` to mean "optional parameter". However, this is merely notational and is not valid Futhorc source. Parameters become optional by providing a default evaluation with `=`.

In collection method signatures, `T` represents the collection's element type. In array signatures, `N` represents runtime capacity. Array capacity is not part of static type identity: `ᚪᚱ(T, 3)` and `ᚪᚱ(T, 8)` have the same static type.

Collection indexes are zero-based. Negative indexes count backwards from the end of the collection:

```
collection[-n] == collection[collection.ᛚᛖᛝᚦ() - n]
```

For example, `collection[-1]` accesses the last item and `collection[-2]` accesses the second-to-last item. An index outside the occupied range is a runtime error.

For methods that insert at an index, `index == ᛚᛖᛝᚦ()` is valid and inserts at the end. An index greater than the collection's length is an error; insertion never creates gaps filled with `ᚾᛁᛚ`.

Search methods return `ᚾᛁᛚ` when no matching item or occurrence exists. `ᚠᛠᚾᛞ_ᚾᚦ(item, number)` uses one-based occurrence numbering: `1` means the first occurrence, `2` the second, and so on. A `number` below `1` is a runtime error.

`ᚳᚪᛈᛁ()` performs a deep copy. Nested collections and structs are recursively copied. Repeated references and cycles preserve their topology: if two references in the original point to the same object, their copies point to the same copied object rather than two independent copies.

## Non-mutating conversion functions:
- `ᛁᚾᛏ ᛁᚾᛏ(ᛖᚾᛁ ?value)`
  - Converts `value` to an integer.
  - Returns `0` if omitted.
- `ᚳᚻᚪᚱ ᚳᚻᚪᚱ(ᛖᚾᛁ ?value)`
  - Converts `value` to a character.
  - Returns `'\0'` if omitted.
- `ᛋᛏᚱ ᛋᛏᚱ(ᛖᚾᛁ ?value)`
  - Converts `value` to a string.
  - Returns `""` if omitted.
- `ᚠᛚᚩᛏ ᚠᛚᚩᛏ(ᛖᚾᛁ ?value)`
  - Converts `value` to a floating-point number.
  - Returns `0.0` if omitted.
- `ᛒᚣᛚ ᛒᚣᛚ(ᛖᚾᛁ value)`
  - Converts `value` according to its truthiness.
- `ᛚᛁᛋᛏ(T) ᛚᛁᛋᛏ(type T, ᛖᚾᛁ ?value)`
  - Converts `value` into a list whose element type is `T`.
  - Returns `[]` if `value` is omitted.
  - Invocation syntax is `ᛚᛁᛋᛏ(T, value)` or `ᛚᛁᛋᛏ(T)`.
- `ᚪᚱ(T, N) ᚪᚱ(type T, ᛖᚾᛁ ?value, ᛁᚾᛏ ?capacity)`
  - Converts `value` into an array whose element type is `T`.
  - If `capacity` is omitted and `value` is provided, capacity defaults to the resulting length.
  - If both `value` and `capacity` are omitted, returns an empty array with capacity `0`.
  - If `capacity` is greater than the resulting length, the remaining capacity consists of internal empty slots. Empty slots are not Futhorc `ᚾᛁᛚ` values and cannot be read directly.
  - If `capacity` is smaller than the number of converted elements, excess elements are truncated and a warning is emitted.
  - Invocation syntax is `ᚪᚱ(T, value, capacity)`. `ᚪᚱ(T, capacity = N)` creates an empty array with reserved capacity.
- `ᛋᛖᛏ(T) ᛋᛖᛏ(type T, ᛖᚾᛁ ?value)`
  - Converts `value` into a set whose element type is `T`.
  - Returns `()` if `value` is omitted.
  - Futhorc sets are ordered, immutable collections and may contain duplicate values.
  - Invocation syntax is `ᛋᛖᛏ(T, value)` or `ᛋᛖᛏ(T)`.
- `ᛞᛁᚳᛏ(K, V) ᛞᛁᚳᛏ(type K, type V, ᛖᚾᛁ ?value)`
  - Creates a dictionary whose keys have type `K` and values have type `V`.
  - Returns an empty dictionary if `value` is omitted.
  - Copies entries from another Futhorc dictionary or from a Python mapping held by `ᛈᛠᚪᛒᚷᚻᛖᚳᛏ`.
  - The returned dictionary is a fresh outer collection; later mutation does not affect the source.
  - Every key and value must already match its declared type. Keys must additionally be hashable.

These conversions create a fresh outer collection and never mutate the source. Futhorc collections, strings, and foreign Python iterables are copied in iteration order; a non-iterable Futhorc value becomes one element. Elements are not individually coerced and must already match `T`. Nested collection elements are checked recursively. Contained object identities are retained, making this an outer-container copy rather than the recursive deep copy performed by `ᚳᚪᛈᛁ()`.

## Mutating conversion functions
- `ᚾᛁᛚ ᛏᚣ_ᛁᚾᛏ(ᛖᚾᛁ value)`
- `ᚾᛁᛚ ᛏᚣ_ᚳᚻᚪᚱ(ᛖᚾᛁ value)`
- `ᚾᛁᛚ ᛏᚣ_ᛋᛏᚱ(ᛖᚾᛁ value)`
- `ᚾᛁᛚ ᛏᚣ_ᚠᛚᚩᛏ(ᛖᚾᛁ value)`
- `ᚾᛁᛚ ᛏᚣ_ᛒᚣᛚ(ᛖᚾᛁ value)`
- `ᚾᛁᛚ ᛏᚣ_ᛚᛁᛋᛏ(ᛖᚾᛁ value)`
- `ᚾᛁᛚ ᛏᚣ_ᚪᚱ(ᛖᚾᛁ value, ᛁᚾᛏ ?capacity)`
  - Converts `value` into an array in place.
  - If `capacity` is omitted, capacity defaults to the resulting length.
  - If `capacity` exceeds the resulting length, the remaining capacity consists of internal empty slots.
  - If `capacity` is smaller than the resulting length, excess elements are truncated and a warning is emitted.

## Verification functions
- `ᛒᚣᛚ ᛁᛋ_ᛁᚾᛏ(ᛖᚾᛁ value)`
- `ᛒᚣᛚ ᛁᛋ_ᚳᚻᚪᚱ(ᛖᚾᛁ value)`
- `ᛒᚣᛚ ᛁᛋ_ᛋᛏᚱ(ᛖᚾᛁ value)`
- `ᛒᚣᛚ ᛁᛋ_ᚠᛚᚩᛏ(ᛖᚾᛁ value)`
- `ᛒᚣᛚ ᛁᛋ_ᛒᚣᛚ(ᛖᚾᛁ value)`
- `ᛒᚣᛚ ᛁᛋ_ᛚᛁᛋᛏ(ᛖᚾᛁ value)`
- `ᛒᚣᛚ ᛁᛋ_ᚪᚱ(ᛖᚾᛁ value)`
- `ᛒᚣᛚ ᛁᛋ_ᛋᛖᛏ(ᛖᚾᛁ value)`
- `ᛒᚣᛚ is_dict(ᛖᚾᛁ value)`
- `ᛒᚣᛚ ᛁᛋ_ᛖᛗᛈᛏᛁ(ᛖᚾᛁ collec)`
  - Returns whether the collection contains no occupied elements.
  - Raises an error if `collec` is not a collection.
- `ᛒᚣᛚ ᛁᛋ_ᚠᚣᛚ(ᚪᚱ(T, N) collec)`
  - Returns whether `collec.ᛚᛖᛝᚦ() == collec.ᚳᚢᛈᛋᛁᛏᛁᛁ()`.

## Integer methods:
- `ᛒᚣᛚ ᚷᚦ(ᛁᚾᛏ value)`
  - Returns whether the integer is greater than `value`.
- `ᛒᚣᛚ ᛚᚦ(ᛁᚾᛏ value)`
  - Returns whether the integer is less than `value`.
- `ᛒᚣᛚ ᛒᛁᛏᚹᛁᛁᚾ(ᛖᚾᛁ lower, ᛖᚾᛁ upper)`
  - Returns whether the integer is between two values. If a boundary is provided as an integer, that boundary is inclusive; if it is provided as a string, that boundary is exclusive.
    ```
    5.ᛒᛁᛏᚹᛁᛁᚾ(1, 6) = [1, 6] = 1 ≤ 5 ≤ 6
    5.ᛒᛁᛏᚹᛁᛁᚾ("1", 6) = (1, 6] = 1 < 5 ≤ 6
    5.ᛒᛁᛏᚹᛁᛁᚾ(1, "6") = [1, 6) = 1 ≤ 5 < 6
    5.ᛒᛁᛏᚹᛁᛁᚾ("1", "6") = (1, 6) = 1 < 5 < 6
    ```

## String methods
- `ᛁᚾᛏ ᛚᛖᛝᚦ()`
  - Returns the number of Unicode code points in the string.
- ASCII aliases `lower`, `upper`, `strip`, `split`, `replace`, `contains`, `starts_with`, `ends_with`, `find`, and `count` have the signatures and behavior defined in the ASCII specification. Textual lists, arrays, and sets also provide the collection-owned ASCII method `join`.

## List methods
- `ᚾᛁᛚ ᚢᛈᛖᚾᛞ(T item)`
  - Adds `item` to the end of the list.
- `ᚾᛁᛚ ᛁᚾᛋᚢᚱᛏ(T item, ᛁᚾᛏ index)`
  - Adds `item` at `index` and shifts the item previously at that index and all following items one position forward.
  - `index == ᛚᛖᛝᚦ()` inserts at the end.
  - An index outside the valid insertion range is an error.
- `ᚾᛁᛚ ᛈᚱᛁᛈᛖᚾᛞ(T item)`
  - Adds `item` at the beginning of the list and shifts all existing items one position forward.
- `T ᚱᛁᛈᛚᛠᛋ_ᚫᛏ(T item, ᛁᚾᛏ index)`
  - Replaces the item at `index` with `item`.
  - Returns the previous item.
- `ᛚᛁᛋᛏ(T) ᛋᚻᛟᛏᛖᚾ(ᛁᚾᛏ amount = 1)`
  - Removes `amount` items from the end of the list.
  - Returns the removed items in their original order.
- `T ᚱᛁᛗᚣᚠ_ᚫᛏ(ᛁᚾᛏ index)`
  - Removes the item at `index` and shifts all following items one position backward.
  - Returns the removed item.
- `ᛚᛁᛋᛏ(T) ᛋᚻᛠᚠ(ᛁᚾᛏ amount = 1)`
  - Removes `amount` items from the beginning of the list.
  - Shifts the remaining items backward and returns the removed items in their original order.
- `ᛁᚾᛏ ᛚᛖᛝᚦ()`
  - Returns the number of items in the list.
- `ᛁᚾᛏ | ᚾᛁᛚ ᚠᛠᚾᛞ_ᚠᚢᛋᛏ(ᛖᚾᛁ item)`
  - Returns the index of the first occurrence of `item`.
  - Returns `ᚾᛁᛚ` if no occurrence exists.
- `ᛁᚾᛏ | ᚾᛁᛚ ᚠᛠᚾᛞ_ᚾᚦ(ᛖᚾᛁ item, ᛁᚾᛏ number)`
  - Returns the index of the specified occurrence of `item`.
  - `number` is one-based.
  - Returns `ᚾᛁᛚ` if that occurrence does not exist.
  - A `number` below `1` is an error.
- `ᛁᚾᛏ | ᚾᛁᛚ ᚠᛠᚾᛞ_ᛚᚫᛋᛏ(ᛖᚾᛁ item)`
  - Returns the index of the last occurrence of `item`.
  - Returns `ᚾᛁᛚ` if no occurrence exists.
- `T ᛚᚪᚳᛠᛏ(ᛁᚾᛏ index)`
  - Returns the item at `index`.
  - Negative indexes count backwards from the end.
- `ᚾᛁᛚ ᚳᚢᛗᛈᚱᛖᛋ()`
  - Removes all actual `ᚾᛁᛚ` values from the list while preserving the order of all remaining items.
  - On a list whose element type cannot contain `ᚾᛁᛚ`, this is normally a no-op.
    ```
    [1, 2, 3, ᚾᛁᛚ, 4, ᚾᛁᛚ, 5]
    ↓
    [1, 2, 3, 4, 5]
    ```
- `ᛚᛁᛋᛏ(T) ᚳᚪᛈᛁ()`
  - Returns a deep copy of the list.

For both `ᛋᚻᛟᛏᛖᚾ(amount)` and `ᛋᚻᛠᚠ(amount)`:
- `amount == 0` returns an empty list and does not modify the collection.
- `amount < 0` is an error.
- `amount > ᛚᛖᛝᚦ()` is an error.

## Array methods
Arrays have both a **length** and a **capacity**.

- **length** is the number of occupied elements.
- **capacity** is the number of elements the array can contain before explicit resizing is required.
- For homogeneous `ᚪᚱ(T, N)`, capacity is runtime allocation and is not part of static type identity. For heterogeneous arrays, capacity is fixed by the positional schema and the complete schema is part of static type identity.
- Unoccupied capacity consists of internal empty slots. Empty slots are not Futhorc `ᚾᛁᛚ` values and cannot be accessed as elements.
- Arrays never resize automatically. Operations that would exceed capacity produce a runtime error. Homogeneous capacity may be increased explicitly; heterogeneous capacity cannot be changed because every position has a declared type.
- Capacity changes are visible through every alias referring to the same array.
- Assigning an existing array to a declaration written with a different `N` does not resize it.

Methods that access, replace, or remove existing items require an occupied index. An index below the array's capacity may still be invalid when it refers to an empty slot.

- `ᚾᛁᛚ ᚱᛁᛋᛠᛋ(ᛁᚾᛏ new_size)`
  - Explicitly changes the array's capacity.
  - `new_size < 0` is an error.
  - `new_size == ᚳᚢᛈᛋᛁᛏᛁᛁ()` does nothing.
  - Increasing capacity creates additional internal empty slots and does not change length.
  - Reducing capacity below the current length truncates elements from the end until `ᛚᛖᛝᚦ() <= new_size` and emits a runtime warning.
  - Resizing to `0` is valid; any occupied elements are truncated with a warning.
- `ᛁᚾᛏ ᛚᛖᛝᚦ()`
  - Returns the number of occupied elements in the array.
- `ᛁᚾᛏ ᚳᚢᛈᛋᛁᛏᛁᛁ()`
  - Returns the current runtime capacity of the array.
- `ᚾᛁᛚ ᚢᛈᛖᚾᛞ(T item)`
  - Adds `item` to the end of the occupied portion of the array.
  - Raises an error if the array is full.
  - On a heterogeneous array, `item` must match the next slot's declared type.
- `ᚾᛁᛚ ᛁᚾᛋᚢᚱᛏ(T item, ᛁᚾᛏ index)`
  - Adds `item` at `index` and shifts the item previously at that index and all following occupied items one position forward.
  - `index == ᛚᛖᛝᚦ()` inserts at the end.
  - Raises an error if the array is full.
  - An index greater than the current length is an error.
- `ᚾᛁᛚ ᛈᚱᛁᛈᛖᚾᛞ(T item)`
  - Adds `item` to the beginning of the array and shifts all occupied items one position forward.
  - Raises an error if the array is full.
- `T ᚱᛁᛈᛚᛠᛋ_ᚫᛏ(T item, ᛁᚾᛏ index)`
  - Replaces the occupied item at `index` with `item`.
  - Returns the previous item.
  - Does not change length or capacity.
  - On a heterogeneous array, `item` must match the selected slot's declared type.
- `ᛚᛁᛋᛏ(T) ᛋᚻᛟᛏᛖᚾ(ᛁᚾᛏ amount = 1)`
  - Removes `amount` occupied items from the end of the array.
  - Returns the removed items as a list in their original order.
  - Does not change array capacity.
- `T ᚱᛁᛗᚣᚠ_ᚫᛏ(ᛁᚾᛏ index)`
  - Removes the occupied item at `index`, shifts all following occupied items one position backward, and leaves an empty slot at the end of the occupied portion.
  - Returns the removed item.
  - Does not change capacity.
- `ᛚᛁᛋᛏ(T) ᛋᚻᛠᚠ(ᛁᚾᛏ amount = 1)`
  - Removes `amount` occupied items from the beginning of the array.
  - Shifts the remaining occupied items backward and returns the removed items as a list in their original order.
  - Does not change array capacity.
- `ᛁᚾᛏ | ᚾᛁᛚ ᚠᛠᚾᛞ_ᚠᚢᛋᛏ(ᛖᚾᛁ item)`
  - Returns the index of the first occurrence of `item`.
  - Returns `ᚾᛁᛚ` if no occurrence exists.
- `ᛁᚾᛏ | ᚾᛁᛚ ᚠᛠᚾᛞ_ᚾᚦ(ᛖᚾᛁ item, ᛁᚾᛏ number)`
  - Returns the index of the specified occurrence of `item`.
  - `number` is one-based.
  - Returns `ᚾᛁᛚ` if that occurrence does not exist.
  - A `number` below `1` is an error.
- `ᛁᚾᛏ | ᚾᛁᛚ ᚠᛠᚾᛞ_ᛚᚫᛋᛏ(ᛖᚾᛁ item)`
  - Returns the index of the last occurrence of `item`.
  - Returns `ᚾᛁᛚ` if no occurrence exists.
- `T ᛚᚪᚳᛠᛏ(ᛁᚾᛏ index)`
  - Returns the occupied item at `index`.
  - Negative indexes count backwards from the end of the occupied elements, not from capacity.
- `ᚾᛁᛚ ᚳᚢᛗᛈᚱᛖᛋ()`
  - Removes all actual `ᚾᛁᛚ` values from the occupied portion of the array and shifts the remaining elements together while preserving their order.
  - Capacity remains unchanged.
  - Internal empty slots are not Futhorc `ᚾᛁᛚ` and are unaffected.
  - On an array whose element type cannot contain `ᚾᛁᛚ`, this is normally a no-op.
    ```
    <1, 2, 3, ᚾᛁᛚ, 4, ᚾᛁᛚ, 5>
    ↓
    <1, 2, 3, 4, 5>
    ```
- `ᚪᚱ(T, N) ᚳᚪᛈᛁ()`
  - Returns a deep copy of the array.
  - The copied array initially has the same current capacity as the source array.
- `ᚾᛁᛚ ᚠᛁᛚ(T value)`
  - Fills every currently unoccupied slot with `value`.
  - Existing occupied elements are not replaced.
  - After the operation, `ᛚᛖᛝᚦ() == ᚳᚢᛈᛋᛁᛏᛁᛁ()`.
  - If the array is already full, the operation does nothing.
    ```
    ᚪᚱ(ᛁᚾᛏ, 5) array = <1, 2, 3>
    array.ᚠᛁᛚ(1)

    >> <1, 2, 3, 1, 1>
    ```
  - A value incompatible with `T` is a type error.
- `ᚾᛁᛚ ᛋᚳᛁᚾᛏᛠᛏ()`
  - Reduces capacity until it equals length.
  - Emits the warning: `warning: using internal name "ᛋᚳᛁᚾᛏᛠᛏ". Consider "ᛋᚻᚱᛁᛝᚳ_ᛏᚣ_ᚠᛁᛏ()" instead, weirdo`.
- `ᚾᛁᛚ ᛋᚻᚱᛁᛝᚳ_ᛏᚣ_ᚠᛁᛏ()`
  - Reduces capacity until it equals length without emitting the `ᛋᚳᛁᚾᛏᛠᛏ()` warning.

For both `ᛋᚻᛟᛏᛖᚾ(amount)` and `ᛋᚻᛠᚠ(amount)`:
- `amount == 0` returns an empty list and does not modify the array.
- `amount < 0` is an error.
- `amount > ᛚᛖᛝᚦ()` is an error.

Slicing a homogeneous array produces a new array containing the selected occupied elements with capacity equal to its resulting length. Heterogeneous array slices require constant non-negative bounds and retain the corresponding portion of the positional schema, including unoccupied typed slots.

## Set methods
Futhorc sets are ordered, immutable collections. Unlike mathematical sets and sets in many other languages, Futhorc sets permit duplicate values and retain their order. Their contents cannot be added to, removed from, replaced, or reordered after construction.

A non-`ᚳᛟᚾᛋᛏ` variable containing a set may still be rebound to another set. `ᚳᛟᚾᛋᛏ ᛋᛖᛏ(T)` prevents that rebinding as well.

- `ᛁᚾᛏ ᛚᛖᛝᚦ()`
  - Returns the number of items in the set.
- `ᛁᚾᛏ | ᚾᛁᛚ ᚠᛠᚾᛞ_ᚠᚢᛋᛏ(ᛖᚾᛁ item)`
  - Returns the index of the first occurrence of `item`.
  - Returns `ᚾᛁᛚ` if no occurrence exists.
- `ᛁᚾᛏ | ᚾᛁᛚ ᚠᛠᚾᛞ_ᚾᚦ(ᛖᚾᛁ item, ᛁᚾᛏ number)`
  - Returns the index of the specified occurrence of `item`.
  - `number` is one-based.
  - Returns `ᚾᛁᛚ` if that occurrence does not exist.
  - A `number` below `1` is an error.
- `ᛁᚾᛏ | ᚾᛁᛚ ᚠᛠᚾᛞ_ᛚᚫᛋᛏ(ᛖᚾᛁ item)`
  - Returns the index of the last occurrence of `item`.
  - Returns `ᚾᛁᛚ` if no occurrence exists.
- `T ᛚᚪᚳᛠᛏ(ᛁᚾᛏ index)`
  - Returns the item at `index`.
  - Negative indexes count backwards from the end.
- `ᛋᛖᛏ(T) ᚳᚪᛈᛁ()`
  - Returns a deep copy of the set.

## Dictionary methods
- `ᛁᚾᛏ ᛚᛖᛝᚦ()`
  - Returns the number of key-value pairs.
- `V | ᚾᛁᛚ ᚷᛖᛏ(K key, V | ᚾᛁᛚ default = ᚾᛁᛚ)`
  - Returns the value associated with `key`.
  - Returns `default` when the key is absent.
- `ᛒᚣᛚ ᚻᚫᛋ(K key)`
  - Returns whether `key` exists.
- `V ᚱᛁᛗᚣᚠ(K key)`
  - Removes `key` and returns its associated value.
  - A missing key is a runtime error.
- `ᛚᛁᛋᛏ(K) ᚳᛁᛁᛋ()`
  - Returns the keys in insertion order.
- `ᛚᛁᛋᛏ(V) ᚠᚫᛚᛄᚣᛋ()`
  - Returns the values in key insertion order.
- `ᛚᛁᛋᛏ(ᚪᚱ(K | V, 2)) ᛠᛏᛖᛗᛋ()`
  - Returns the entries in insertion order as two-element arrays containing each key and value.
- `ᚾᛁᛚ ᚳᛚᛁᚢᚱ()`
  - Removes every entry.
- `ᛞᛁᚳᛏ(K, V) ᚳᚪᛈᛁ()`
  - Returns a deep copy of the dictionary.

## Functional
- `ᛁᚾᛏ ᛁᚾᛞᛖᛉ(ᛖᚾᛁ item)`
  - Extracts the index attached to an item obtained through a `ᚠᛟᚱᛁᛁᚳᚻ`.
- `ᛋᛏᚱ ᛁᚾᛈᚣᛏ(ᛋᛏᚱ ?preview)`
  - Prints the optional `preview`, then returns the contents read from standard input.
- `ᚾᛁᛚ ᛈᚱᛁᚾᛏ(ᛖᚾᛁ output, ᛋᛏᚱ end = "\n")`
  - Prints `output`.
  - `end` is appended after the output and defaults to a newline.

## File handling

- `ᚠᛠᛚ ᚩᛈᛖᚾ(ᛋᛏᚱ ᛈᚫᚦ, ᛋᛏᚱ ᛗᚩᛞ = "r", ᛋᛏᚱ ᛖᚾᚳᚩᛞᛁᛝ = "utf-8")`
  - Opens a text file. Supported modes are `r`, `w`, `a`, `x`, and their `+` variants.
  - Binary modes are unavailable until Futhorc has a `bytes` type.
- `ᛋᛏᚱ ᚠᛠᛚ.ᚱᛁᛁᛞ(ᛁᚾᛏ | ᚾᛁᛚ ᛋᛠᛋ = ᚾᛁᛚ)`
  - Reads the remaining contents, optionally limited by `ᛋᛠᛋ`.
- `ᛋᛏᚱ ᚠᛠᛚ.ᚱᛁᛁᛞᛚᛠᚾ(ᛁᚾᛏ | ᚾᛁᛚ ᛋᛠᛋ = ᚾᛁᛚ)`
  - Reads one line, optionally limited by `ᛋᛠᛋ`.
- `ᛚᛁᛋᛏ(ᛋᛏᚱ) ᚠᛠᛚ.ᚱᛁᛁᛞᛚᛠᚾᛋ()`
  - Reads all remaining lines and retains their line terminators.
- `ᛁᚾᛏ ᚠᛠᛚ.ᚹᚱᛠᛏ(ᛋᛏᚱ ᚳᚪᚾᛏᛖᚾᛏ)`
  - Writes text and returns the number of characters accepted.
- `ᚾᛁᛚ ᚠᛠᛚ.ᚹᚱᛠᛏᛚᛠᚾ(ᛚᛁᛋᛏ(ᛋᛏᚱ) ᛚᛠᚾᛋ)`
  - Writes each string exactly as supplied without inserting newlines.
- `ᚾᛁᛚ ᚠᛠᛚ.ᚠᛚᚢᛋᚻ()`
  - Flushes buffered output.
- `ᛁᚾᛏ ᚠᛠᛚ.ᛋᛁᛁᚳ(ᛁᚾᛏ ᚢᚠᛋᛖᛏ, ᛁᚾᛏ ᚩᚱᛁᚷᚻᛁᚾ = 0)`
  - Moves the stream position relative to the beginning (`0`), current position (`1`), or end (`2`), subject to text-stream restrictions.
- `ᛁᚾᛏ ᚠᛠᛚ.ᛏᛖᛚ()`
  - Returns an opaque position suitable for passing back to `ᛋᛁᛁᚳ()`.
- `ᚾᛁᛚ ᚠᛠᛚ.ᚳᛚᚩᛋ()`
  - Flushes and closes the file; closing an already closed file does nothing.
- `ᛒᚣᛚ ᚠᛠᛚ.ᚳᛚᚩᛋᛞ()`
  - Returns whether the file is closed.
- `ᛒᚣᛚ ᚠᛠᛚ.ᚱᛁᛁᛞᚢᛒᚢᛚ()`
  - Returns whether the selected mode permits reading.
- `ᛒᚣᛚ ᚠᛠᛚ.ᚹᚱᛠᛏᚢᛒᚢᛚ()`
  - Returns whether the selected mode permits writing.
- `ᛒᚣᛚ ᚠᛠᛚ.ᛋᛁᛁᚳᚢᛒᚢᛚ()`
  - Returns whether the underlying stream supports seeking.

File and encoding failures are reported as source-positioned Futhorc runtime errors.

## Python interoperability
- `ᛈᛠᚪᛒᚷᚻᛖᚳᛏ ᛈᛠᛁᛗᛈᛟᚱᛏ(ᛋᛏᚱ ᛗᚫᚷᚻᚣᛚ)`
  - Imports `ᛗᚫᚷᚻᚣᛚ` using Python's normal import system and returns the module as a foreign object.
  - English form: `ᛈᛠᚪᛒᚷᚻᛖᚳᛏ ᛈᛠᛁᛗᛈᛟᚱᛏ(ᛋᛏᚱ ᛗᚫᚷᚻᚣᛚ)`.
- `ᛁᛗᛈᛟᚱᛏ ᛈᛠᚦᚣᚾ "module" ᚫᛋ binding;`
  - Imports the Python module and declares `binding` with static type `ᛈᛠᚪᛒᚷᚻᛖᚳᛏ`.
  - Equivalent to `ᛈᛠᚪᛒᚷᚻᛖᚳᛏ binding = ᛈᛠᛁᛗᛈᛟᚱᛏ("module");`.

Operations supported by `ᛈᛠᚪᛒᚷᚻᛖᚳᛏ` values:
- `object.member`: dynamically retrieves a Python attribute and returns it as `ᛈᛠᚪᛒᚷᚻᛖᚳᛏ`.
- `object(arguments...)`: invokes a wrapped Python callable. Futhorc named arguments become Python keyword arguments.
- `object[index]`: performs Python indexing and returns `ᛈᛠᚪᛒᚷᚻᛖᚳᛏ`.
- `object[start:end]`: performs Python slicing and returns `ᛈᛠᚪᛒᚷᚻᛖᚳᛏ`.
- `ᚠᛟᚱᛁᛁᚳᚻ (item in object)`: iterates a Python iterable; each item has static type `ᛈᛠᚪᛒᚷᚻᛖᚳᛏ`.

Python return values remain `ᛈᛠᚪᛒᚷᚻᛖᚳᛏ` even when their runtime value is a Python primitive. Explicit Futhorc conversion establishes a statically known Futhorc type.
