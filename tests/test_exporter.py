import pytest
from datetime import date
from unittest.mock import MagicMock
from pathlib import Path
from currency_analyzer.api.client import ExchangeRateClient
from currency_analyzer.reporting.export import CSVRateExporter, JSONRateExporter
from currency_analyzer.core.database import RateRepository
from currency_analyzer.reporting.analysis import DataPreparationStrategy
from currency_analyzer.core.exceptions import ExportError


@pytest.fixture
def mock_repository():
    return MagicMock(spec=RateRepository)


@pytest.fixture
def mock_client(monkeypatch):
    client = MagicMock(spec=ExchangeRateClient)
    client.source = "NBP"
    monkeypatch.setattr(
        "currency_analyzer.reporting.analysis.ExchangeRateClient", lambda: client
    )
    return client


@pytest.fixture
def mock_data_strategy():
    mock = MagicMock(spec=DataPreparationStrategy)
    mock.__str__.return_value = "mock"
    return mock


@pytest.fixture
def csv_exporter(mock_repository, mock_data_strategy, mock_client):
    return CSVRateExporter(mock_repository, mock_data_strategy, mock_client)


@pytest.fixture
def json_exporter(mock_repository, mock_data_strategy):
    return JSONRateExporter(mock_repository, mock_data_strategy, mock_client)


def test_csv_export(csv_exporter, tmp_path):
    data = [
        {"currency_code": "USD", "rate": 1.0, "date": "2023-01-01", "source": "NBP"}
    ]
    output_path = tmp_path / "test_report.csv"
    result_path = csv_exporter.export(data, output_path)
    assert result_path == output_path
    assert output_path.exists()


def test_csv_export_no_data(csv_exporter, tmp_path):
    output_path = tmp_path / "test_report.csv"
    with pytest.raises(ExportError):
        csv_exporter.export([], output_path)


def test_json_export(json_exporter, tmp_path):
    data = [
        {"currency_code": "USD", "rate": 1.0, "date": "2023-01-01", "source": "NBP"}
    ]
    output_path = tmp_path / "test_report.json"
    result_path = json_exporter.export(data, output_path)
    assert result_path == output_path
    assert output_path.exists()


def test_generate_report(csv_exporter, tmp_path):
    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 31)
    output_path = tmp_path / "test_report.csv"
    csv_exporter.data_strategy.prepare_data.return_value = [
        {"currency_code": "USD", "rate": 1.0, "date": "2023-01-01", "source": "NBP"}
    ]
    output_path = csv_exporter.generate_report(start_date, end_date, output_path, "USD")
    assert Path(output_path).exists()


def test_generate_report_error(csv_exporter):
    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 31)
    csv_exporter.data_strategy.prepare_data.side_effect = Exception(
        "Data preparation failed"
    )
    with pytest.raises(ExportError):
        csv_exporter.generate_report(start_date, end_date, "USD", "test_report")
