import pandas as pd

from dashboard.models import Ticker



def get_historical_prices_df(ticker_symbols: list) -> pd.DataFrame:
    all_data = []

    for symbol in ticker_symbols:
        try:
            ticker = Ticker.objects.get(symbol=symbol)
        except Ticker.DoesNotExist:
            continue

        prices = ticker.historical_prices.all().order_by('date')
        for p in prices:
            all_data.append({
                "Date": p.date,
                "Close": float(p.close_price),
                "Ticker": symbol
            })

    if not all_data:
        return pd.DataFrame()  # Empty

    return pd.DataFrame(all_data)
