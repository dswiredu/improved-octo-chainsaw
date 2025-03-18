from collections import defaultdict
from datetime import datetime, timedelta, date

from django.shortcuts import render, get_object_or_404
from django.core.cache import cache
from django.http import JsonResponse
from django.db.models import Q
import plotly.express as px

from .models import Ticker, HistoricalPrice

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