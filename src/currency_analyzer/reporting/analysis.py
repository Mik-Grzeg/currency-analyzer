from dataclasses import asdict
from datetime import date
from typing import Any, Dict, List, Optional, Protocol

from currency_analyzer.api.client import ExchangeRateClient
from currency_analyzer.core.database import (
    ExchangeRate,
    ExchangeRateChange,
    RateRepository,
)


class DataPreparationStrategy(Protocol):
    """Protocol for data preparation strategies"""

    def prepare_data(
        self,
        repository: RateRepository,
        client: ExchangeRateClient,
        start_date: date,
        end_date: date,
        currency_code: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        pass


class RateChangesDataStrategy(DataPreparationStrategy):
    def prepare_data(
        self,
        repository: RateRepository,
        client: ExchangeRateClient,
        start_date: date,
        end_date: date,
        currency_code: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        api_rates = client.get_exchange_rates(start_date, end_date)
        repository.insert_exchange_rates(api_rates)

        rate_changes: List[ExchangeRateChange] = repository.get_exchange_rate_changes(
            start_date=start_date,
            end_date=end_date,
            currency_code=currency_code,
            source=client.source,
        )

        return [asdict(item) for item in rate_changes]

    def __str__(self):
        return "changes"


class RawRatesDataStrategy(DataPreparationStrategy):
    def prepare_data(
        self,
        repository: RateRepository,
        client: ExchangeRateClient,
        start_date: date,
        end_date: date,
        currency_code: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        api_rates = client.get_exchange_rates(start_date, end_date)
        repository.insert_exchange_rates(api_rates)

        rates: List[ExchangeRate] = repository.get_exchange_rates(
            start_date, end_date, currency_code, client.source
        )

        return [asdict(item) for item in rates]

    def __str__(self):
        return "raw"
