from __future__ import annotations

import argparse
from pathlib import Path

from lexer import Lexer
from parser import Parser, TokenStream
from Token import TokenKind as TK
from runtime import ThornRuntimeError
from module_system import ModuleLoader, ModuleLoadError


SOURCE_SUFFIXES = (".þ", ".futhorc")


def thorn_source_path(value: str) -> Path:
    path = Path(value)
    if path.suffix not in SOURCE_SUFFIXES:
        raise argparse.ArgumentTypeError(
            "Futhorc source files must use the '.þ' or '.futhorc' extension"
        )
    return path


def parse_source(source: str):
    lexer = Lexer(source)
    lexer.Tokenize()
    tokens = [token for token in lexer.tokenStream if token.kind != TK.COMMENT]
    return Parser(TokenStream(tokens, source=source)).parse()


def run_source(
    source: str,
    *,
    output=None,
    input_function=None,
    source_path: str | Path | None = None,
):
    program = parse_source(source)
    loader = ModuleLoader(
        source_path,
        output=output,
        input_function=input_function,
    )
    record = loader.registerEntry(source, program)
    try:
        loader.analyzeEntry(record)
    except ModuleLoadError as error:
        raise SyntaxError(str(error)) from error
    return loader.runEntry(record)


def format_runtime_error(error: ThornRuntimeError, source: str, path: str) -> str:
    if error.span is None:
        return f"runtime error: {error.message}"
    lines = source.splitlines()

    def location(span):
        line = source.count("\n", 0, span.start) + 1
        last_newline = source.rfind("\n", 0, span.start)
        column = span.start - last_newline
        return line, column

    line, column = location(error.span)
    source_line = lines[line - 1] if line <= len(lines) else ""
    width = max(1, min(error.span.end - error.span.start, len(source_line) - column + 1))
    gutter = len(str(line))
    rendered = [
        f"runtime error: {error.message}",
        f"  --> {path}:{line}:{column}",
        f"{' ' * gutter} |",
        f"{line:>{gutter}} | {source_line}",
        f"{' ' * gutter} | {' ' * (column - 1)}{'^' * width}",
    ]
    for name, span in error.frames:
        if span is None:
            rendered.append(f"  called from {name}")
        else:
            frame_line, frame_column = location(span)
            rendered.append(
                f"  called from {name} at {path}:{frame_line}:{frame_column}"
            )
    return "\n".join(rendered)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="futhorc", description="Run a Futhorc program")
    parser.add_argument(
        "file",
        type=thorn_source_path,
        help="Futhorc source file (.þ or .futhorc)",
    )
    args = parser.parse_args(argv)
    source = args.file.read_text(encoding="utf-8")
    try:
        run_source(source, source_path=args.file)
    except ThornRuntimeError as error:
        print(format_runtime_error(error, source, str(args.file)))
        return 1
    except (SyntaxError, ValueError) as error:
        print(error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
