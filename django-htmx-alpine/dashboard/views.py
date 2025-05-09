from django.shortcuts import render
from django.http import HttpResponse

import pandas as pd
from django.core.cache import cache
from django.db.models import Min, Max
from .models import HistoricalPrice
from .constants import PERIOD_MAPPING, DATA_FIELDS

import io
from django.http import HttpResponse
from django.conf import settings

from .utils.services import get_historical_prices
from .utils.analytics import compute_percentage_changes
from .utils.graphing import generate_summary_sparklines, generate_chart


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
    sparkline_components = generate_summary_sparklines(df)
    price_data = df.iloc[-1].to_dict()
    price_data.update(sparkline_components)

    chart_script, chart_div = generate_chart(df, column=metric)

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
        "chart_script": chart_script,
        "chart_div": chart_div,
    }
    return render(request, "dashboard/index.html", context)


def get_chart_input_data(
    selected_date,
    metric: str = "close_price",
    crash_threshold: str = "5",
    period: str = "D",
    index: bool = False,
    start: int=0,
    end: int=None
):
    df = get_historical_prices(selected_date)

    if period != "D":
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        df = df.resample(period).first().reset_index()

    compute_percentage_changes(df, col=metric, index=index)
    df["crash"] = df[f"{metric}_pct_change"] <= -int(crash_threshold)
    return df
    
def update_line_chart(request):
    metric = request.GET.get("metric")
    crash = request.GET.get("threshold")
    period = request.GET.get("period")
    selected_date = request.GET.get("selected_date")

    print(metric, crash, period, selected_date, sep=" | ")

    df = get_chart_input_data(selected_date, metric, crash, period)

    chart_script, chart_div = generate_chart(df, column=metric)
    context = {
        "chart_script": chart_script,
        "chart_div": chart_div,
    }
    return render(request, 'partials/_chart_view.html', context=context)

def render_table(request):
    metric = request.GET.get("metric")
    crash = request.GET.get("threshold")
    period = request.GET.get("period")
    selected_date = request.GET.get("selected_date")
    page = int(request.GET.get("page", 1))

    total_rows = HistoricalPrice.objects.filter(
        date__lte=selected_date).order_by("date").count()

    print(metric, crash, period, selected_date, sep=" | ")

    page_size = settings.PAGINATION_SIZE
    start = (page-1)*page_size
    end = start + page_size

    paginated_df = get_chart_input_data(
        selected_date,
        metric,
        crash,
        period,
        index=False,
        start=start,
        end=end
    )
    has_next = (page * page_size) < total_rows

    context = {
        "df" : paginated_df.to_dict("records"),
        "has_next": has_next,
        "next_page": page + 1
    }

    if request.headers.get("HX-Request") and page > 1:
        print("Just return the rows for infinite scroll")
        return render(request, "partials/_table_rows.html", context)
    
    # First page load: render full table with tbody and loader
    return render(request, 'partials/_table_view.html', context)


def date_test(request):
    context = {"selected_date": "2025-04-26"} 
    return render(request, "dashboard/date_test.html", context)

def nav_test(request):
    return render(request, "dashboard/nav_tests.html")

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

