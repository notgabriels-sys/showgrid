from __future__ import annotations

import json
from pathlib import Path

from showgrid.cli import main


def test_check_reports_a_valid_declared_plan_to_humans(write_show, capsys) -> None:
    source = write_show(_show_toml())

    assert main(["check", str(source)]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == (
        "OK: declared show plan is internally consistent (1 gear item, 2 cues).\n"
        "Planning status: DECLARED PLAN - SHOW READINESS UNVERIFIED.\n"
    )


def test_check_can_return_a_machine_readable_plan_result(write_show, capsys) -> None:
    source = write_show(_show_toml())

    assert main(["check", str(source), "--json"]) == 0

    assert json.loads(capsys.readouterr().out) == {
        "errors": [],
        "ok": True,
        "planning_status": "DECLARED PLAN - SHOW READINESS UNVERIFIED",
        "show": {
            "artist": "Example Artist",
            "cues": 2,
            "gear": 1,
            "title": "Example Live Set",
        },
    }


def test_check_returns_nonzero_for_an_invalid_plan(write_show, capsys) -> None:
    source = write_show(_show_toml().replace('artist = "Example Artist"', 'artist = "  "'))

    assert main(["check", str(source)]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "INVALID: show.artist must not be blank\n"


def test_build_creates_documents_after_a_successful_check(write_show, tmp_path: Path, capsys) -> None:
    source = write_show(_show_toml())
    output = tmp_path / "show-documents"

    assert main(["build", str(source), "--output", str(output)]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == f"Built Showgrid documents: {output}\n"
    assert (output / "SHOW_CARD.md").is_file()
    assert (output / "TECHNICAL_BRIEF.md").is_file()
    assert (output / "RUN_SHEET.md").is_file()
    assert (output / "SHOWDAY_CHECKLIST.md").is_file()
    assert (output / "manifest.json").is_file()


def _show_toml() -> str:
    return """
[show]
artist = "Example Artist"
title = "Example Live Set"
requirements_basis = "Provisional artist-side plan - confirm with promoter and venue."
date = "2026-08-13"
venue = "Example Venue"
city = "Berlin"
timezone = "Europe/Berlin"
set_start = "23:50"
set_duration_minutes = 60

[technical]
outputs = 2
output_connection = "Balanced XLR"
monitor_requirement = "Stereo booth monitoring"
power_requirement = "2 x 230 V Schuko outlets"

[[gear]]
name = "Performance computer"
role = "Playback and live processing"
critical = true
backup_plan = "Prepared fallback computer and USB export"

[[cues]]
offset = "00:00"
action = "Start set"
owner = "Artist"

[[cues]]
offset = "15:30"
action = "Check monitor balance"
owner = "Artist"
""".strip()
