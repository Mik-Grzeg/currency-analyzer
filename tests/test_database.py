import pytest
from datetime import date
from currency_analyzer.core.database import RateRepository
from currency_analyzer.core.types import ExchangeRate
from currency_analyzer.core.exceptions import DatabaseError


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test_db.sqlite"


@pytest.fixture
def rate_repository(db_path):
    return RateRepository(db_path)


@pytest.fixture
def sample_rates():
    return [
        ExchangeRate(
            currency_code="USD", rate=1.0, date=date(2023, 1, 1), source="NBP"
        ),
        ExchangeRate(
            currency_code="USD", rate=1.1, date=date(2023, 1, 2), source="NBP"
        ),
        ExchangeRate(
            currency_code="EUR", rate=0.9, date=date(2023, 1, 1), source="NBP"
        ),
        ExchangeRate(
            currency_code="EUR", rate=0.95, date=date(2023, 1, 2), source="NBP"
        ),
    ]


def test_apply_migrations(rate_repository):
    try:
        rate_repository.apply_migrations()
    except DatabaseError:
        pytest.fail("apply_migrations() raised DatabaseError unexpectedly!")


def test_insert_exchange_rates(rate_repository, sample_rates):
    try:
        rate_repository.insert_exchange_rates(sample_rates)
    except DatabaseError:
        pytest.fail("insert_exchange_rates() raised DatabaseError unexpectedly!")


def test_get_exchange_rates(rate_repository, sample_rates):
    rate_repository.insert_exchange_rates(sample_rates)
    rates = rate_repository.get_exchange_rates(
        date(2023, 1, 1), date(2023, 1, 2), "USD", "NBP"
    )
    assert len(rates) == 2
    assert rates[0].currency_code == "USD"
    assert rates[1].currency_code == "USD"


def test_get_exchange_rates_no_currency(rate_repository, sample_rates):
    rate_repository.insert_exchange_rates(sample_rates)
    rates = rate_repository.get_exchange_rates(
        date(2023, 1, 1), date(2023, 1, 2), None, "NBP"
    )
    assert len(rates) == 4


def test_get_exchange_rates_missing_data_for_dates(rate_repository, sample_rates):
    rate_repository.insert_exchange_rates(sample_rates)
    rates = rate_repository.get_exchange_rates(
        date(2023, 1, 1), date(2023, 1, 4), None, "NBP"
    )
    assert len(rates) == 8


def test_get_exchange_rate_changes(rate_repository, sample_rates):
    rate_repository.insert_exchange_rates(sample_rates)
    changes = rate_repository.get_exchange_rate_changes(
        date(2023, 1, 1), date(2023, 1, 2), None, "NBP"
    )
    assert len(changes) == 2
    assert changes[0].currency_code == "USD"
    assert changes[1].currency_code == "EUR"


def test_get_exchange_rate_changes_for_single_currency(rate_repository, sample_rates):
    rate_repository.insert_exchange_rates(sample_rates)
    changes = rate_repository.get_exchange_rate_changes(
        date(2023, 1, 1), date(2023, 1, 2), "USD", "NBP"
    )
    assert len(changes) == 1
    assert changes[0].currency_code == "USD"
