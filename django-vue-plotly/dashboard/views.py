from collections import defaultdict
import time
from datetime import datetime, timedelta, date

from django.shortcuts import render
from django.core.cache import cache
from django.http import JsonResponse
from django.db.models import Q
import plotly.express as px
import pandas as pd
import numpy as np

from .models import Ticker, HistoricalPrice

from .utils.analytics import get_historical_prices_df
from .utils.graphs import get_ticker_color_map

# Create your views here.

def generate_sparkline(price_data):
    """
    Creates a Plotly sparkline using px.line() and returns it as an HTML div.
    """
    if not price_data:
        return ""

    # Create DataFrame for Plotly Express
    df = {"index": list(range(len(price_data))), "price": price_data}

    # Generate Sparkline using px.line()
    fig = px.line(
        df,
        x="index",
        y="price",
    )

    # Format the chart (minimalist styling)
    fig.update_layout(
        template="none",
        plot_bgcolor="white",  # Match card background
        paper_bgcolor="white",
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),  # Hide X-axis
        yaxis=dict(visible=False),  # Hide Y-axis
        height=50,  # Small height for sparkline effect
        width=140,  # Small width to fit inside card
    )
    fig.update_traces(line=dict(color="#1E3A8A"))
    # Convert the figure to an HTML div string
    sparkline_html = fig.to_html(full_html=False)

    return sparkline_html

def index(request):
    tickers = Ticker.objects.all().order_by("symbol")
    ticker_data = []

    selected_date = request.GET.get("selected_date")
    today = date.today()

    if selected_date:
        sdate = datetime.strptime(selected_date, "%Y-%m-%d").date()
    else:
        sdate = today

    ninety_days_ago = sdate - timedelta(days=90)

    # Get all relevant historical prices once!
    historical_prices = HistoricalPrice.objects.filter(
        ticker__in = tickers,
        date__range=(ninety_days_ago, sdate)
    ).order_by('ticker', 'date').values('ticker', 'date', 'close_price')

    price_dict = defaultdict(list)

    for entry in historical_prices:
        price_dict[entry["ticker"]].append(entry["close_price"])
    
    cache_key = f"prices_{sdate}"
    cached_data = cache.get(cache_key)

    if cached_data:
        ticker_data = cached_data
    else:
        print("cache expired")
        ticker_data = []
        for ticker in tickers:
            price_data = price_dict.get(ticker.id, [])

            if not price_data:
                continue

            # Extract latest and old prices
            latest_price = price_data[-1] if price_data else None
            print(ticker.symbol, latest_price, sep="~")
            old_price = price_data[0] if price_data else None

            if latest_price and old_price and old_price != 0:
                percent_change = ((latest_price - old_price) / old_price) * 100
            else:
                percent_change = None
            
            # Prepare sparkline data
            sparkline = generate_sparkline(price_data)

            ticker_data.append({
                "symbol": ticker.symbol,
                "name": ticker.name,
                "latest_price": latest_price,
                "percent_change": percent_change,
                "sparkline": sparkline,
            })
        cache.set(cache_key, ticker_data, timeout=60*15) # cache for 15 mins

    context = {
        "date_value": sdate.strftime("%Y-%m-%d"),
        "date_max": today.strftime("%Y-%m-%d"),
        "ticker_data": ticker_data
    }

    return render(request, 'dashboard/index.html', context)

def ticker_detail(request, symbol):
    try:
        ticker = Ticker.objects.get(symbol=symbol)
    except Ticker.DoesNotExist:
        return render(request, "dashboard/404.html", status=404)

    today = date.today()
    ninety_days_ago = today - timedelta(days=90)

    price_data_qs = HistoricalPrice.objects.filter(
        ticker=ticker,
        date__range=(ninety_days_ago, today)
    ).order_by('date').values_list('date', 'close_price')

    price_data = list(price_data_qs)
    latest_price = price_data[-1][1] if price_data else None
    old_price = price_data[0][1] if price_data else None
    percent_change = ((latest_price - old_price) / old_price) * 100 if old_price else None

    context = {
        "ticker": ticker,
        "latest_price": latest_price,
        "percent_change": percent_change,
        "price_data": price_data,
    }
    return render(request, 'dashboard/ticker_detail.html', context)

