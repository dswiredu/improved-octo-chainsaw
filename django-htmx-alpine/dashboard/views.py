from datetime import datetime

from django.shortcuts import render
from django.http import HttpResponse
import plotly.express as px
import pandas as pd
from django.core.cache import cache
from django.db.models import Min, Max
from .models import HistoricalPrice

import plotly.io as pio
import base64

from .utils.services import get_historical_prices
from .utils.analytics import compute_percentage_changes

SPARKLINE_DAYS = 30


def get_price_date_bounds():
    bounds = cache.get("historical_price_date_bounds")
    if not bounds:
        bounds = HistoricalPrice.objects.aggregate(
            min_date=Min("date"), max_date=Max("date")
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

    df = get_historical_prices(initial_date)
    sparklines = generate_summary_sparkline(df)
    compute_percentage_changes(df)
    df.to_csv("full_data.csv", index=False)
    price_data = df.iloc[-1].to_dict()
    print(price_data)
    price_data.update(sparklines)

    chart_html = generate_chart(df)

    context = {
        "initial_date": initial_date,
        "initial_show_date": initial_date,
        "price_data": price_data,
        "min_date": min_date.isoformat(),
        "max_date": max_date.isoformat(),
        "datepicker_years": list(
            range(max_date.year, min_date.year - 1, -1)
        ),  # descending
        "line_chart": chart_html,
    }
    return render(request, "dashboard/index.html", context)


def generate_summary_sparkline(df: pd.DataFrame) -> dict:
    """
    Creates a Plotly sparkline using px.line() and returns it as an HTML div.
    """

    res = dict()
    spark_df = df.tail(SPARKLINE_DAYS)
    spark_df.to_csv("sparkline_days.csv", index=False)

    for col in spark_df.columns:
        if col != "date":
            # Generate Sparkline using px.line()
            fig = px.line(spark_df, x=spark_df.index, y=col)

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
                line=dict(color="#1E3A8A"), hoverinfo="skip", hovertemplate=None
            )

            # Export to SVG and encode
            svg_bytes = pio.to_image(fig, format="svg")
            base64_svg = base64.b64encode(svg_bytes).decode("utf-8")
            data_uri = f"data:image/svg+xml;base64,{base64_svg}"

            res[f"{col}_sparkline"] = data_uri
    return res


def generate_chart(df, column="close_price"):  # Need to add period and threshold picker
    fig = px.line(df, x="date", y=column, labels={column: "Value ($)"})

    # Apply None theme (transparent background)
    fig.update_layout(
        template="none",  # No background styling
        plot_bgcolor="white",  # Match card background
        paper_bgcolor="white",
        xaxis=dict(showgrid=False),  # No vertical grid
        yaxis=dict(
            showgrid=True, gridcolor="rgba(211, 211, 211, 0.3)"
        ),  # Faint horizontal grid
        font=dict(color="#1f2937"),  # Text color to match the card
    )

    # Set line color to Dark Blue
    fig.update_traces(line=dict(color="#1E3A8A"))  # Dark blue color

    return fig.to_html(full_html=False)


def update_line_chart(request):
    metric_select = request.GET.get("metric")
    crash_threshold = request.GET.get("threshold")
    period = request.GET.get("period")
    selected_date = request.GET["selected_date"]

    print(metric_select, crash_threshold, period, selected_date, sep=" | ")

    df = get_historical_prices(selected_date)
    chart_html = generate_chart(df, column=metric_select)
    return HttpResponse(chart_html)
