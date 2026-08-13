"""Semantic validation for a declared live-show plan."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .models import Cue, ShowPlan


@dataclass(frozen=True)
class ValidationReport:
    """All locally detectable declared-plan problems in a stable order."""

    errors: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.errors


def validate_show(plan: ShowPlan) -> ValidationReport:
    """Validate a local plan without treating it as real-world readiness proof."""

    errors: list[str] = []
    show = plan.show
    for field_name, value in (
        ("artist", show.artist),
        ("title", show.title),
        ("requirements_basis", show.requirements_basis),
    ):
        if not _is_nonblank_string(value):
            errors.append(f"show.{field_name} must not be blank")

    for field_name, value in (
        ("venue", show.venue),
        ("city", show.city),
        ("timezone", show.timezone),
    ):
        if value is not None and not _is_nonblank_string(value):
            errors.append(f"show.{field_name} must not be blank when supplied")

    if show.date is not None and not _is_valid_date(show.date):
        errors.append("show.date must be a valid ISO 8601 date (YYYY-MM-DD)")
    if _is_nonblank_string(show.timezone) and not _is_valid_timezone(show.timezone):
        errors.append("show.timezone must be a valid IANA timezone")
    if _clock_minutes(show.set_start) is None:
        errors.append("show.set_start must use HH:MM from 00:00 through 23:59")
    if not _is_positive_integer(show.set_duration_minutes):
        errors.append("show.set_duration_minutes must be a positive integer")

    technical = plan.technical
    if not _is_positive_integer(technical.outputs):
        errors.append("technical.outputs must be a positive integer")
    for field_name, value in (
        ("output_connection", technical.output_connection),
        ("monitor_requirement", technical.monitor_requirement),
        ("power_requirement", technical.power_requirement),
    ):
        if not _is_nonblank_string(value):
            errors.append(f"technical.{field_name} must not be blank")

    errors.extend(_validate_gear(plan))
    errors.extend(_validate_cues(plan))
    return ValidationReport(tuple(errors))


def cue_offset_seconds(value: object) -> int | None:
    """Return a `MM:SS` or `HH:MM:SS` offset in seconds, or ``None``."""

    if not isinstance(value, str):
        return None
    parts = value.split(":")
    if len(parts) == 2:
        minutes, seconds = parts
        if not (minutes.isdigit() and seconds.isdigit() and len(seconds) == 2):
            return None
        if int(seconds) > 59:
            return None
        return int(minutes) * 60 + int(seconds)
    if len(parts) == 3:
        hours, minutes, seconds = parts
        if not (
            hours.isdigit()
            and minutes.isdigit()
            and seconds.isdigit()
            and len(minutes) == 2
            and len(seconds) == 2
        ):
            return None
        if int(minutes) > 59 or int(seconds) > 59:
            return None
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    return None


def _validate_gear(plan: ShowPlan) -> list[str]:
    if not plan.gear:
        return ["at least one [[gear]] entry is required"]

    errors: list[str] = []
    seen_names: set[str] = set()
    for item in plan.gear:
        if not _is_nonblank_string(item.name):
            errors.append("gear name must not be blank")
        if not _is_nonblank_string(item.role):
            errors.append(f"gear '{item.name}' role must not be blank")
        if not isinstance(item.critical, bool):
            errors.append(f"gear '{item.name}' critical must be a boolean")
        elif item.critical and not _is_nonblank_string(item.backup_plan):
            errors.append(f"critical gear '{item.name}' must have a nonblank backup_plan")

        normalized_name = _normalize(item.name)
        if normalized_name:
            if normalized_name in seen_names:
                errors.append(
                    f"gear name is duplicated after normalization: '{normalized_name}'"
                )
            else:
                seen_names.add(normalized_name)
    return errors


def _validate_cues(plan: ShowPlan) -> list[str]:
    errors: list[str] = []
    maximum_offset = (
        plan.show.set_duration_minutes * 60
        if _is_positive_integer(plan.show.set_duration_minutes)
        else None
    )
    for index, cue in enumerate(plan.cues, 1):
        seconds = cue_offset_seconds(cue.offset)
        if seconds is None:
            errors.append(
                f"cue {index} offset must use MM:SS or HH:MM:SS with seconds from 00 to 59"
            )
        elif maximum_offset is not None and seconds > maximum_offset:
            errors.append(
                f"cue {index} offset {cue.offset} is outside the "
                f"{plan.show.set_duration_minutes}-minute planned set"
            )
        if not _is_nonblank_string(cue.action):
            errors.append(f"cue {index} action must not be blank")
        if not _is_nonblank_string(cue.owner):
            errors.append(f"cue {index} owner must not be blank")
    return errors


def _is_nonblank_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_positive_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_valid_date(value: object) -> bool:
    if isinstance(value, datetime):
        return False
    if isinstance(value, date):
        return True
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _is_valid_timezone(value: str) -> bool:
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError:
        return False
    return True


def _clock_minutes(value: object) -> int | None:
    if not isinstance(value, str) or len(value) != 5 or value[2] != ":":
        return None
    hours, minutes = value.split(":")
    if not (hours.isdigit() and minutes.isdigit() and len(hours) == 2 and len(minutes) == 2):
        return None
    if int(hours) > 23 or int(minutes) > 59:
        return None
    return int(hours) * 60 + int(minutes)


def _normalize(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split()).casefold()
