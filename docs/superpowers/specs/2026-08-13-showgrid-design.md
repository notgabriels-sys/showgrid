# Showgrid design

## Purpose

Showgrid is an offline live-show planning tool. It checks a declared
`show.toml` for internal consistency and turns it into a compact set of
show-day documents: an artist/show card, technical brief, time-coded run
sheet, and a checklist that makes live readiness explicit.

It supports artist-side preparation and clear venue communication. It does not
contact a promoter or venue, inspect equipment, send a rider, transfer a
showfile, or claim that any planned item is actually confirmed.

## Commands

```text
showgrid check SHOW_TOML [--json]
showgrid build SHOW_TOML --output OUTPUT_DIRECTORY
```

`check` is read-only. `build` validates first and creates a new output
directory only when the declared plan is internally consistent. Existing output
directories are never replaced.

## Input shape

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
offset = "00:00"
action = "Start set"
owner = "Artist"
```

`requirements_basis` is mandatory: the output must preserve whether a plan is
confirmed in writing or is provisional. Technical details are declared free
text except for output count; Showgrid never invents a universal rider.

## Validation

- Artist, title, requirement basis, technical connection/monitor/power text,
  and gear name/role cannot be blank.
- Optional date must be a valid ISO date; optional timezone must be a valid
  IANA timezone; set start must be `HH:MM`.
- Set duration and output count must be positive integers.
- At least one declared gear item is required. Critical gear must have an
  explicit backup plan; noncritical gear may omit one.
- Duplicate gear names are rejected after whitespace and case normalisation.
- Optional cues must have `MM:SS` or `HH:MM:SS` offsets within the planned set,
  plus nonblank action and owner text.

## Build output

A successful build produces:

- `SHOW_CARD.md` - concise declared event and set summary.
- `TECHNICAL_BRIEF.md` - artist-side technical details and declared gear.
- `RUN_SHEET.md` - planned clock times derived from set start and cue offsets.
- `SHOWDAY_CHECKLIST.md` - external-evidence gates, initially `UNVERIFIED`.
- `manifest.json` - portable machine-readable source and output record.

No generated file uses absolute host paths or claims it has verified venue,
travel, equipment, backup media, soundcheck, performance, transfer, or public
event state.

## Evidence boundary

All outputs begin with `DECLARED PLAN - SHOW READINESS UNVERIFIED`. A clean
local check proves only that a plan is internally consistent. The show-day
checklist makes the missing proofs visible rather than guessing at them.

## Deliberate exclusions

- No calendar, booking, email, messaging, payment, ticketing, or social-media
  integration.
- No audio file, project-file, laptop, USB, hardware, or venue inspection.
- No universal I/O, monitoring, power, set length, or backup requirement.
- No claim of a performance, audience, promoter confirmation, or actual show
  completion.
