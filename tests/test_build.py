from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from showgrid.build import OutputDirectoryExistsError, ValidationFailedError, build_show_documents
from showgrid.models import Gear, ShowPlan
from showgrid.parser import load_show


def test_build_show_documents_writes_portable_declared_plan_documents(
    write_show, tmp_path: Path
) -> None:
    source = write_show(_show_toml())
    output = tmp_path / "example-show"

    result = build_show_documents(load_show(source), source, output)

    assert result.output == output
    assert [path.name for path in result.files] == [
        "RUN_SHEET.md",
        "SHOW_CARD.md",
        "SHOWDAY_CHECKLIST.md",
        "TECHNICAL_BRIEF.md",
        "manifest.json",
    ]
    card = (output / "SHOW_CARD.md").read_text(encoding="utf-8")
    assert "# Example Artist - Example Live Set" in card
    assert "DECLARED PLAN - SHOW READINESS UNVERIFIED" in card
    assert "| Declared set start | 23:50 |" in card
    assert "| Planned set end | 00:50 (+1 day) |" in card
    assert "| Requirement basis | Provisional artist-side plan - confirm with promoter and venue. |" in card

    technical = (output / "TECHNICAL_BRIEF.md").read_text(encoding="utf-8")
    assert "| Outputs | 2 |" in technical
    assert "| Performance computer | Playback and live processing | Critical | Prepared fallback computer and USB export |" in technical
    assert "not confirmation that equipment, backup media, power, I/O, monitoring, or a soundcheck is available" in technical

    run_sheet = (output / "RUN_SHEET.md").read_text(encoding="utf-8")
    assert "| 00:00 | 23:50 | Start set | Artist |" in run_sheet
    assert "| 15:30 | 00:05:30 (+1 day) | Check monitor balance | Artist |" in run_sheet

    checklist = (output / "SHOWDAY_CHECKLIST.md").read_text(encoding="utf-8")
    assert "| Plan/timing confirmed directly with promoter or venue | UNVERIFIED |  |  |" in checklist
    assert "| Soundcheck or line check completed | UNVERIFIED |  |  |" in checklist
    assert "| Performance completed | UNVERIFIED |  |  |" in checklist

    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["planning_status"] == "DECLARED PLAN - SHOW READINESS UNVERIFIED"
    assert manifest["source"] == {
        "filename": "show.toml",
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }
    assert manifest["show"]["planned_set_end"] == "00:50 (+1 day)"
    assert manifest["cues"][1]["planned_clock_time"] == "00:05:30 (+1 day)"
    assert manifest["files"] == [
        "RUN_SHEET.md",
        "SHOW_CARD.md",
        "SHOWDAY_CHECKLIST.md",
        "TECHNICAL_BRIEF.md",
        "manifest.json",
    ]
    assert str(tmp_path) not in (output / "manifest.json").read_text(encoding="utf-8")


def test_build_show_documents_refuses_invalid_plans_without_creating_output(
    write_show, tmp_path: Path
) -> None:
    source = write_show(_show_toml())
    plan = load_show(source)
    invalid = ShowPlan(
        show=plan.show,
        technical=plan.technical,
        gear=(Gear("Performance computer", "Playback", True),),
        cues=plan.cues,
    )
    output = tmp_path / "invalid-show"

    with pytest.raises(ValidationFailedError, match="critical gear"):
        build_show_documents(invalid, source, output)

    assert not output.exists()


def test_build_show_documents_refuses_to_replace_an_existing_directory(
    write_show, tmp_path: Path
) -> None:
    source = write_show(_show_toml())
    output = tmp_path / "existing-show"
    output.mkdir()

    with pytest.raises(OutputDirectoryExistsError, match="refusing to replace existing output"):
        build_show_documents(load_show(source), source, output)


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
