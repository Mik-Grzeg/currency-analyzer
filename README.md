# Currency analyzer

Currency analyzer is a Python application that automates retrieval of currency exchange rate data from the NBP API, stores the data in a SQLite database, and generates reports in CSV/JSON format. This is a CLI application.


## Installation

This application requires [Poetry](https://python-poetry.org/) for dependency management.

1. Install the required dependencies using Poetry:

    ```sh
    poetry install
    ```

## Usage

The application provides a command-line interface (CLI) for interacting with the various functionalities. Below are some examples of how to use the CLI.

### Report all currencies raw exchange rates

To report raw exchange rates for specific date range:

#### JSON output

```sh
poetry run analyzer --start-date 2024-12-01 --end-date 2024-12-05 --output reports/rates_export_raw.json --format json --export-type raw 
```

#### CSV otuput
```sh
poetry run analyzer --start-date 2024-12-01 --end-date 2024-12-05 --output reports/rates_export_raw.csv --format csv --export-type raw
```

### Report selected currency raw exchange rates

To report raw exchange rates for specific date range and currency:

#### JSON output

```sh
poetry run analyzer --start-date 2024-12-01 --end-date 2024-12-05 --currency USD --output reports/rates_export_USD_raw.json --format json --export-type raw 
```

#### CSV otuput
```sh
poetry run analyzer --start-date 2024-12-01 --end-date 2024-12-05 --currency USD --output reports/rates_export_USD_raw.csv --format csv --export-type raw
```

### Report exchange rate changes 

To report exchange rate changes for specific date range ordered by the highest fluctuations:

#### JSON output

```sh
poetry run analyzer --start-date 2024-12-01 --end-date 2024-12-05 --output reports/rates_export_changes.json --format json --export-type changes 
```

#### CSV otuput
```sh
poetry run analyzer --start-date 2024-12-01 --end-date 2024-12-05 --output reports/rates_export_changes.csv --format csv --export-type changes
```

### Report selected currency exchange rate changes

To report exchange rate changes for specific date range and currency:

#### JSON output

```sh
poetry run analyzer --start-date 2024-12-01 --end-date 2024-12-05 --currency USD --output reports/rates_export_USD_changes.json --format json --export-type changes 
```

#### CSV otuput
```sh
poetry run analyzer --start-date 2024-12-01 --end-date 2024-12-05 --currency USD --output reports/rates_export_USD_changes.csv --format csv --export-type changes
```

## Data structures

### Raw exports

The raw export contains the historical exchange rates for the specified date range. Each entry in the export includes the following fields:

* `currency_code`: The code of the currency (e.g. USD, EUR).
* `rate`: The exchange rate of the currency.
* `date`: The date of the exchange rate.
* `source`: The source of the exchange rate data (e.g. NBP).

### Changes exports

The changes export contains the analysis of exchange rate changes for the specified date range and currency. Each entry in the export includes the following fields:

* `currency_code`: The code of the currency (e.g. USD, EUR).
* `source`: The source of the exchange rate data (e.g. NBP).
* `start_date`: The start date of the analysis period.
* `end_date`: The end date of the analysis period.
* `min_rate`: The minimum exchange rate during the analysis period.
* `max_rate`: The maximum exchange rate during the analysis period.
* `avg_rate`: The average exchange rate during the analysis period.
* `total_change_percent`: The total percentage change in the exchange rate in the analyssis period.
* `avg_daily_change`: The average daily percentage change in the exchange rate during the analysis period.
* `start_rate`: The exchange rate at the start of the analysis period.
* `end_rate`: The exchange rate at the end of the analysis period.
* `start_to_end_change_percent`: The percentage change in the exchange rate from the start to the end of the analysis period.

## Example reports

Example reports:

|Path|Reports|
|:---|:---|
|`./example_reports/raw.csv`| CSV report with raw exchange rates of all currencies|
|`./example_reports/raw.json`| JSON report with raw exchange rates of all currencies|
|`./example_reports/raw_usd.csv`| CSV report with raw exchange rates of USD currency|
|`./example_reports/raw_usd.json`| JSON report with raw exchange rates of USD currency|
|`./example_reports/changes.csv`| CSV report with exchange rate changes|
|`./example_reports/changes.json`| JSON report with exchange rate changes|
|`./example_reports/changes_usd.csv`| CSV report with exchange rate changes of USD currency|
|`./example_reports/changes_usd.json`| JSON report with exchange rate changes of USD currency|

## Tests

Tests are located in `./tests` directory. They can be ran with:

```sh
poetry run pytest tests
```