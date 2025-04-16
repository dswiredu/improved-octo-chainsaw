from django.core.management.base import BaseCommand
import pandas as pd

from dashboard.models import HistoricalPrice

class Command(BaseCommand):
    """
    Usage:
        python manage.py load_historical_price prices.csv
    """

    help = (
        "Load historical prices based on provided prices file."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--file_path",
            type=str,
            help="Prices file.",
            required=True
        )

    def handle(self, *args, **options):
        prices_file = options["file_path"]
        self.stdout.write(f"Loading prices from {prices_file}...")

        df = pd.read_csv(prices_file,parse_dates=["Date"])
        rows_inserted = 0
        for _, row in df.iterrows():
            data = {
                "date": row["Date"],
                "open_price": row["Open"],
                "high_price": row["High"],
                "low_price": row["Low"],
                "close_price": row["Close"],
                "volume": row["Volume"],
            }
            _, created = HistoricalPrice.objects.update_or_create(
                date=data["date"], defaults=data
            )
            if created:
                rows_inserted +=1
        self.stdout.write(self.style.SUCCESS(f"Historical price sync complete. {rows_inserted} new rows inserted/created!"))
