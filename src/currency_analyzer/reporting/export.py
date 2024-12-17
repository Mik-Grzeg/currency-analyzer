from typing import List, Dict, Any, Optional
from datetime import date
from abc import ABC, abstractmethod
import json
import csv
from pathlib import Path

from currency_analyzer.api.client import ExchangeRateClient
from currency_analyzer.reporting.analysis import DataPreparationStrategy
from currency_analyzer.logger import get_logger

from ..core.database import RateRepository
from ..core.exceptions import ExportError

logger = get_logger(__name__)


class RateExporter(ABC):
    """Abstract base class for rate exporters"""

    def __init__(
        self,
        repository: RateRepository,
        data_strategy: DataPreparationStrategy,
        client: ExchangeRateClient,
    ):
        self.repository = repository
        self.data_strategy = data_strategy
        self.client = client

    def _prepare_data(
        self, start_date: date, end_date: date, currency_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return self.data_strategy.prepare_data(
            self.repository, self.client, start_date, end_date, currency_code
        )

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """File extension for the export format"""
        pass

    @abstractmethod
    def export(self, data: List[Dict[str, Any]], output_path: Path) -> Path:
        """Export data to file"""
        pass

    def validate_path_suffix(self, output_path: Path):
        """Validate the file extension of the output path"""
        if self.file_extension != output_path.suffix[1:]:
            raise ExportError(
                f"Invalid file extension: {output_path.suffix}, expected: {self.file_extension}"
            )

    def generate_report(
        self,
        start_date: date,
        end_date: date,
        output_file: Path,
        currency_code: Optional[str] = None,
    ) -> Path:
        """Generate report in the specified format"""
        try:
            self.validate_path_suffix(output_file)
            data = self._prepare_data(start_date, end_date, currency_code)
            return self.export(data, output_file)
        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")
            raise ExportError(f"Failed to generate report: {str(e)}")


class CSVRateExporter(RateExporter):

    @property
    def file_extension(self) -> str:
        return "csv"

    def export(self, data: List[Dict[str, Any]], output_path: Path) -> Path:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", newline="") as csvfile:
                if not data:
                    raise ExportError("No data to export")

                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                writer.writerows(data)

            logger.info(f"Successfully exported data to CSV: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to export to CSV: {str(e)}")
            raise ExportError(f"Failed to export to CSV: {str(e)}")


class JSONRateExporter(RateExporter):

    class DateEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, date):
                return obj.isoformat()
            return super().default(obj)

    @property
    def file_extension(self) -> str:
        return "json"

    def export(self, data: List[Dict[str, Any]], output_path: Path) -> Path:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as jsonfile:
                json.dump(
                    data, jsonfile, cls=self.DateEncoder, indent=2, ensure_ascii=False
                )

            logger.info(f"Successfully exported data to JSON: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to export to JSON: {str(e)}")
            raise ExportError(f"Failed to export to JSON: {str(e)}")
