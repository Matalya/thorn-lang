from __future__ import annotations

import argparse
from pathlib import Path

from lexer import Lexer
from parser import Parser, TokenStream
from semantic import SemanticAnalyzer
from Token import TokenKind as TK
from interpreter import Interpreter
from runtime import ThornRuntimeError


SOURCE_SUFFIXES = (".þ", ".thorn")


def thorn_source_path(value: str) -> Path:
    path = Path(value)
    if path.suffix not in SOURCE_SUFFIXES:
        raise argparse.ArgumentTypeError(
            "Thorn source files must use the '.þ' or '.thorn' extension"
        )
    return path


def parse_source(source: str):
    lexer = Lexer(source)
    lexer.Tokenize()
    tokens = [token for token in lexer.tokenStream if token.kind != TK.COMMENT]
    return Parser(TokenStream(tokens)).parse()


def run_source(source: str, *, output=None, input_function=None):
    program = parse_source(source)
    issues = SemanticAnalyzer().analyze(program)
    if issues:
        raise SyntaxError("\n".join(str(issue) for issue in issues))
    return Interpreter(
        output=output,
        input_function=input_function,
    ).run(program)


def format_runtime_error(error: ThornRuntimeError, source: str, path: str) -> str:
    if error.span is None:
        return f"runtime error: {error.message}"
    line = source.count("\n", 0, error.span.start) + 1
    last_newline = source.rfind("\n", 0, error.span.start)
    column = error.span.start - last_newline
    return f"runtime error: {error.message}\n  at {path}:{line}:{column}"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="thorn", description="Run a Thorn program")
    parser.add_argument(
        "file",
        type=thorn_source_path,
        help="Thorn source file (.þ or .thorn)",
    )
    args = parser.parse_args(argv)
    source = args.file.read_text(encoding="utf-8")
    try:
        run_source(source)
    except ThornRuntimeError as error:
        print(format_runtime_error(error, source, str(args.file)))
        return 1
    except (SyntaxError, ValueError) as error:
        print(error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