def ticker_suggestions(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse([], safe=False)
    
    matches = Ticker.objects.filter(
        Q(symbol__startswith=query) | Q(name__icontains=query)
    ).order_by("symbol")[:10]

    results = [
        {"symbol": t.symbol, "name": t.name} for t in matches
    ]
    return JsonResponse(results, safe=False)

def compare_tickers(request):
    return render(request, "dashboard/compare_tickers.html", {})

def compare_line_chart(request):
    tickers_param = request.POST.get('tickers', '')
    ticker_symbols = [t.strip() for t in tickers_param.split(',') if t.strip()]

    print("Tickers selected:", ticker_symbols)

    df = get_historical_prices_df(ticker_symbols)

    if df.empty:
        return render(request, 'dashboard/partials/compare_chart.html', {
            'chart_div': "<div class='text-gray-500'>No data available for selected tickers.</div>"
        })

    # Build consistent color map
    color_map = get_ticker_color_map(df['Ticker'].unique())

    # Create line chart with color mapping
    fig = px.line(
        df,
        x="Date",
        y="Close",
        color="Ticker",
        title="Ticker Close Prices Comparison",
        color_discrete_map=color_map
    )

    # Custom styling
    fig.update_layout(
        template="none",
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(211, 211, 211, 0.3)"),
        font=dict(color="#1f2937"),
        hovermode="x unified",
        showlegend=False,
    )

    chart_div = fig.to_html(full_html=False)

    return render(request, 'dashboard/partials/compare_chart.html', {
        'chart_div': chart_div
    })


def compare_risk_return(request):
    tickers_param = request.POST.get('tickers', '')
    ticker_symbols = [t.strip() for t in tickers_param.split(',') if t.strip()]
    print("Tickers selected:", ticker_symbols)

    df = get_historical_prices_df(ticker_symbols)

    if df.empty:
        return render(request, 'dashboard/partials/compare_risk_return.html', {
            'chart_div': "<div class='text-gray-500'>No data available for selected tickers.</div>"
        })

    all_stats = []

    for symbol in df['Ticker'].unique():
        subset = df[df['Ticker'] == symbol].sort_values("Date")
        subset['Return'] = subset['Close'].pct_change()

        if subset['Return'].dropna().shape[0] < 2:
            continue

        mean_return = subset['Return'].mean()
        volatility = subset['Return'].std()

        annualized_return = mean_return * 252
        annualized_volatility = volatility * np.sqrt(252)

        all_stats.append({
            "Ticker": symbol,
            "Annual Return": annualized_return,
            "Annual Volatility": annualized_volatility,
            "Size": 5,
        })

    if not all_stats:
        return render(request, 'dashboard/partials/compare_risk_return.html', {
            'chart_div': "<div class='text-gray-500'>Not enough data for selected tickers.</div>"
        })

    stats_df = pd.DataFrame(all_stats)

    # ✅ Apply color mapping here
    color_map = get_ticker_color_map(stats_df['Ticker'].unique())

    fig = px.scatter(
        stats_df,
        x='Annual Volatility',
        y='Annual Return',
        size="Size",
        color='Ticker',
        title="Risk-Return Map",
        labels={"Annual Volatility": "Volatility", "Annual Return": "Return"},
        color_discrete_map=color_map
    )

    fig.update_traces(textposition='top left')
    fig.update_layout(
        template="none",
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="rgba(211, 211, 211, 0.7)", title=""),
        yaxis=dict(showgrid=True, gridcolor="rgba(211, 211, 211, 0.7)", title=""),
        font=dict(color="#1f2937"),
        showlegend=False,
    )

    chart_div = fig.to_html(full_html=False)

    return render(request, 'dashboard/partials/compare_risk_return.html', {
        'chart_div': chart_div
    })

