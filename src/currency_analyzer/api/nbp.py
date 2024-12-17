from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, Final, List
import requests

from currency_analyzer.api.client import ExchangeRateClient
from currency_analyzer.logger import get_logger

from ..core.exceptions import (
    APIError,
    RateLimitError,
)
from ..core.types import ExchangeRate

logger = get_logger(__name__)


class NBPClient(ExchangeRateClient):
    BASE_URL: str = "http://api.nbp.pl/api/"

    @property
    def source(self) -> str:
        return "NBP"

    def _make_request(self, start_date: date, end_date: date) -> List[ExchangeRate]:
        """Make single NBP API request for given date range"""
        url = f"{self.BASE_URL}/exchangerates/tables/A/{start_date}/{end_date}/"

        try:

            logger.debug("Making NBP API request: %s", url)
            response = requests.get(url, params=dict(format="json"))
            logger.debug("NBP API response: %s", response.text)
            match response.status_code:
                case 200:
                    tables_data = NBPTableResponse.from_json(data=response.json())

                    return [
                        exchange_rate
                        for table_data in tables_data
                        for exchange_rate in table_data.to_exchange_rates()
                    ]
                case 429:
                    raise RateLimitError()
                case _:
                    raise APIError(f"NBP API request failed: {response.text}")
        except requests.RequestException as e:
            raise APIError(f"NBP API request failed: {str(e)}")

    def get_exchange_rates(
        self, start_date: date, end_date: date
    ) -> List[ExchangeRate]:
        # If period is within 93 days, make single request.
        # NBP api does not allow to fetch more than 93 days at once.
        if (end_date - start_date).days <= 93:
            return self._make_request(start_date, end_date)

        # Split into 93-day chunks
        all_rates = []
        current_start = start_date

        while current_start <= end_date:
            current_end = min(current_start + timedelta(days=93), end_date)

            # Get rates for this chunk
            chunk_rates = self._make_request(current_start, current_end)
            all_rates.extend(chunk_rates)

            # Move to next chunk
            current_start = current_end + timedelta(days=1)

        return all_rates


@dataclass(frozen=True)
class NBPRate:
    currency: str
    code: str
    mid: Decimal
    source: Final[str] = "NBP"


@dataclass
class NBPTableResponse:
    table: str
    no: str
    effectiveDate: date
    rates: List[NBPRate]

    def to_exchange_rates(self) -> List["ExchangeRate"]:
        return [
            ExchangeRate(
                currency_code=rate.code,
                rate=rate.mid,
                date=self.effectiveDate,
                source=rate.source,
            )
            for rate in self.rates
        ]

    @classmethod
    def from_json(cls, data: List[Dict[str, Any]]) -> List["NBPTableResponse"]:
        return [
            cls(
                table=table.get("table", ""),
                no=table.get("no", ""),
                effectiveDate=date.fromisoformat(table.get("effectiveDate", "")),
                rates=[NBPRate(**rate) for rate in table.get("rates", [])],
            )
            for table in data
        ]
