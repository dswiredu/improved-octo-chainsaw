import plotly.colors

def get_ticker_color_map(tickers):
    """
    Assigns a consistent color to each ticker.
    Uses Plotly's qualitative color palettes.
    """
    base_colors = plotly.colors.qualitative.Plotly
    extended_colors = plotly.colors.qualitative.Alphabet

    palette = base_colors if len(tickers) <= len(base_colors) else extended_colors

    return {ticker: palette[i % len(palette)] for i, ticker in enumerate(sorted(tickers))}
