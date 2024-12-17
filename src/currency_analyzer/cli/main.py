from pathlib import Path
import typer
from datetime import date, datetime

from typing import Annotated, Any, Callable, Optional
from enum import Enum


from currency_analyzer.api.client import ExchangeRateClient
from currency_analyzer.api.nbp import NBPClient
from currency_analyzer.logger import get_logger
from currency_analyzer.reporting.export import (
    CSVRateExporter,
    JSONRateExporter,
    RateExporter,
)
from currency_analyzer.reporting.analysis import (
    RateChangesDataStrategy,
    RawRatesDataStrategy,
)

from ..core.database import RateRepository
from ..core.exceptions import APIError, DatabaseError

logger = get_logger(__name__)

app = typer.Typer(name="currency-analyzer", add_completion=False)


def validate_dates(start_date: date, end_date: date) -> None:
    if end_date < start_date:
        raise ValueError("End date must be after start date")

    if (end_date - start_date).days > 279:
        raise ValueError("Date range cannot exceed 279 days")

    if end_date > date.today():
        raise ValueError("End date cannot be in the future")


def exporter_cls_from_params(
    export_type: str, format: str
) -> Callable[[Any, Any], RateExporter]:
    exporters = {
        ("changes", "csv"): lambda r, c: CSVRateExporter(
            r, RateChangesDataStrategy(), c
        ),
        ("changes", "json"): lambda r, c: JSONRateExporter(
            r, RateChangesDataStrategy(), c
        ),
        ("raw", "csv"): lambda r, c: CSVRateExporter(r, RawRatesDataStrategy(), c),
        ("raw", "json"): lambda r, c: JSONRateExporter(r, RawRatesDataStrategy(), c),
    }

    exporter_class = exporters.get((export_type, format.lower()))
    if not exporter_class:
        raise ValueError(f"Unsupported format: {format}")
    return exporter_class


def get_client(source: str) -> ExchangeRateClient:
    if source == "nbp":
        return NBPClient()
    else:
        raise ValueError(f"Unsupported source: {source}")


class ExportFormat(str, Enum):
    CSV = "csv"
    JSON = "json"


class ExportType(str, Enum):
    CHANGES = "changes"
    RAW = "raw"


class DataSource(str, Enum):
    NBP = "nbp"


@app.command()
def export(
    start_date: Annotated[datetime, typer.Option(help="Start date (YYYY-MM-DD)")],
    end_date: Annotated[datetime, typer.Option(help="End date (YYYY-MM-DD)")],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output file name",
        ),
    ],
    currency: Annotated[
        Optional[str],
        typer.Option(
            help="Currency code (e.g., USD). If not provided, exports all currencies"
        ),
    ] = None,
    format: Annotated[
        ExportFormat, typer.Option(help="Export format (csv/json)")
    ] = ExportFormat.JSON,
    export_type: Annotated[
        ExportType, typer.Option(help="Type of export (changes/raw)")
    ] = ExportType.CHANGES,
    db_path: Annotated[
        str, typer.Option(help="Path to the database file")
    ] = "rates.db",
    source: Annotated[DataSource, typer.Option(help="Data source")] = DataSource.NBP,
):
    """Export exchange rates report"""
    try:
        validate_dates(start_date.date(), end_date.date())

        repo = RateRepository(db_path)

        client = get_client(source)

        # select exporter based on export type and format
        exporter_cls = exporter_cls_from_params(export_type, format)

        exporter = exporter_cls(repo, client)
        filepath = exporter.generate_report(
            start_date=start_date.date(),
            end_date=end_date.date(),
            currency_code=currency,
            output_file=output,
        )

        return filepath

    except (ValueError, APIError, DatabaseError) as e:
        print(f"Export failed: {str(e)}")
        raise typer.Exit(code=1)


def app_with_logger():
    return app


if __name__ == "__main__":
    app_with_logger()
