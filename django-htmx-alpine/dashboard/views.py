from datetime import datetime

from django.shortcuts import render
from django.http import HttpResponse
import plotly.express as px
import pandas as pd
from django.core.cache import cache
from django.db.models import Min, Max
from .models import HistoricalPrice

from .utils.services import get_historical_prices
from .utils.analytics import compute_percentage_changes

def get_price_date_bounds():
    bounds = cache.get("historical_price_date_bounds")
    if not bounds:
        bounds = HistoricalPrice.objects.aggregate(
            min_date = Min("date"),
            max_date = Max("date")
        )
        cache.set("historical_price_date_bounds", bounds, timeout=3600)
    return bounds


def index(request):
    selected_date = request.GET.get("selected_date")

    bounds = get_price_date_bounds()
    min_date = bounds["min_date"]
    max_date = bounds["max_date"]

    initial_date = selected_date or max_date.strftime("%Y-%m-%d")
    print(max_date, min_date, initial_date, sep=" | ")

    df = get_historical_prices(initial_date, days=30)
    sparklines = generate_summary_sparkline(df)
    compute_percentage_changes(df)
    price_data = df.iloc[-1].to_dict()
    price_data.update(sparklines)
    # print(price_data)
    # df.to_csv("last_30_dataset.csv", index=False)

    context = {
        "initial_date": initial_date,
        "initial_show_date": initial_date,
        "price_data": price_data,
        "min_date": min_date.isoformat(),
        "max_date": max_date.isoformat(),
        "datepicker_years": list(range(max_date.year, min_date.year - 1, -1))  # descending
    }
    return render(request, "dashboard/index.html", context)

def generate_summary_sparkline(df: pd.DataFrame) -> dict:
    """
    Creates a Plotly sparkline using px.line() and returns it as an HTML div.
    """
    res = dict()

    config = {
                "displayModeBar": False,
                "displaylogo": False,
                "staticPlot": True 
            }

    for col in df.columns:
        if col != "date":
            # Generate Sparkline using px.line()
            fig = px.line(df, x=df.index, y=col)

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
                showlegend=False,
            )

            fig.update_traces(
                line=dict(color="#1E3A8A"),
                hoverinfo="skip",
                hovertemplate=None
                )
            # Convert the figure to an HTML div string
            res[f"{col}_sparkline"] = fig.to_html(full_html=False, config=config)
    return res

def update_index_contents(request):
    selected_date = request.GET.get("selected_date")
    print(f"Selected date {selected_date}")

    try:
        parsed_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return HttpResponse("<p class='text-red-500'>Invalid date selected</p>")
    
    df = get_historical_prices(selected_date)
    price_data = df.iloc[-1].to_dict()
    print(price_data)
    if df.empty:
        return HttpResponse("<p class='text-gray-500 italic'>No data for this date.</p>")

    context = {
        "selected_date": parsed_date.strftime("%A, %B %d, %Y"),
        "price_data": price_data
    }
    return render(request, "dashboard/partials/_index_contents.html", context=context)