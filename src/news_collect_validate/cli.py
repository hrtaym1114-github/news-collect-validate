"""Command-line interface."""
from __future__ import annotations
import argparse
import json
from .validate import MIN_ITEMS, validate_file, validate_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline news collection quality gate")
    parser.add_argument("mode", choices=tuple(MIN_ITEMS))
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("path", nargs="?", help="UTF-8 Markdown file")
    inputs.add_argument("--text", help="Markdown text instead of a file")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args(argv)
    result = (validate_text(args.mode, args.text) if args.text is not None
              else validate_file(args.mode, args.path))
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"{'PASS' if result['ok'] else 'FAIL'}: {result['path'] or '<text>'} ({result['mode']})")
        for problem in result['problems']:
            print(f"  - {problem}")
    return 0 if result['ok'] else 1
