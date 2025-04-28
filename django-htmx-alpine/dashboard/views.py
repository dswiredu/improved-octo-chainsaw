from datetime import datetime

from django.shortcuts import render
from django.http import HttpResponse
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from django.core.cache import cache
from django.db.models import Min, Max
from .models import HistoricalPrice
from .constants import SPARKLINE_DAYS, PERIOD_MAPPING, DATA_FIELDS

import plotly.io as pio
import base64
import io
from django.http import HttpResponse

from .utils.services import get_historical_prices
from .utils.analytics import compute_percentage_changes


def get_price_date_bounds():
    bounds = cache.get("historical_price_date_bounds")
    if not bounds:
        bounds = HistoricalPrice.objects.aggregate(
            min_date=Min("date"), max_date=Max("date")
        )
        cache.set("historical_price_date_bounds", bounds, timeout=3600)
    return bounds


def index(request):
    metric = request.GET.get("metric", "close_price")
    crash = request.GET.get("threshold", 5)
    period =  "D" # request.GET.get("period", "D")
    selected_date = request.GET.get("selected_date")

    bounds = get_price_date_bounds()
    min_date = bounds["min_date"]
    max_date = bounds["max_date"]

    initial_date = selected_date or max_date.strftime("%Y-%m-%d")
    print(metric, crash, period, selected_date, sep=" | ")

    df = get_chart_input_data(
        selected_date=initial_date,
        metric=metric,
        crash_threshold=crash,
        period=period,
        index=True,
    )
    sparklines = generate_summary_sparkline(df)
    price_data = df.iloc[-1].to_dict()
    price_data.update(sparklines)

    chart_html = generate_chart(df, column=metric)

    context = {
        "initial_date": initial_date,
        "initial_show_date": initial_date,
        "metric": metric,
        "threshold": crash,
        "period": period,
        "data_fields": DATA_FIELDS,
        "period_fields": PERIOD_MAPPING,
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


def get_chart_input_data(
    selected_date,
    metric: str = "close_price",
    crash_threshold: str = "5",
    period: str = "D",
    index: bool = False,
):
    df = get_historical_prices(selected_date)

    if period != "D":
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        df = df.resample(period).first().reset_index()

    compute_percentage_changes(df, col=metric, index=index)
    df["crash"] = df[f"{metric}_pct_change"] <= -int(crash_threshold)
    return df


def generate_chart(df: pd.DataFrame, column="close_price"): 
    title = column.replace("_", " ").title()

    # --- main line -------------------------------------------
    fig = px.line(
        df, x="date", y=column,
        labels={column: "Value ($)"},
        title=title
    )

    # Dark-blue line colour only for the line trace
    fig.update_traces(
        selector=dict(mode="lines"),   # apply to the line only
        line=dict(color="#1E3A8A")
    )

    # --- crash overlay ---------------------------------------
    crash = df[df["crash"]]
    if not crash.empty:
        fig.add_trace(
            go.Scatter(
                x=crash["date"],
                y=crash[column],
                mode="markers",
                marker=dict(color="red", size=8, symbol="circle"),
                name="Crash"
            )
        )

    # --- layout ----------------------------------------------
    fig.update_layout(
        template="none",
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(211,211,211,0.3)"),
        font=dict(color="#1f2937"),
        legend=dict(title=None)   # optional: tidy legend
    )

    return fig.to_html(full_html=False)
    
def update_line_chart(request):
    metric = request.GET.get("metric")
    crash = request.GET.get("threshold")
    period = request.GET.get("period")
    selected_date = request.GET.get("selected_date")

    print(metric, crash, period, selected_date, sep=" | ")

    df = get_chart_input_data(selected_date, metric, crash, period)

    chart_html = generate_chart(df, column=metric)
    context = {
        "line_chart": chart_html
    }
    return render(request, 'partials/_chart_view.html', context=context)

def render_table(request):
    metric = request.GET.get("metric")
    crash = request.GET.get("threshold")
    period = request.GET.get("period")
    selected_date = request.GET.get("selected_date")

    print(metric, crash, period, selected_date, sep=" | ")

    df = get_chart_input_data(selected_date, metric, crash, period)
    print(df.head)
    context = {
        "df" : df.to_dict("records")
    }
    return render(request, 'partials/_table_view.html', context)


def date_test(request):
    context = {"selected_date": "2025-04-26"} 
    return render(request, "dashboard/date_test.html", context)

def export_data(request):
    metric = request.GET.get("metric")
    crash = request.GET.get("threshold")
    period = request.GET.get("period")
    selected_date = request.GET.get("selected_date")

    print(metric, crash, period, selected_date, sep=" || ")

    df = get_chart_input_data(selected_date, metric, crash, period)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name="Data", index=False)
    output.seek(0)

    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    response['Content-Disposition'] = 'attachment; filename="exported_data.xlsx"'
    return response

