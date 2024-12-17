import polars as pl
from typing import List
import pytest
from typer.testing import CliRunner
from datetime import datetime, timedelta, date
from unittest.mock import MagicMock, Mock
from currency_analyzer.cli.main import ExportFormat, app_with_logger
from currency_analyzer.core.database import ExchangeRate
from currency_analyzer.api.nbp import NBPClient
from currency_analyzer.core.types import ExchangeRateChange
from pathlib import Path

runner = CliRunner()


@pytest.fixture
def mock_nbp_client(monkeypatch):
    client = MagicMock(spec=NBPClient)
    client.source = "NBP"
    client.get_exchange_rates.return_value = [
        ExchangeRate(
            currency_code="USD", rate=1.0, date=date(2024, 1, 1), source="NBP"
        ),
        ExchangeRate(
            currency_code="USD", rate=1.1, date=date(2024, 1, 2), source="NBP"
        ),
        ExchangeRate(
            currency_code="USD", rate=1.2, date=date(2024, 1, 4), source="NBP"
        ),
        ExchangeRate(
            currency_code="EUR", rate=1.0, date=date(2024, 1, 2), source="NBP"
        ),
        ExchangeRate(
            currency_code="EUR", rate=2.0, date=date(2024, 1, 4), source="NBP"
        ),
    ]
    monkeypatch.setattr(
        "currency_analyzer.cli.main.NBPClient", Mock(return_value=client)
    )
    return client


@pytest.fixture
def start_date() -> str:
    return str(date(2024, 1, 1))


@pytest.fixture
def end_date() -> str:
    return str(date(2024, 1, 5))


