from datetime import datetime, timedelta

import pandas as pd
from ..models import HistoricalPrice, PositionSnapshot

def get_historical_prices(dte: str, days: int = None, start: int=0, end: int=None) -> pd.DataFrame:
    """
    Retrieves all prices less than a given date.
    """

    dte_obj = datetime.strptime(dte, "%Y-%m-%d").date()

    if days:
        start_date = dte_obj - timedelta(days=days * 2)
        qs = HistoricalPrice.objects.filter(date__range=(start_date, dte_obj)).order_by("date")
    else:
        qs = HistoricalPrice.objects.filter(date__lte=dte).order_by("date")
    
    if end:
        qs = qs[start:end]

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

    decimal_cols = ["open_price", "close_price", "high_price", "low_price"]
    df[decimal_cols] = df[decimal_cols].astype(float)
    return df.sort_values(by=["date"])

def get_positions_snapshot(selected_date) -> list:

    dte_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
    positions = (
        PositionSnapshot.objects
        .filter(date=dte_obj)
        .select_related("account__client", "instrument")
    )

    # Flatten the queryset
    records = [
        {
            "date": ps.date.isoformat(),
            "client_id": ps.account.client.client_id,
            "client_name": ps.account.client.name,
            "account_id": ps.account.account_id,
            "account_name": ps.account.account_name,
            "symbol": ps.instrument.symbol,
            "instrument_name": ps.instrument.name,
            "units": float(ps.units),
            "market_price": float(ps.market_price),
            "market_value": float(ps.market_value),
            "book_value": float(ps.book_value),
            "deposits": float(ps.deposits),
            "withdrawals": float(ps.withdrawals),
            "net_deposits": float(ps.net_deposits),
            "total_return": float(ps.total_return),
            "cumulative_return": float(ps.cumulative_return),
            "pct_of_portfolio": float(ps.pct_of_portfolio),
        }
        for ps in positions
    ]
    return  records