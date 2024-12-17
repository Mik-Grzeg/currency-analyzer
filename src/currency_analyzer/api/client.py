from abc import ABC, abstractmethod
from datetime import date
from typing import List

from currency_analyzer.core.types import ExchangeRate


class ExchangeRateClient(ABC):
    @abstractmethod
    def get_exchange_rates(
        self, start_date: date, end_date: date
    ) -> List[ExchangeRate]:
        pass

    @property
    @abstractmethod
    def source(self) -> str:
        pass
