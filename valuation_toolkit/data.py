"""Read a dated snapshot or fetch exact-date closes with yfinance."""

import csv
from datetime import date, timedelta
from pathlib import Path
import tomllib

import pandas as pd

from .model import Financials, ValuationError, number, positive


def read_config(path):
    with Path(path).open("rb") as file:
        return tomllib.load(file)


def read_rows(path, required):
    with Path(path).open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        missing = set(required) - set(reader.fieldnames or ())
        if missing:
            raise ValuationError(f"{path}: missing columns {', '.join(sorted(missing))}")
        rows = {}
        for line, row in enumerate(reader, 2):
            if None in row or any(value is None for value in row.values()):
                raise ValuationError(f"{path}:{line}: inconsistent number of CSV fields")
            ticker = row["ticker"].strip()
            if not ticker or ticker in rows:
                raise ValuationError(f"{path}: blank or duplicate ticker {ticker!r}")
            rows[ticker] = row
        return rows


def csv_number(row, field):
    value = row[field].strip()
    if not value:
        return None
    try:
        return number(float(value), f"{row['ticker']} {field}")
    except ValueError as exc:
        raise ValuationError(f"{row['ticker']} {field} must be a finite number") from exc


def financial_snapshot(path, as_of):
    text_fields = ("ticker", "name", "sector", "currency")
    numeric_fields = ("revenue", "ebit", "ebitda", "eps", "debt", "cash", "minorities",
                      "other_nonoperating", "shares", "margin_fy23", "margin_fy24")
    date_fields = ("period_end", "available_by")
    rows = read_rows(path, (*text_fields, *numeric_fields, *date_fields))
    result = {}
    for ticker, row in rows.items():
        period, available = (date.fromisoformat(row[field]) for field in date_fields)
        if not period < available <= as_of:
            raise ValuationError(f"{ticker}: financials unavailable as of {as_of}")
        if any(not row[field].strip() for field in text_fields):
            raise ValuationError(f"{ticker}: missing company name, sector or currency")
        result[ticker] = Financials(
            **{field: row[field].strip() for field in text_fields},
            **{field: csv_number(row, field) for field in numeric_fields},
        )
    return result


def price_snapshot(path, as_of, financials):
    rows = read_rows(path, ("ticker", "date", "close", "currency", "source"))
    prices = {}
    sources = {}
    for ticker, row in rows.items():
        if ticker not in financials:
            continue
        if row["date"] != as_of.isoformat():
            raise ValuationError(f"{ticker}: close is dated {row['date']}, expected {as_of}")
        if row["currency"] != financials[ticker].currency:
            raise ValuationError(f"{ticker}: price and financial statement currencies differ")
        if not row["source"].strip():
            raise ValuationError(f"{ticker}: missing price source")
        prices[ticker] = positive(csv_number(row, "close"), f"{ticker} close")
        sources[ticker] = row["source"]
    return prices, sources


def yahoo_closes(tickers, as_of, financials):
    import yfinance as yf

    prices = {}
    sources = {}
    for ticker in tickers:
        try:
            security = yf.Ticker(ticker)
            bars = security.history(
                start=as_of.isoformat(), end=(as_of + timedelta(days=1)).isoformat(),
                auto_adjust=False, raise_errors=True, timeout=10,
            )
            if bars.empty:
                raise ValuationError("No quote for the requested trading date")
            actual_dates = pd.DatetimeIndex(bars.index).date
            matches = bars.loc[actual_dates == as_of, "Close"]
            if len(matches) != 1:
                raise ValuationError("Expected one unadjusted close on the requested date")
            currency = security.history_metadata.get("currency")
            if currency != financials[ticker].currency:
                raise ValuationError(f"Price currency {currency!r} differs from financial statements")
            prices[ticker] = positive(matches.iloc[0], f"{ticker} close")
            sources[ticker] = f"https://finance.yahoo.com/quote/{ticker}/history/"
        except Exception as exc:
            raise ValuationError(f"{ticker}: Yahoo close unavailable for {as_of}: {exc}") from exc
    return prices, sources
