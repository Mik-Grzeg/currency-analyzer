import pytest
from datetime import date
from unittest.mock import MagicMock
from currency_analyzer.api.client import ExchangeRateClient
from currency_analyzer.reporting.analysis import (
    RateChangesDataStrategy,
    RawRatesDataStrategy,
)
from currency_analyzer.core.database import (
    RateRepository,
    ExchangeRate,
    ExchangeRateChange,
)


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


def test_rate_changes_data_strategy_prepare_data(mock_repository, mock_client):
    strategy = RateChangesDataStrategy()
    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 31)
    mock_client.get_exchange_rates.return_value = [
        ExchangeRate(currency_code="USD", rate=1.0, date="2023-01-01", source="NBP"),
        ExchangeRate(currency_code="USD", rate=1.1, date="2023-01-02", source="NBP"),
    ]
    mock_repository.get_exchange_rate_changes.return_value = [
        ExchangeRateChange(
            currency_code="USD",
            source="NBP",
            start_date=start_date,
            end_date=end_date,
            min_rate=1.0,
            max_rate=1.1,
            avg_rate=1.05,
            total_change_percent=10.0,
            avg_daily_change=0.05,
            start_rate=1.0,
            end_rate=1.1,
            start_to_end_change_percent=10.0,
        )
    ]

    data = strategy.prepare_data(
        mock_repository, mock_client, start_date, end_date, None
    )

    mock_client.get_exchange_rates.assert_called_once_with(start_date, end_date)
    mock_repository.insert_exchange_rates.assert_called_once()
    mock_repository.get_exchange_rate_changes.assert_called_once_with(
        start_date=start_date, end_date=end_date, currency_code=None, source="NBP"
    )
    assert len(data) == 1
    assert data[0]["currency_code"] == "USD"


def test_raw_rates_data_strategy_prepare_data(mock_repository, mock_client):
    strategy = RawRatesDataStrategy()
    start_date = date(2023, 1, 1)
    end_date = date(2023, 1, 31)
    mock_client.get_exchange_rates.return_value = [
        ExchangeRate(currency_code="USD", rate=1.0, date="2023-01-01", source="NBP"),
        ExchangeRate(currency_code="USD", rate=1.1, date="2023-01-02", source="NBP"),
    ]
    mock_repository.get_exchange_rates.return_value = [
        ExchangeRate(currency_code="USD", rate=1.0, date="2023-01-01", source="NBP"),
        ExchangeRate(currency_code="USD", rate=1.1, date="2023-01-02", source="NBP"),
    ]

    data = strategy.prepare_data(
        mock_repository, mock_client, start_date, end_date, currency_code=None
    )

    mock_client.get_exchange_rates.assert_called_once_with(start_date, end_date)
    mock_repository.insert_exchange_rates.assert_called_once()
    assert len(data) == 2
    assert data[0]["currency_code"] == "USD"
    assert data[1]["currency_code"] == "USD"
