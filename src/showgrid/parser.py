"""TOML loading for declared live-show plans."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any
import tomllib

from .models import Cue, Gear, Show, ShowPlan, Technical


class ShowFormatError(ValueError):
    """Raised when a show TOML file cannot be structurally interpreted."""


def load_show(path: str | Path) -> ShowPlan:
    """Load a show plan without changing it or implying external confirmation."""

    source = Path(path)
    try:
        data = tomllib.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ShowFormatError(f"show file does not exist: {source}") from error
    except tomllib.TOMLDecodeError as error:
        raise ShowFormatError(f"could not parse TOML in {source}: {error}") from error

    show = _required_table(data, "show")
    technical = _required_table(data, "technical")
    gear_tables = data.get("gear", [])
    cue_tables = data.get("cues", [])
    if not isinstance(gear_tables, list):
        raise ShowFormatError("gear must be declared with [[gear]] tables")
    if not isinstance(cue_tables, list):
        raise ShowFormatError("cues must be declared with [[cues]] tables")

    return ShowPlan(
        show=Show(
            artist=_required_string(show, "artist", "show"),
            title=_required_string(show, "title", "show"),
            requirements_basis=_required_string(show, "requirements_basis", "show"),
            date=_optional_date(show.get("date")),
            venue=_optional_string(show.get("venue"), "show.venue"),
            city=_optional_string(show.get("city"), "show.city"),
            timezone=_optional_string(show.get("timezone"), "show.timezone"),
            set_start=_required_string(show, "set_start", "show"),
            set_duration_minutes=_required_integer(show, "set_duration_minutes", "show"),
        ),
        technical=Technical(
            outputs=_required_integer(technical, "outputs", "technical"),
            output_connection=_required_string(technical, "output_connection", "technical"),
            monitor_requirement=_required_string(
                technical, "monitor_requirement", "technical"
            ),
            power_requirement=_required_string(technical, "power_requirement", "technical"),
        ),
        gear=tuple(_load_gear(entry, index) for index, entry in enumerate(gear_tables, 1)),
        cues=tuple(_load_cue(entry, index) for index, entry in enumerate(cue_tables, 1)),
    )


def _load_gear(entry: Any, index: int) -> Gear:
    if not isinstance(entry, dict):
        raise ShowFormatError(f"gear entry {index} must be a TOML table")
    critical = entry.get("critical")
    if not isinstance(critical, bool):
        raise ShowFormatError(f"gear entry {index}.critical must be a boolean")
    return Gear(
        name=_required_string(entry, "name", f"gear entry {index}"),
        role=_required_string(entry, "role", f"gear entry {index}"),
        critical=critical,
        backup_plan=_optional_string(entry.get("backup_plan"), f"gear entry {index}.backup_plan"),
    )


def _load_cue(entry: Any, index: int) -> Cue:
    if not isinstance(entry, dict):
        raise ShowFormatError(f"cues entry {index} must be a TOML table")
    return Cue(
        offset=_required_string(entry, "offset", f"cues entry {index}"),
        action=_required_string(entry, "action", f"cues entry {index}"),
        owner=_required_string(entry, "owner", f"cues entry {index}"),
    )


def _required_table(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name)
    if not isinstance(value, dict):
        raise ShowFormatError(f"show.toml must contain a [{name}] table")
    return value


def _required_string(table: dict[str, Any], name: str, context: str) -> str:
    value = table.get(name)
    if not isinstance(value, str):
        raise ShowFormatError(f"{context}.{name} must be a string")
    return value


def _required_integer(table: dict[str, Any], name: str, context: str) -> int:
    value = table.get(name)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ShowFormatError(f"{context}.{name} must be an integer")
    return value


def _optional_string(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ShowFormatError(f"{field_name} must be a string")
    return value


def _optional_date(value: Any) -> date | str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        raise ShowFormatError("show.date must be a date, not a date-time")
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise ShowFormatError("show.date must be an ISO 8601 date string")
    try:
        return date.fromisoformat(value)
    except ValueError:
        return value
