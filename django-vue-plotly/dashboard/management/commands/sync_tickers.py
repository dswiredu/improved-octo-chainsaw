from django.core.management.base import BaseCommand
from dashboard.models import Ticker, TickerMetadata

import yfinance as yf

from dashboard.constants.yahoo_finance import TICKERS


def sync_ticker_and_metadata(symbol):
    """
    Fetches data from yfinaince for `symbol` anf updates/creates:
        1) Ticker (core info)
        2) TIckerMetadata (exetended info)
    """
    yf_ticker = yf.Ticker(symbol)
    info = yf_ticker.info or {}

    # Basic Ticker fields
    name = info.get("longName") or info.get("shortName", "")
    exchange = info.get("exchange", "")
    sector = info.get("sector", "")
    industry = info.get("industry", "")

    ticker_obj, _ = Ticker.objects.update_or_create(
        symbol=symbol,
        defaults={
            "name": name,
            "exchange": exchange,
            "sector": sector,
            "industry": industry,
        },
    )

    # Extended metadata for TickerMetadata
    summary = info.get("longBusinessSummary", "")
    website = info.get("website", "")
    market_cap = info.get("marketCap")
    beta = info.get("beta")
    dividendYield = info.get("dividendYield", 0.0)
    fullTimeEmployees = info.get("fullTimeEmployees", 0)
    country = info.get("country", "")

    TickerMetadata.objects.update_or_create(
        ticker=ticker_obj,
        defaults={
            "long_business_summary": summary,
            "website": website,
            "market_cap": market_cap,
            "beta": beta,
            "dividend_yield": dividendYield,
            "full_time_employees": fullTimeEmployees,
            "country": country,
        },
    )


class Command(BaseCommand):
    help = "Fetch and store metadata for multiple ticker symbols from Yahoo Finance."

    def handle(self, *args, **options):
        if not TICKERS:
            self.stdout.write(self.style.ERROR("Cannot find any list of tickers."))
            return

        self.stdout.write("Syncing ticker and metadata for configured tickers...")
        for symbol in TICKERS:
            try:
                self.stdout.write(f"  Processing: {symbol}")
                sync_ticker_and_metadata(symbol)
            except Exception as err:
                self.stdout.write(
                    self.style.ERROR(f"Unexpected error for {symbol}: {err}")
                )

        self.stdout.write(self.style.SUCCESS("All done!"))
