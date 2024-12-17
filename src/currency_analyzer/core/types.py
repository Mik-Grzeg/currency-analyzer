from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from typing import Optional


@dataclass
class ExchangeRate:
    """Representation of exchange rate, which might come from different sources"""

    currency_code: str
    rate: Optional[Decimal]
    date: date
    source: str

    def to_tuple(self) -> tuple[str, Optional[float], str, str]:
        return (
            self.currency_code,
            float(self.rate) if self.rate is not None else None,
            self.date.isoformat(),
            self.source,
        )


@dataclass
class ExchangeRateChange:
    """Representation of exchange rate change"""

    currency_code: str
    source: str
    start_date: date
    end_date: date
    min_rate: Decimal
    max_rate: Decimal
    avg_rate: Decimal
    total_change_percent: Decimal
    avg_daily_change: Decimal
    start_rate: Decimal
    end_rate: Decimal
    start_to_end_change_percent: Decimal
