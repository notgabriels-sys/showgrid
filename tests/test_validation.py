from __future__ import annotations

from datetime import date

from showgrid.models import Cue, Gear, Show, ShowPlan, Technical
from showgrid.validation import validate_show


def test_validate_show_accepts_an_internally_consistent_declared_plan() -> None:
    assert validate_show(_valid_plan()).errors == ()


def test_validate_show_reports_invalid_show_and_technical_fields() -> None:
    plan = ShowPlan(
        show=Show(
            artist="  ",
            title="Example Live Set",
            requirements_basis="",
            date="2026-02-30",
            timezone="Mars/Nowhere",
            set_start="24:00",
            set_duration_minutes=0,
        ),
        technical=Technical(
            outputs=0,
            output_connection=" ",
            monitor_requirement="",
            power_requirement="  ",
        ),
        gear=(),
    )

    assert validate_show(plan).errors == (
        "show.artist must not be blank",
        "show.requirements_basis must not be blank",
        "show.date must be a valid ISO 8601 date (YYYY-MM-DD)",
        "show.timezone must be a valid IANA timezone",
        "show.set_start must use HH:MM from 00:00 through 23:59",
        "show.set_duration_minutes must be a positive integer",
        "technical.outputs must be a positive integer",
        "technical.output_connection must not be blank",
        "technical.monitor_requirement must not be blank",
        "technical.power_requirement must not be blank",
        "at least one [[gear]] entry is required",
    )


def test_validate_show_requires_backup_plans_for_critical_gear_and_valid_cues() -> None:
    plan = ShowPlan(
        show=_valid_plan().show,
        technical=_valid_plan().technical,
        gear=(
            Gear("Performance   computer", "Playback", True, " "),
            Gear("performance computer", "Fallback", False),
        ),
        cues=(
            Cue("61:00", "Outside set", "Artist"),
            Cue("00:70", "Invalid time", "Artist"),
            Cue("00:30", " ", ""),
        ),
    )

    assert validate_show(plan).errors == (
        "critical gear 'Performance   computer' must have a nonblank backup_plan",
        "gear name is duplicated after normalization: 'performance computer'",
        "cue 1 offset 61:00 is outside the 60-minute planned set",
        "cue 2 offset must use MM:SS or HH:MM:SS with seconds from 00 to 59",
        "cue 3 action must not be blank",
        "cue 3 owner must not be blank",
    )


def _valid_plan() -> ShowPlan:
    return ShowPlan(
        show=Show(
            artist="Example Artist",
            title="Example Live Set",
            requirements_basis="Provisional artist-side plan - confirm with promoter and venue.",
            date=date(2026, 8, 13),
            venue="Example Venue",
            city="Berlin",
            timezone="Europe/Berlin",
            set_start="23:00",
            set_duration_minutes=60,
        ),
        technical=Technical(
            outputs=2,
            output_connection="Balanced XLR",
            monitor_requirement="Stereo booth monitoring",
            power_requirement="2 x 230 V Schuko outlets",
        ),
        gear=(
            Gear(
                "Performance computer",
                "Playback and live processing",
                True,
                "Prepared fallback computer and USB export",
            ),
        ),
        cues=(Cue("00:00", "Start set", "Artist"),),
    )
