from datetime import datetime

from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    min_date = datetime.strptime("2015-01-01", "%Y-%m-%d").date()
    max_date = datetime.strptime("2026-01-01", "%Y-%m-%d").date()
    today = datetime.today().date()

    context = {
        "initial_date": today.strftime("%Y-%m-%d"),
        "initial_show_date": today.strftime("%A, %B %d, %Y"),
        "min_date": min_date.isoformat(),
        "max_date": max_date.isoformat(),
        "datepicker_years": list(range(max_date.year, min_date.year - 1, -1))  # descending
    }
    return render(request, "dashboard/index.html", context)

def update_index_contents(request):
    selected_date = request.GET.get("selected_date")

    try:
        parsed_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return HttpResponse("<p class='text-red-500'>Invalid date selected</p>")

    context = {
        "selected_date": parsed_date.strftime("%A, %B %d, %Y")
    }
    return render(request, "dashboard/partials/_index_contents.html", context=context)