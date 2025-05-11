import json
from django.shortcuts import render
from django.http import HttpResponse

from django.core.cache import cache
from django.db.models import Min, Max
from ..models import PositionSnapshot
from ..constants.client_portfolios import TABULATOR_COLUMNS

from django.conf import settings

from ..utils.services import get_positions_snapshot

def get_position_snapshot_date_bounds():
    bounds = cache.get("position_snapshot_date_bounds")
    if not bounds:
        bounds = PositionSnapshot.objects.aggregate(
            min_date=Min("date"), max_date=Max("date")
        )
        cache.set("position_snapshot_date_bounds", bounds, timeout=settings.CACHE_TIMEOUT)
    return bounds

def index(request):
    selected_date = request.GET.get("selected_date")

    bounds = get_position_snapshot_date_bounds()
    min_date = bounds["min_date"]
    max_date = bounds["max_date"]
    display_date = selected_date or max_date.strftime("%Y-%m-%d")

    print(min_date, max_date, display_date, selected_date, sep = " | ")

    records = get_positions_snapshot(display_date)

    context = {
        "display_date": display_date,
        "min_date": min_date.isoformat(),
        "max_date": max_date.isoformat(),
        "datepicker_years": list(
            range(max_date.year, min_date.year - 1, -1)
        ),
        "data_json": json.dumps(records),
        "column_json": json.dumps(TABULATOR_COLUMNS)
    }
    return render(request, "dashboard/client_portfolios.html", context)