@pytest.mark.parametrize("export_format", [ExportFormat.CSV, ExportFormat.JSON])
def test_export_changes_single_currency_valid(
    tmp_path, start_date, end_date, mock_nbp_client, export_format
):
    output_path = tmp_path / f"test_report.{export_format.value}"
    result = runner.invoke(
        app_with_logger(),
        [
            "--start-date",
            start_date,
            "--end-date",
            end_date,
            "--currency",
            "USD",
            "--format",
            export_format,
            "--db-path",
            str(tmp_path / "test_db.sqlite"),
            "--export-type",
            "changes",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    mock_nbp_client.get_exchange_rates.assert_called_once()
    assert output_path.exists()

    exchange_rate_changes = read_exchange_rate_changes(output_path, export_format)
    expected_changes = [
        ExchangeRateChange(
            currency_code="USD",
            source="NBP",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 5),
            min_rate=1.0,
            max_rate=1.2,
            avg_rate=1.1,
            total_change_percent=20.0,
            avg_daily_change=9.55,
            start_rate=1.0,
            end_rate=1.2,
            start_to_end_change_percent=20.0,
        )
    ]

    assert expected_changes == exchange_rate_changes


@pytest.mark.parametrize("export_format", [ExportFormat.CSV, ExportFormat.JSON])
def test_export_changes_all_currencies_valid(
    tmp_path, start_date, end_date, mock_nbp_client, export_format
):
    output_path = tmp_path / f"test_report.{export_format.value}"
    result = runner.invoke(
        app_with_logger(),
        [
            "--start-date",
            start_date,
            "--end-date",
            end_date,
            "--format",
            export_format,
            "--db-path",
            str(tmp_path / "test_db.sqlite"),
            "--export-type",
            "changes",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    mock_nbp_client.get_exchange_rates.assert_called_once()
    assert output_path.exists()

    exchange_rate_changes = read_exchange_rate_changes(output_path, export_format)
    expected_changes = [
        ExchangeRateChange(
            currency_code="EUR",
            source="NBP",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 5),
            min_rate=1.0,
            max_rate=2.0,
            avg_rate=1.5,
            total_change_percent=100.0,
            avg_daily_change=100,
            start_rate=1.0,
            end_rate=2.0,
            start_to_end_change_percent=100.0,
        ),
        ExchangeRateChange(
            currency_code="USD",
            source="NBP",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 5),
            min_rate=1.0,
            max_rate=1.2,
            avg_rate=1.1,
            total_change_percent=20.0,
            avg_daily_change=9.55,
            start_rate=1.0,
            end_rate=1.2,
            start_to_end_change_percent=20.0,
        ),
    ]

    assert expected_changes == exchange_rate_changes


@pytest.mark.parametrize("export_format", [ExportFormat.CSV, ExportFormat.JSON])
def test_export_raw_single_currency_valid(
    tmp_path, start_date, end_date, mock_nbp_client, export_format
):
    output_path = tmp_path / f"test_report.{export_format.value}"
    result = runner.invoke(
        app_with_logger(),
        [
            "--start-date",
            start_date,
            "--end-date",
            end_date,
            "--currency",
            "EUR",
            "--format",
            export_format,
            "--db-path",
            str(tmp_path / "test_db.sqlite"),
            "--export-type",
            "raw",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    mock_nbp_client.get_exchange_rates.assert_called_once()
    assert output_path.exists()

    exchange_rates = read_exchange_rates(output_path, export_format)
    expected_rates = [
        ExchangeRate(
            currency_code="EUR", rate=None, date=date(2024, 1, 1), source="NBP"
        ),
        ExchangeRate(
            currency_code="EUR", rate=1.0, date=date(2024, 1, 2), source="NBP"
        ),
        ExchangeRate(
            currency_code="EUR", rate=None, date=date(2024, 1, 3), source="NBP"
        ),
        ExchangeRate(
            currency_code="EUR", rate=2.0, date=date(2024, 1, 4), source="NBP"
        ),
        ExchangeRate(
            currency_code="EUR", rate=None, date=date(2024, 1, 5), source="NBP"
        ),
    ]

    assert expected_rates == exchange_rates


@pytest.mark.parametrize("export_format", [ExportFormat.CSV, ExportFormat.JSON])
def test_export_raw_all_currencies_valid(
    tmp_path, start_date, end_date, mock_nbp_client, export_format
):
    output_path = tmp_path / f"test_report.{export_format.value}"
    result = runner.invoke(
        app_with_logger(),
        [
            "--start-date",
            start_date,
            "--end-date",
            end_date,
            "--format",
            export_format,
            "--db-path",
            str(tmp_path / "test_db.sqlite"),
            "--export-type",
            "raw",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    mock_nbp_client.get_exchange_rates.assert_called_once()
    assert output_path.exists()

    exchange_rates = read_exchange_rates(output_path, export_format)
    expected_rates = [
        ExchangeRate(
            currency_code="EUR", rate=None, date=date(2024, 1, 1), source="NBP"
        ),
        ExchangeRate(
            currency_code="EUR", rate=1.0, date=date(2024, 1, 2), source="NBP"
        ),
        ExchangeRate(
            currency_code="EUR", rate=None, date=date(2024, 1, 3), source="NBP"
        ),
        ExchangeRate(
            currency_code="EUR", rate=2.0, date=date(2024, 1, 4), source="NBP"
        ),
        ExchangeRate(
            currency_code="EUR", rate=None, date=date(2024, 1, 5), source="NBP"
        ),
        ExchangeRate(
            currency_code="USD", rate=1.0, date=date(2024, 1, 1), source="NBP"
        ),
        ExchangeRate(
            currency_code="USD", rate=1.1, date=date(2024, 1, 2), source="NBP"
        ),
        ExchangeRate(
            currency_code="USD", rate=None, date=date(2024, 1, 3), source="NBP"
        ),
        ExchangeRate(
            currency_code="USD", rate=1.2, date=date(2024, 1, 4), source="NBP"
        ),
        ExchangeRate(
            currency_code="USD", rate=None, date=date(2024, 1, 5), source="NBP"
        ),
    ]

    assert expected_rates == exchange_rates


def test_export_invalid_date_range(tmp_path):
    start_date = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = (datetime.today() - timedelta(days=31)).strftime("%Y-%m-%d")

    result = runner.invoke(
        app_with_logger(),
        [
            "--start-date",
            start_date,
            "--end-date",
            end_date,
            "--currency",
            "USD",
            "--format",
            "csv",
            "--db-path",
            str(tmp_path / "test_db.sqlite"),
            "--export-type",
            "changes",
            "--output",
            "test_report",
        ],
    )
    assert result.exit_code != 0
    assert "End date must be after start date" in result.output


def read_exchange_rates(path: Path, format: ExportFormat) -> List[ExchangeRate]:
    schema = {
        "currency_code": pl.Utf8,
        "rate": pl.Float64,
        "date": pl.Utf8,
        "source": pl.Utf8,
    }

    match format:
        case ExportFormat.CSV:
            df = pl.read_csv(path, schema=schema, try_parse_dates=True)
        case ExportFormat.JSON:
            df = pl.read_json(path, schema=schema)
        case _:
            raise ValueError(f"Unsupported format: {format}")

    df = df.with_columns([pl.col("date").cast(pl.Date)])

    return [ExchangeRate(**row) for row in df.to_dicts()]


def read_exchange_rate_changes(
    path: Path, format: ExportFormat
) -> List[ExchangeRateChange]:
    schema = {
        "currency_code": pl.Utf8,
        "source": pl.Utf8,
        "start_date": pl.Utf8,
        "end_date": pl.Utf8,
        "min_rate": pl.Float64,
        "max_rate": pl.Float64,
        "avg_rate": pl.Float64,
        "total_change_percent": pl.Float64,
        "avg_daily_change": pl.Float64,
        "start_rate": pl.Float64,
        "end_rate": pl.Float64,
        "start_to_end_change_percent": pl.Float64,
    }
    match format:
        case ExportFormat.CSV:
            df = pl.read_csv(path, schema=schema)
        case ExportFormat.JSON:
            df = pl.read_json(path, schema=schema)
        case _:
            raise ValueError(f"Unsupported format: {format}")

    df = df.with_columns(
        [pl.col("start_date").cast(pl.Date), pl.col("end_date").cast(pl.Date)]
    )
    return [ExchangeRateChange(**row) for row in df.to_dicts()]
