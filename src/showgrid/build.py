"""Safe, atomic creation of declared show-plan documents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import tempfile

from .models import ShowPlan
from .render import (
    _OUTPUT_FILENAMES,
    render_manifest,
    render_run_sheet,
    render_show_card,
    render_showday_checklist,
    render_technical_brief,
)
from .validation import ValidationReport, validate_show


class ValidationFailedError(ValueError):
    """Raised when an inconsistent declared plan cannot be built."""

    def __init__(self, report: ValidationReport) -> None:
        self.report = report
        super().__init__("\n".join(report.errors))


class OutputDirectoryExistsError(FileExistsError):
    """Raised instead of replacing a pre-existing output directory."""


@dataclass(frozen=True)
class BuildResult:
    """The new output directory and all files generated in it."""

    output: Path
    files: tuple[Path, ...]


def build_show_documents(
    plan: ShowPlan, source: str | Path, output: str | Path
) -> BuildResult:
    """Validate and atomically create a new local show-plan document bundle."""

    report = validate_show(plan)
    if not report.is_valid:
        raise ValidationFailedError(report)

    source_path = Path(source)
    output_path = Path(output)
    if output_path.exists():
        raise OutputDirectoryExistsError(
            f"refusing to replace existing output directory: {output_path}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = Path(
        tempfile.mkdtemp(prefix=f".{output_path.name}.", dir=output_path.parent)
    )
    try:
        (temporary_path / "SHOW_CARD.md").write_text(
            render_show_card(plan), encoding="utf-8"
        )
        (temporary_path / "TECHNICAL_BRIEF.md").write_text(
            render_technical_brief(plan), encoding="utf-8"
        )
        (temporary_path / "RUN_SHEET.md").write_text(
            render_run_sheet(plan), encoding="utf-8"
        )
        (temporary_path / "SHOWDAY_CHECKLIST.md").write_text(
            render_showday_checklist(), encoding="utf-8"
        )
        (temporary_path / "manifest.json").write_text(
            render_manifest(plan, source_path), encoding="utf-8"
        )
        temporary_path.replace(output_path)
    except BaseException:
        shutil.rmtree(temporary_path, ignore_errors=True)
        raise

    return BuildResult(
        output=output_path,
        files=tuple(output_path / filename for filename in _OUTPUT_FILENAMES),
    )
