from datetime import datetime

from django.core.management.base import BaseCommand
import yfinance as yf
from dashboard.models import Ticker, HistoricalPrice
from dashboard.constants.yahoo_finance import TICKERS

class Command(BaseCommand):
    """
    Usage:
        python manage.py sync_prices --start_date=YYYY-MM-DD --end_date=YYYY-MM-DD [--symbols AAPL MSFT]

    If --symbols is omitted, the command will fetch prices for ALL Ticker objects in the DB.
    """

    help = (
        "Fetch/update historical prices (OHLCV) for one or more tickers from yfinance."
    )

    def add_arguments(self, parser):
        # Optional arguments for date range
        parser.add_argument(
            "--start_date",
            type=str,
            help="Start date (YYYY-MM-DD)",
            default="2022-01-01",
        )
        parser.add_argument(
            "--end_date", type=str, help="End date (YYYY-MM-DD)", default=None
        )

        # Optional argument for specific symbols
        parser.add_argument(
            "--symbols", nargs="*", help="List of ticker symbols to sync"
        )

    def handle(self, *args, **options):
        start_date = options["start_date"]
        end_date = options["end_date"]
        symbols = options["symbols"]

        if not end_date:
            # default to today's date if not provided
            end_date = datetime.now().strftime("%Y-%m-%d")

        self.stdout.write(f"Fetching data from {start_date} to {end_date}...")

        if not symbols:
            symbols = TICKERS        
        ticker_qs = Ticker.objects.filter(symbol__in=symbols)

        if not ticker_qs.exists():
            self.stdout.write(self.style.ERROR("No tickers found to sync."))
            return

        self.stdout.write(f"Updating {ticker_qs.count()} tickers.\n")

        # Fetch tickers here:
        self.batch_download_prices(ticker_qs, start_date, end_date)

        self.stdout.write(self.style.SUCCESS("Historical price sync complete!"))

    def batch_download_prices(self, ticker_qs, start_date, end_date):
        """
        Fetch multiple tickers at once using yfinance.
        This can be more efficient, but requires parsing a multi-index DataFrame.
        """
        symbol_list = [t.symbol for t in ticker_qs]
        self.stdout.write(f"==> Downloading batch for: {symbol_list}")

        df = yf.download(symbol_list, start=start_date, end=end_date, group_by="ticker")

        if df.empty:
            self.stdout.write(self.style.WARNING("No data returned in batch fetch."))
            return

        # 'df' will have a multi-level column index, like:
        #   Columns: [(AAPL, Open), (AAPL, High), (AAPL, Low), (AAPL, Close), (AAPL, Adj Close), (AAPL, Volume),
        #             (MSFT, Open), (MSFT, High), ... ]
        # We'll need to iterate over each symbol's sub-DataFrame.

        self.stdout.write(f"Saving historical data for all symbols: {symbol_list}...")
        for ticker in ticker_qs:
            symbol = ticker.symbol
            # Some rows might not exist if yfinance can't fetch data for that symbol
            if symbol not in df.columns.levels[0]:
                self.stdout.write(
                    self.style.WARNING(
                        f"No data found in batch for {symbol}. Skipping."
                    )
                )
                continue

            sub_df = df[symbol]
            rows_inserted = 0
            for index, row in sub_df.iterrows():
                try:
                    date_val = index.date()
                    hp_values = {
                        "open_price": row["Open"],
                        "high_price": row["High"],
                        "low_price": row["Low"],
                        "close_price": row["Close"],
                        "volume": row["Volume"],
                    }
                    _, created = HistoricalPrice.objects.update_or_create(
                        ticker=ticker, date=date_val, defaults=hp_values
                    )
                    if created:
                        rows_inserted += 1
                except Exception as err:
                    self.stdout.write(
                        self.style.ERROR(
                            f"   Unexepected error -> {symbol} data: {err}."
                        )
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"   -> {symbol} data: {rows_inserted} new rows inserted/updated."
                )
            )
