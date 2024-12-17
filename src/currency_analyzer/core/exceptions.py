from typing import Optional


class CurrencyAnalyzerError(Exception):
    """Base exception class for NBP Currency Analyzer"""

    pass


class APIError(CurrencyAnalyzerError):
    """Raised when there is an error with the NBP API"""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message)


class RateLimitError(APIError):
    """Raised when NBP API rate limit is exceeded"""

    def __init__(self, message: str = "NBP API rate limit exceeded"):
        super().__init__(message, status_code=429)


class DatabaseError(Exception):
    """Raised when there is an error with the database operations"""

    pass


class ValidationError(CurrencyAnalyzerError):
    """Raised when there is a data validation error"""

    pass


class DateRangeError(ValidationError):
    """Raised when there is an issue with the date range (no more than 93 days)"""

    pass


class ExportError(CurrencyAnalyzerError):
    """Raised when there is an error exporting data"""

    pass


class MissingDataError(CurrencyAnalyzerError):
    """Raised when there is missing currency data"""

    pass
