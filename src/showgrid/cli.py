"""Command-line interface for Showgrid's offline plan checks and builds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

from .build import OutputDirectoryExistsError, build_show_documents
from .parser import ShowFormatError, load_show
from .render import PLANNING_STATUS
from .validation import ValidationReport, validate_show


def main(argv: Sequence[str] | None = None) -> int:
    """Run a read-only plan check or build documents from a valid plan."""

    parser = _build_parser()
    arguments = parser.parse_args(argv)
    try:
        plan = load_show(arguments.show_file)
    except ShowFormatError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    report = validate_show(plan)
    if arguments.command == "check":
        return _run_check(plan, report, as_json=arguments.json)

    if not report.is_valid:
        _print_validation_errors(report)
        return 1

    try:
        result = build_show_documents(plan, arguments.show_file, arguments.output)
    except OutputDirectoryExistsError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    print(f"Built Showgrid documents: {result.output}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="showgrid",
        description="Validate a declared live-show plan and build offline show-day documents.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    check_parser = subcommands.add_parser("check", help="validate a show TOML file without writing")
    check_parser.add_argument("show_file", type=Path)
    check_parser.add_argument("--json", action="store_true", help="emit a JSON validation result")

    build_parser = subcommands.add_parser(
        "build", help="validate and write a new declared-plan document bundle"
    )
    build_parser.add_argument("show_file", type=Path)
    build_parser.add_argument("--output", type=Path, required=True)
    return parser


def _run_check(plan, report: ValidationReport, *, as_json: bool) -> int:
    if as_json:
        payload = {
            "errors": list(report.errors),
            "ok": report.is_valid,
            "planning_status": PLANNING_STATUS,
            "show": {
                "artist": plan.show.artist,
                "cues": len(plan.cues),
                "gear": len(plan.gear),
                "title": plan.show.title,
            },
        }
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    elif report.is_valid:
        gear_noun = "gear item" if len(plan.gear) == 1 else "gear items"
        cue_noun = "cue" if len(plan.cues) == 1 else "cues"
        print(
            "OK: declared show plan is internally consistent "
            f"({len(plan.gear)} {gear_noun}, {len(plan.cues)} {cue_noun})."
        )
        print(f"Planning status: {PLANNING_STATUS}.")
    else:
        _print_validation_errors(report)
    return 0 if report.is_valid else 1


def _print_validation_errors(report: ValidationReport) -> None:
    for error in report.errors:
        print(f"INVALID: {error}", file=sys.stderr)


if __name__ == "__main__":  # pragma: no cover - exercised by installed-command smoke test.
    raise SystemExit(main())