def compare_max_drawdown(request):
    tickers_param = request.POST.get('tickers', '')
    ticker_symbols = [t.strip() for t in tickers_param.split(',') if t.strip()]
    print("Tickers selected:", ticker_symbols)

    df = get_historical_prices_df(ticker_symbols)

    if df.empty:
        return render(request, 'dashboard/partials/compare_max_drawdown.html', {
            'chart_div': "<div class='text-gray-500'>No data available for selected tickers.</div>"
        })

    drawdowns = []

    for symbol in df['Ticker'].unique():
        prices = df[df['Ticker'] == symbol].sort_values('Date')['Close']
        running_max = prices.cummax()
        dd_series = (prices - running_max) / running_max
        max_drawdown = dd_series.min()

        drawdowns.append({
            "Ticker": symbol,
            "Max Drawdown (%)": round(max_drawdown * 100, 2)  # convert to percentage
        })

    if not drawdowns:
        return render(request, 'dashboard/partials/compare_max_drawdown.html', {
            'chart_div': "<div class='text-gray-500'>Not enough data to compute drawdowns.</div>"
        })

    dd_df = pd.DataFrame(drawdowns)

    fig = px.bar(
    dd_df,
    x='Max Drawdown (%)',
    y='Ticker',
    orientation='h',
    color='Ticker',
    color_discrete_map=get_ticker_color_map(dd_df['Ticker'].unique()),
    title="Max Drawdown per Ticker"
)

    # Flip bars downward and tidy up layout
    fig.update_layout(
        template="none",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="#1f2937"),
        showlegend=False,
    )

    # Make bars drop below x-axis
    fig.update_yaxes(autorange='reversed', title="")  # 👈 remove y-axis title
    fig.update_xaxes(title="")  # 👈 remove x-axis title

    chart_div = fig.to_html(full_html=False)

    return render(request, 'dashboard/partials/compare_max_drawdown.html', {
        'chart_div': chart_div
    })

def compare_sharpe_ratio(request):
    tickers_param = request.POST.get('tickers', '')
    ticker_symbols = [t.strip() for t in tickers_param.split(',') if t.strip()]
    print("Tickers selected:", ticker_symbols)

    df = get_historical_prices_df(ticker_symbols)

    if df.empty:
        return render(request, 'dashboard/partials/compare_sharpe_ratio.html', {
            'chart_div': "<div class='text-gray-500'>No data available for selected tickers.</div>"
        })

    stats = []

    for symbol in df['Ticker'].unique():
        subset = df[df['Ticker'] == symbol].sort_values("Date")
        subset['Return'] = subset['Close'].pct_change()

        if subset['Return'].dropna().shape[0] < 2:
            continue

        mean_daily = subset['Return'].mean()
        std_daily = subset['Return'].std()

        annual_return = mean_daily * 252
        annual_volatility = std_daily * np.sqrt(252)
        sharpe = annual_return / annual_volatility if annual_volatility > 0 else 0

        stats.append({
            "Ticker": symbol,
            "Sharpe Ratio": round(sharpe, 2),
            "Annual Return": round(annual_return * 100, 2),
            "Volatility": round(annual_volatility * 100, 2)
        })

    if not stats:
        return render(request, 'dashboard/partials/compare_sharpe_ratio.html', {
            'chart_div': "<div class='text-gray-500'>Not enough data to compute Sharpe ratios.</div>"
        })

    sr_df = pd.DataFrame(stats)

    fig = px.scatter(
        sr_df,
        x="Sharpe Ratio",
        y="Ticker",
        size="Annual Return",
        color="Volatility",
        color_continuous_scale="Blues",
        title="Sharpe Ratio vs. Risk & Return",
        hover_data=["Annual Return", "Volatility"]
    )

    fig.update_layout(
        template="none",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="#1f2937"),
        showlegend=False,
    )

    chart_div = fig.to_html(full_html=False)

    return render(request, 'dashboard/partials/compare_sharpe_ratio.html', {
        'chart_div': chart_div
    })