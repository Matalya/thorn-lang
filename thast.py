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
    NEG = auto()
    AND = auto()
    OR = auto()
    XOR = auto()

PRECEDENCE: list[list[Op]] = [
    [Op.POWER],
    [Op.MULT, Op.DIV, Op.MOD, Op.FLOOR_DIV],
    [Op.ADD, Op.SUB],
    [Op.EQUALS, Op.NOT_EQUAL, Op.LESS_THAN, Op.MORE_THAN, Op.LESS_EQUAL, Op.MORE_EQUAL],
    [Op.NEG],
    [Op.AND],
    [Op.OR, Op.XOR]
]

def precedence(operator: Op) -> int:
    global PRECEDENCE
    if not isinstance(operator, Op): 
        raise TypeError(f"precedence(): Expected operator type, got {type(operator)}")
    for i in range(len(PRECEDENCE)):
        if operator in PRECEDENCE[i]:
            return i
    raise ValueError("precedence(): Operator not identified")

class Node:
    pass

class Program(Node):
    def __init__(self, statements: list[Node] = []):
        self.statements: list[Node] = statements
    
    def __repr__(self, depth: int = 5):
        preview = "\n    ".join(repr(stmt) for stmt in self.statements[:depth])
        more = "..." if len(self.statements) > depth else ""
        if not self.statements:
            return "Program empty"
        else:
            return f"Program:\n    {preview}\n    {more}"
    
    def addNode(self, node: Node):
        self.statements.append(node)

############################################ NODES ############################################
class Uninitialized(Node):
    def __init__(self, type: Type = Type.UNINITIALIZED):
        self.type: Type = type
    
    def __repr__(self):
        return "<uninitialized>"
    
    def __str__(self):
        return "<uninitialized>"
UNINITIALIZED = Uninitialized()

class VarDeclaration(Node):
    def __init__(self, varType : Type, varName: str, varValue: Node = UNINITIALIZED):
        self.varType: Type = varType
        self.varName: str  = varName
        self.varValue: Node = varValue
    
    def __repr__(self):
        value = "" if self.varValue is UNINITIALIZED else f" = {self.varValue}"
        return f"varDeclaration: {self.varType.name.lower()} {self.varName}{value};"

class Literal(Node):
    def __init__(self, litType: Type, litValue: str):
        self.litType: Type = litType
        self.litValue: str = litValue
    
    def strfy(self):
        return "\"" if self.litType == Type.STR else ""
    def __repr__(self):
        return f"Literal({self.litType}:{self.strfy()}{self.litValue}{self.strfy()})"

class CST(Enum):
    """Compound String... Type?"""
    STRING_COMPONENT = auto()
    EVALUATION_COMPONENT = auto()

class stringComponent(Node):
    def __init__(self, type: CST, value: str):
        self.type: CST = type
        self.value: Literal | str = Literal(Type.STR, value) if self.type == CST.STRING_COMPONENT else value
    def __repr__(self):
        return f"{"EvalComp" if self.type == CST.EVALUATION_COMPONENT else ""}{self.value}"

class CompositeString(Node):
    def __init__(self, string: str):
        
        def show_context(string: str, index: int, padding: int = 5):
            lower = index - padding
            upper = index + padding
            if lower > 0 and upper < len(string):
                return string[lower : upper]
            else:
                return string
            
        self.components: list[stringComponent] = list()
        acc: str = str()
        evalMode: bool = False
        openbraceindex = 0
        for i in range(len(string)):
            if string[i] == "\"":
                continue
            elif string[i] == "{":
                evalMode = True
                if acc:
                    self.components.append(stringComponent(CST.STRING_COMPONENT, acc))
                acc = ""
                openbraceindex = i
            elif string[i] == "}":
                evalMode = False
                self.components.append(stringComponent(CST.EVALUATION_COMPONENT, "{" + acc + "}"))
                acc = ""
            else:
                acc += string[i]
        if acc:
            self.components.append(stringComponent(CST.STRING_COMPONENT, acc)) # assumed string cuz if it was an eval it would've gotten flushed by "}"
        if evalMode:
            raise SyntaxError(f"compositeString: Unclosed brace @ {openbraceindex}: …{show_context(string, openbraceindex)}…")
    
    def __repr__(self):
        return str(self.components)

class BinaryOp(Node):
    def __init__(self, left: str|int, op: Op, right: str|int):
        self.left: str|int = left
        self.op: Op = op
        self.right: str|int = right
    
    def __repr__(self):
        return f"binOp({self.left} {self.op} {self.right})"