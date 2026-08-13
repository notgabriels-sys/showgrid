"""Deterministic Markdown and JSON documents for a valid declared show plan."""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path

from .models import Cue, ShowPlan
from .validation import cue_offset_seconds


PLANNING_STATUS = "DECLARED PLAN - SHOW READINESS UNVERIFIED"
_OUTPUT_FILENAMES = (
    "RUN_SHEET.md",
    "SHOW_CARD.md",
    "SHOWDAY_CHECKLIST.md",
    "TECHNICAL_BRIEF.md",
    "manifest.json",
)


def render_show_card(plan: ShowPlan) -> str:
    """Render concise show facts as declared, never as external confirmation."""

    show = plan.show
    rows: list[tuple[str, str]] = [
        ("Artist", show.artist),
        ("Title", show.title),
    ]
    if show.date is not None:
        rows.append(("Declared date", _date_text(show.date)))
    if show.venue is not None:
        rows.append(("Declared venue", show.venue))
    if show.city is not None:
        rows.append(("Declared city", show.city))
    if show.timezone is not None:
        rows.append(("Declared timezone", show.timezone))
    rows.extend(
        [
            ("Declared set start", show.set_start),
            ("Planned set end", planned_set_end(plan)),
            ("Declared set duration", f"{show.set_duration_minutes} minutes"),
            ("Requirement basis", show.requirements_basis),
        ]
    )

    lines = [
        f"# {_markdown_cell(show.artist)} - {_markdown_cell(show.title)}",
        "",
        PLANNING_STATUS,
        "",
        "## Declared show plan",
        "",
        "| Field | Declared value |",
        "| --- | --- |",
    ]
    lines.extend(f"| {_markdown_cell(name)} | {_markdown_cell(value)} |" for name, value in rows)
    lines.extend(
        [
            "",
            "## Evidence boundary",
            "",
            "This card records a local plan. It is not confirmation of a booking, venue, timetable, travel, equipment, soundcheck, or completed performance.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_technical_brief(plan: ShowPlan) -> str:
    """Render declared technical needs and fallback planning."""

    technical = plan.technical
    lines = [
        f"# Technical brief - {_markdown_cell(plan.show.artist)}",
        "",
        PLANNING_STATUS,
        "",
        "## Declared technical requirements",
        "",
        "| Field | Declared requirement |",
        "| --- | --- |",
        f"| Outputs | {technical.outputs} |",
        f"| Output connection | {_markdown_cell(technical.output_connection)} |",
        f"| Monitoring | {_markdown_cell(technical.monitor_requirement)} |",
        f"| Power | {_markdown_cell(technical.power_requirement)} |",
        "",
        "## Declared gear and fallback plans",
        "",
        "| Item | Role | Criticality | Backup plan |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(
        "| {name} | {role} | {criticality} | {backup_plan} |".format(
            name=_markdown_cell(item.name),
            role=_markdown_cell(item.role),
            criticality="Critical" if item.critical else "Noncritical",
            backup_plan=_markdown_cell(item.backup_plan or ""),
        )
        for item in plan.gear
    )
    lines.extend(
        [
            "",
            "## Evidence boundary",
            "",
            "This is an artist-side technical plan, not confirmation that equipment, backup media, power, I/O, monitoring, or a soundcheck is available.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_run_sheet(plan: ShowPlan) -> str:
    """Render planned cue times from the declared set start and cue offsets."""

    lines = [
        f"# Run sheet - {_markdown_cell(plan.show.artist)} - {_markdown_cell(plan.show.title)}",
        "",
        PLANNING_STATUS,
        "",
        f"Declared set start: {plan.show.set_start}",
        f"Planned set end: {planned_set_end(plan)}",
        "",
        "| Offset | Planned clock time | Action | Owner |",
        "| --- | --- | --- | --- |",
    ]
    ordered_cues = sorted(
        plan.cues, key=lambda cue: cue_offset_seconds(cue.offset) or 0
    )
    if ordered_cues:
        lines.extend(
            "| {offset} | {clock_time} | {action} | {owner} |".format(
                offset=_markdown_cell(cue.offset),
                clock_time=_markdown_cell(planned_cue_time(plan, cue)),
                action=_markdown_cell(cue.action),
                owner=_markdown_cell(cue.owner),
            )
            for cue in ordered_cues
        )
    else:
        lines.append("|  | No planned cues declared |  |  |")

    lines.extend(
        [
            "",
            "## Evidence boundary",
            "",
            "Clock times are calculated from the declared start and offsets. They are a planning aid, not a confirmed timetable or record of what occurred.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_showday_checklist() -> str:
    """Render unverified gates that need real-world evidence on show day."""

    gates = (
        "Plan/timing confirmed directly with promoter or venue",
        "Travel, entry, and load-in details confirmed",
        "Critical gear and declared fallback physically present",
        "Backup media or fallback show file tested",
        "Power, I/O, and monitoring available as required",
        "Soundcheck or line check completed",
        "Performance completed",
        "Post-show files and notes backed up",
    )
    lines = [
        "# Show-day verification checklist",
        "",
        PLANNING_STATUS,
        "",
        "Use direct real-world evidence for each gate. A local Showgrid check does not change any status below.",
        "",
        "| Gate | Status | Evidence | Checked at |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(f"| {gate} | UNVERIFIED |  |  |" for gate in gates)
    return "\n".join(lines) + "\n"


def render_manifest(plan: ShowPlan, source: Path) -> str:
    """Render a portable machine-readable record without absolute host paths."""

    manifest = {
        "cues": [
            {
                "action": cue.action,
                "offset": cue.offset,
                "offset_seconds": cue_offset_seconds(cue.offset),
                "owner": cue.owner,
                "planned_clock_time": planned_cue_time(plan, cue),
            }
            for cue in sorted(plan.cues, key=lambda cue: cue_offset_seconds(cue.offset) or 0)
        ],
        "files": list(_OUTPUT_FILENAMES),
        "gear": [
            {
                "backup_plan": item.backup_plan,
                "critical": item.critical,
                "name": item.name,
                "role": item.role,
            }
            for item in plan.gear
        ],
        "planning_status": PLANNING_STATUS,
        "schema_version": 1,
        "show": {
            "artist": plan.show.artist,
            "city": plan.show.city,
            "date": _date_text(plan.show.date) if plan.show.date is not None else None,
            "planned_set_end": planned_set_end(plan),
            "requirements_basis": plan.show.requirements_basis,
            "set_duration_minutes": plan.show.set_duration_minutes,
            "set_start": plan.show.set_start,
            "timezone": plan.show.timezone,
            "title": plan.show.title,
            "venue": plan.show.venue,
        },
        "source": {"filename": source.name, "sha256": _sha256(source)},
        "technical": {
            "monitor_requirement": plan.technical.monitor_requirement,
            "output_connection": plan.technical.output_connection,
            "outputs": plan.technical.outputs,
            "power_requirement": plan.technical.power_requirement,
        },
    }
    return json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def planned_set_end(plan: ShowPlan) -> str:
    """Return the planned end time implied by declared start and duration."""

    return _format_clock_time(
        _show_start_seconds(plan) + plan.show.set_duration_minutes * 60
    )


def planned_cue_time(plan: ShowPlan, cue: Cue) -> str:
    """Return the clock time implied by a valid declared cue offset."""

    seconds = cue_offset_seconds(cue.offset)
    if seconds is None:  # Defensive only: builds run after validation.
        raise ValueError(f"invalid cue offset: {cue.offset}")
    return _format_clock_time(_show_start_seconds(plan) + seconds)


def _show_start_seconds(plan: ShowPlan) -> int:
    hours, minutes = (int(value) for value in plan.show.set_start.split(":"))
    return hours * 3600 + minutes * 60


def _format_clock_time(total_seconds: int) -> str:
    day_offset, seconds_in_day = divmod(total_seconds, 24 * 60 * 60)
    hours, remainder = divmod(seconds_in_day, 60 * 60)
    minutes, seconds = divmod(remainder, 60)
    clock = f"{hours:02d}:{minutes:02d}"
    if seconds:
        clock += f":{seconds:02d}"
    if day_offset:
        suffix = "day" if day_offset == 1 else "days"
        clock += f" (+{day_offset} {suffix})"
    return clock


def _date_text(value: date | str) -> str:
    return value.isoformat() if isinstance(value, date) else value


def _markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def _sha256(source: Path) -> str:
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()
