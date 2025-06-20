from django.shortcuts import render
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.http import urlencode
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
import pandas as pd

from io import StringIO
from django.http import HttpResponse

from ..utils.validators import validate_scurve_upload
from ..utils.services import (
    generate_and_save_sda_results,
    get_metric_card_context,
    convert_cashflows_to_dataframe
)
from ..utils.graphing import plot_mortgage_floating_cashflows
from ..models import SDACurveInputs
from core.utils.normalization import min_max_normalize

from django.contrib.auth.decorators import login_required

@login_required
def load_data(request: HttpRequest):
    breadcrumbs = [
        {"name": "SDA Curve Calibration"},
        {"name": "Load Data"},  # current page
        {"name": "Results", "url": reverse("modelling:s-curve-results")},
    ]

    context = {
        "breadcrumbs": breadcrumbs,
        "active": "Load Data",
        "title": "SDA Curve Calibration : Load",
        "number_fields": [
            {"label": "PSA Factor (%)", "name": "psa"},
            {"label": "SDA Factor (%)", "name": "sda"},
        ],
    }
    success = False

    if request.method == "POST":
        sa_file = request.FILES.get("security_assumptions")
        curve_file = request.FILES.get("curve_inputs")
        psa = request.POST.get("psa", "0")
        sda = request.POST.get("sda", "0")

        errors = validate_scurve_upload(sa_file, curve_file, psa, sda)

        if errors:
            for e in errors:
                messages.error(request, e)
            success = False
        else:
            try:
                psa_val = float(psa)
                sda_val = float(sda)

                record = SDACurveInputs.objects.create(
                    security_file=sa_file,
                    curve_file=curve_file,
                    psa=psa_val,
                    sda=sda_val,
                    success=True,
                )
                messages.success(request, "Inputs successfully uploaded and validated.")
                success = True
            except Exception as err:
                messages.error(request, f"Unexpected error saving run: {str(e)}")
                success = False

    recent_uploads = SDACurveInputs.objects.order_by("-uploaded_at")[:10]
    context["recent_uploads"] = recent_uploads

    if success:
        url = reverse("s-curve-results")
        query_string = urlencode({"reuse_id": record.id})
        return redirect(f"{url}?{query_string}")

    return render(request, "modelling/s-curve/load.html", context)

@login_required
def get_results(request: HttpRequest):

    run_id = request.GET.get("reuse_id")
    if run_id:
        run = get_object_or_404(SDACurveInputs, id=run_id)
    else:
        run = SDACurveInputs.objects.latest("uploaded_at")

    if not run.has_cached_results():
        generate_and_save_sda_results(run)
    # messages.success(request, f"Successfully run MortgageFloating cashflows for {run.uploaded_at}")
    
    metric_cards = get_metric_card_context(run.metrics)
    cashflows_df = convert_cashflows_to_dataframe(run)

    cf_script, cf_div = plot_mortgage_floating_cashflows(cashflows_df)

    context = {
        "run_id": run_id,
        "metrics": run.metrics,
        "metric_cards": metric_cards,
        "cf_div": cf_div,
        "cf_script": cf_script,
        }
    return render(request, "modelling/s-curve/results.html", context)


@login_required
def export_data_to_csv(request):
    run_id = request.GET.get("reuse_id")
    if run_id:
        run = get_object_or_404(SDACurveInputs, id=run_id)
    else:
        run = SDACurveInputs.objects.latest("uploaded_at")

    if not run.has_cached_results():
        generate_and_save_sda_results(run)
    
    df = pd.DataFrame(list(run.metrics.cashflows.values(
        'timestep', 'balance', 'interest', 'default', 'prepayment', 'principal', 'totalcf'
    )))

    buffer = StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)

    response = HttpResponse(
        buffer,
        content_type='text/csv'
    )
    response['Content-Disposition'] = 'attachment; filename="_cashflows.csv"'
    return response

@login_required
def toggle_graph_table(request):
    run_id = request.GET.get("reuse_id")
    if run_id:
        run = get_object_or_404(SDACurveInputs, id=run_id)
    else:
        run = SDACurveInputs.objects.latest("uploaded_at")
    
    current_mode = request.GET.get("view_mode", "graph")
    next_mode = "table" if current_mode == "graph" else "graph"

    if next_mode == "graph":
        cf_div, cf_script = plot_mortgage_floating_cashflows(run.metrics.cashflows)
        html = render_to_string("modelling/s-curve/partials/cashflows_graph.html", {
            "cf_div": cf_div,
            "cf_script": cf_script,
        })
    else:
        html = render_to_string("modelling/s-curve/partials/cashflows_table.html", {
            "cashflows": run.metrics.cashflows.all(),
        })
    
    return HttpResponse(html)

@login_required
def get_scaled_results(request: HttpRequest) -> HttpResponse:
    run_id = request.GET.get("reuse_id")
    if run_id:
        run = get_object_or_404(SDACurveInputs, id=run_id)
    else:
        run = SDACurveInputs.objects.latest("uploaded_at")
    
    df = pd.DataFrame(list(run.metrics.cashflows.values(
        'timestep', 'balance', 'interest', 'default', 'prepayment', 'principal', 'totalcf'
    )))

    scale = request.GET.get("data_scale", "actual")
    if scale == "normalized":
        scaled_data  = min_max_normalize(df, exclude="timestep")
    else:
        scaled_data = df.copy()
    
    view_mode = request.GET.get("view_mode", "graph")
    if view_mode == "graph":
        cf_div, cf_script = plot_mortgage_floating_cashflows(scaled_data)
        html = render_to_string("modelling/s-curve/partials/cashflows_graph.html", {
            "cf_div": cf_div,
            "cf_script": cf_script,
        })
    else:
        html = render_to_string("modelling/s-curve/partials/cashflows_table.html", {
            "cashflows": run.metrics.cashflows.all(),
        })
    return HttpResponse(html)
