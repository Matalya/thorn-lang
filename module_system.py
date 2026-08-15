from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from lexer import Lexer
from parser import Parser, TokenStream
from Token import TokenKind as TK
from th_ast import (
    EnumDeclaration,
    FromImportStatement,
    FunctionDeclaration,
    ImportStatement,
    NamedTypeDeclaration,
    Program,
    VarDeclaration,
)
from runtime import ThornModule


class ModuleLoadError(Exception):
    pass


@dataclass
class ModuleRecord:
    name: str
    path: Path
    source: str
    program: Program
    exports: set[str] = field(default_factory=set)
    analyzer: object | None = None
    semanticState: str = "new"
    runtimeState: str = "new"
    runtimeModule: ThornModule | None = None

    def valueSymbol(self, name: str):
        if name not in self.exports or self.analyzer is None:
            return None
        scope = self.analyzer.globalScope
        return scope.local(name) or scope.predeclaredFunctions.get(name)

    def typeSymbol(self, name: str):
        if name not in self.exports or self.analyzer is None:
            return None
        return self.analyzer.globalScope.localType(name)


class ModuleLoader:
    def __init__(
        self,
        entryPath: str | Path | None,
        *,
        output=None,
        input_function=None,
    ):
        self.entryPath = (
            Path(entryPath).resolve()
            if entryPath is not None
            else None
        )
        self.root = self.entryPath.parent if self.entryPath is not None else None
        self.output = output
        self.input_function = input_function
        self.records: dict[Path, ModuleRecord] = {}
        self.semanticStack: list[ModuleRecord] = []
        self.runtimeStack: list[ModuleRecord] = []

    @staticmethod
    def parse(source: str) -> Program:
        lexer = Lexer(source)
        lexer.Tokenize()
        tokens = [
            token
            for token in lexer.tokenStream
            if token.kind != TK.COMMENT
        ]
        return Parser(TokenStream(tokens, source=source)).parse()

    @staticmethod
    def exportNames(program: Program) -> set[str]:
        exports: set[str] = set()
        for statement in program.statements:
            if isinstance(statement, VarDeclaration):
                exports.add(statement.varName.name)
            elif isinstance(statement, FunctionDeclaration):
                exports.add(statement.name.name)
            elif isinstance(statement, NamedTypeDeclaration):
                exports.add(statement.name.name)
                if isinstance(statement, EnumDeclaration):
                    exports.update(member.name.name for member in statement.members)
            elif isinstance(statement, (ImportStatement, FromImportStatement)):
                exports.add(statement.bindingName)
        return exports

    def registerEntry(self, source: str, program: Program) -> ModuleRecord:
        path = self.entryPath or Path("<memory>")
        record = ModuleRecord(
            path.stem,
            path,
            source,
            program,
            exports=self.exportNames(program),
        )
        self.records[path] = record
        return record

    def resolve(self, moduleName: str) -> Path:
        if self.root is None:
            raise ModuleLoadError(
                f"Cannot import module '{moduleName}' when executing source "
                f"without a file path."
            )

        if any(separator in moduleName for separator in (".", "/", "\\")):
            raise ModuleLoadError(
                f"Module name '{moduleName}' is invalid; native module names "
                f"must be single identifiers."
            )

        candidates = [
            (self.root / moduleName).with_suffix(suffix)
            for suffix in (".þ", ".futhorc")
        ]
        existing = [candidate.resolve() for candidate in candidates if candidate.is_file()]

        if not existing:
            expected = " or ".join(str(candidate) for candidate in candidates)
            raise ModuleLoadError(
                f"Module '{moduleName}' was not found; expected {expected}."
            )
        if len(existing) > 1:
            raise ModuleLoadError(
                f"Module '{moduleName}' is ambiguous because both "
                f"'{existing[0]}' and '{existing[1]}' exist."
            )
        return existing[0]

    def recordFor(self, moduleName: str) -> ModuleRecord:
        path = self.resolve(moduleName)
        existing = self.records.get(path)
        if existing is not None:
            return existing

        source = path.read_text(encoding="utf-8")
        program = self.parse(source)
        record = ModuleRecord(
            moduleName,
            path,
            source,
            program,
            exports=self.exportNames(program),
        )
        self.records[path] = record
        return record

    def analyzeEntry(self, record: ModuleRecord):
        return self._analyzeRecord(record)

    def loadSemantic(self, moduleName: str) -> ModuleRecord:
        record = self.recordFor(moduleName)
        self._analyzeRecord(record)
        return record

    def _analyzeRecord(self, record: ModuleRecord):
        if record.semanticState == "ready":
            return record.analyzer
        if record.semanticState == "loading":
            chain = " -> ".join(
                item.name for item in [*self.semanticStack, record]
            )
            raise ModuleLoadError(f"Circular module import detected: {chain}.")

        from semantic import SemanticAnalyzer

        record.semanticState = "loading"
        self.semanticStack.append(record)
        try:
            analyzer = SemanticAnalyzer(
                module_loader=self,
                module_path=record.path,
            )
            record.analyzer = analyzer
            issues = analyzer.analyze(record.program)
            if issues:
                rendered = "\n".join(str(issue) for issue in issues)
                raise ModuleLoadError(
                    f"Module '{record.name}' has semantic errors:\n{rendered}"
                )
            record.semanticState = "ready"
            return analyzer
        except Exception:
            if record.semanticState != "ready":
                record.semanticState = "failed"
            raise
        finally:
            self.semanticStack.pop()

    def runEntry(self, record: ModuleRecord):
        from interpreter import Interpreter

        interpreter = Interpreter(
            output=self.output,
            input_function=self.input_function,
            module_loader=self,
            module_path=record.path,
        )
        record.runtimeState = "loading"
        record.runtimeModule = ThornModule(
            record.name,
            interpreter.globals,
            record.exports,
        )
        self.runtimeStack.append(record)
        try:
            result = interpreter.run(record.program)
            record.runtimeState = "ready"
            return result
        finally:
            self.runtimeStack.pop()

    def loadRuntime(self, moduleName: str) -> ThornModule:
        record = self.recordFor(moduleName)
        if record.runtimeState == "ready":
            return record.runtimeModule
        if record.runtimeState == "loading":
            chain = " -> ".join(
                item.name for item in [*self.runtimeStack, record]
            )
            raise ModuleLoadError(f"Circular module import detected: {chain}.")

        from interpreter import Interpreter

        interpreter = Interpreter(
            output=self.output,
            input_function=self.input_function,
            module_loader=self,
            module_path=record.path,
        )
        record.runtimeState = "loading"
        record.runtimeModule = ThornModule(
            record.name,
            interpreter.globals,
            record.exports,
        )
        self.runtimeStack.append(record)
        try:
            interpreter.run(record.program)
            record.runtimeState = "ready"
            return record.runtimeModule
        except Exception:
            record.runtimeState = "failed"
            raise
        finally:
            self.runtimeStack.pop()
