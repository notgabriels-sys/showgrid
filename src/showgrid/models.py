"""Immutable models for a declared live-show plan."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Show:
    """The declared identity, timing, and evidence basis for one live set."""

    artist: str
    title: str
    requirements_basis: str
    date: date | str | None = None
    venue: str | None = None
    city: str | None = None
    timezone: str | None = None
    set_start: str = ""
    set_duration_minutes: int = 0


@dataclass(frozen=True)
class Technical:
    """Declared artist-side technical needs; not venue confirmation."""

    outputs: int
    output_connection: str
    monitor_requirement: str
    power_requirement: str


@dataclass(frozen=True)
class Gear:
    """A planned equipment item and, where needed, its declared fallback."""

    name: str
    role: str
    critical: bool
    backup_plan: str | None = None


@dataclass(frozen=True)
class Cue:
    """A planned, time-relative live-performance cue."""

    offset: str
    action: str
    owner: str


@dataclass(frozen=True)
class ShowPlan:
    """A complete, locally declared live-show plan."""

    show: Show
    technical: Technical
    gear: tuple[Gear, ...] = ()
    cues: tuple[Cue, ...] = ()
