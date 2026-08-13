from __future__ import annotations

from datetime import date

from showgrid.models import Cue, Gear, Show, ShowPlan, Technical
from showgrid.parser import load_show


def test_load_show_parses_a_declared_live_plan(write_show) -> None:
    source = write_show(
        """
[show]
artist = "Example Artist"
title = "Example Live Set"
requirements_basis = "Provisional artist-side plan - confirm with promoter and venue."
date = "2026-08-13"
venue = "Example Venue"
city = "Berlin"
timezone = "Europe/Berlin"
set_start = "23:00"
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
    )

    assert load_show(source) == ShowPlan(
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
                name="Performance computer",
                role="Playback and live processing",
                critical=True,
                backup_plan="Prepared fallback computer and USB export",
            ),
        ),
        cues=(
            Cue(offset="00:00", action="Start set", owner="Artist"),
            Cue(offset="15:30", action="Check monitor balance", owner="Artist"),
        ),
    )
