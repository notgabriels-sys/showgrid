# Showgrid

Showgrid is an offline live-show planning tool. Put a declared set plan,
technical requirements, equipment/fallback plan, and time-relative cues into
one `show.toml`; check it for internal consistency; then build concise
show-day documents for your own preparation or venue-facing communication.

The output is deliberately a **plan**, not evidence that a show is ready. It
does not contact anyone, inspect equipment, send a rider, handle a booking,
transfer a showfile, or claim that a performance has happened.

## What it checks

- Required artist, show title, requirements basis, set start/duration, and
  artist-side technical fields.
- Optional ISO dates and IANA timezones.
- One or more gear items, with a nonblank fallback plan for items marked
  `critical = true`.
- Duplicate gear names after whitespace/case normalisation.
- Optional cues with valid `MM:SS` or `HH:MM:SS` offsets inside the planned set.

It does not impose universal power, I/O, monitor, backup, or set-length
requirements. The fields in your TOML are requirements you declared, so write
their actual source in `show.requirements_basis`. If they are artist-side
assumptions, say that plainly.

## Install from a checkout

```sh
uv venv .venv
uv pip install --python .venv/bin/python -e '.[dev]'
```

Or install it for regular use:

```sh
uv tool install --editable .
```

## Use

Start from [examples/show-example.toml](examples/show-example.toml) and replace
the generic data with the actual written brief.

```sh
showgrid check examples/show-example.toml
showgrid check examples/show-example.toml --json
showgrid build examples/show-example.toml --output ./delivery/showgrid-example
```

`check` is read-only. `build` refuses to replace an existing output directory
and creates these files only after the declared plan validates:

- `SHOW_CARD.md` - short declared show and set summary.
- `TECHNICAL_BRIEF.md` - declared I/O, monitoring, power, gear, and fallbacks.
- `RUN_SHEET.md` - cue offsets with planned clock times, including midnight
  rollover where needed.
- `SHOWDAY_CHECKLIST.md` - real-world evidence gates, all initially
  `UNVERIFIED`.
- `manifest.json` - portable machine-readable source and output record.

Every output begins with `DECLARED PLAN - SHOW READINESS UNVERIFIED`. A clean
local check proves only internal consistency; it does not confirm the booking,
venue, timetable, travel, hardware, backup media, soundcheck, monitoring,
performance, or post-show backup.

## Input format

```toml
[show]
artist = "Example Artist"
title = "Example Live Set"
requirements_basis = "Provisional artist-side plan - confirm with promoter and venue."
date = "2026-08-13"         # optional
venue = "Example Venue"      # optional
city = "Berlin"              # optional
timezone = "Europe/Berlin"   # optional IANA timezone
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
offset = "15:30"
action = "Check monitor balance"
owner = "Artist"
```

## Development

```sh
.venv/bin/python -m pytest -q
```

The runtime depends only on Python 3.11+ and the standard library.
