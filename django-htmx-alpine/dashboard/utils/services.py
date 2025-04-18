from datetime import datetime, timedelta

import pandas as pd
from ..models import HistoricalPrice

def get_historical_prices(dte: str, days: int = None) -> pd.DataFrame:
    """
    Retrieves all prices less than a given date.
    """

    dte_obj = datetime.strptime(dte, "%Y-%m-%d").date()

    if days:
        start_date = dte_obj - timedelta(days=days * 2)
        qs = HistoricalPrice.objects.filter(date__range=(start_date, dte_obj)).order_by("date")
    else:
        qs = HistoricalPrice.objects.filter(date__lte=dte).order_by("date")

    if not qs.exists():
        return pd.DataFrame()
    
    df = pd.DataFrame.from_records(
        qs.values(
            "date", 
            "open_price", 
            "close_price", 
            "high_price", 
            "low_price", 
            "volume"
        )
    )
    return df.sort_values(by=["date"])