import numpy as np
import pandas as pd
import json
from io import StringIO
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.utils import timezone
from .utils.plotting import build_blast_chart_options
from core.utils.exporter import export_df_to_excel
from .model_registry import MODEL_REGISTRY

def load_model_form(request):
    """
    HTMX loader: returns the form fields for the selected Air Blast model.
    """
    model_key = request.GET.get("model")
    if not model_key or model_key not in MODEL_REGISTRY:
        return HttpResponse("")  # return empty placeholder

    model_def = MODEL_REGISTRY[model_key]
    form_class = model_def["form"]
    form = form_class()

    return render(
        request,
        "air_blast/partials/model_form.html",
        {
            "form": form,
            "model_label": model_def["label"],
        },
    )


# ---------------------------------------------------------
# 2. Distance range centered on input D
# ---------------------------------------------------------
def compute_distance_range(D, span=200, step=1):
    """
    Distance = [max(1, D-span) ... D+span] inclusive.
    Default span = 200, step = 1.
    """
    start = max(1, D - span)
    end = D + span
    return np.arange(start, end + 1, step)


# ---------------------------------------------------------
# 3. Weight series centered on input W
# ---------------------------------------------------------
def compute_weight_series(W):
    """
    Curves at: W-100, W-50, W, W+50, W+100
    Only positive weights kept.
    """
    candidates = [W - 100, W - 50, W, W + 50, W + 100]
    return [w for w in candidates if w > 0]

def compute_blast_dataframe_from_model(D, W, compute_fn, params):
    """
    Builds a Air Blast dataframe for the selected model.
    Uses:
        - distance range = D ± 200
        - weight series = [W-100, W-50, W, W+50, W+100]
    """
    distances = compute_distance_range(D)
    weight_series = compute_weight_series(W)

    df = pd.DataFrame({"Distance": distances})

    for weight in weight_series:
        # Compute Air Blast curve: vectorized over distance array
        ab_values = compute_fn(distances, weight, **params)
        df[str(weight)] = ab_values

    return df, weight_series, distances



@require_http_methods(["GET", "POST"])
def index(request):

    # --------------------------
    # POST → compute & save into session
    # --------------------------
    if request.method == "POST":
        distance = float(request.POST.get("distance"))
        weight = float(request.POST.get("weight"))
        selected_model = request.POST.get("model")

        if selected_model not in MODEL_REGISTRY:
            return HttpResponseBadRequest("Invalid model selected.")

        model_def = MODEL_REGISTRY[selected_model]
        form_class = model_def["form"]
        compute_fn = model_def["compute"]

        # Build and validate model-specific form
        model_form = form_class(request.POST)
        if not model_form.is_valid():
            return render(
                request,
                "air_blast/index.html",
                {
                    "model_registry": MODEL_REGISTRY,
                    "selected_model": selected_model,
                    "model_form": model_form,   # <-- return with errors + data
                    "distance": distance,
                    "weight": weight,
                    "options_json": None,
                },
            )

        model_params = model_form.cleaned_data

        # Compute Air Blast curves
        df, weight_series, dist_series = compute_blast_dataframe_from_model(
            distance, weight, compute_fn, model_params
        )

        # Persist into session for GET reload
        request.session["ab_distance"] = distance
        request.session["ab_weight"] = weight
        request.session["ab_model"] = selected_model
        request.session["ab_model_label"] = model_def["label"]
        request.session["ab_params"] = model_params
        request.session["ab_df"] = df.to_json()

        return redirect("air-blast-index")

    # --------------------------
    # GET → load session state & rebuild page
    # --------------------------
    distance = request.session.get("ab_distance")
    weight = request.session.get("ab_weight")
    selected_model = request.session.get("ab_model")
    model_params = request.session.get("ab_params")

    model_form = None
    df = None

    # If a model was previously selected, rehydrate its form
    if selected_model:
        form_class = MODEL_REGISTRY[selected_model]["form"]
        model_form = form_class(initial=model_params)
    
    # print("Model:", selected_model)
    # print("Params:", model_params)
    # if model_form:
    #     print("Form fields:", model_form.fields.keys())
    #     print("Initial:", model_form.initial)

    # If DF exists, rebuild chart
    if request.session.get("ab_df"):
        df = pd.read_json(StringIO(request.session["ab_df"]))

    options_json = None
    if df is not None:
        weight_series = compute_weight_series(weight)
        option = build_blast_chart_options(df, distance, weight, weight_series)
        options_json = json.dumps(option)

    return render(
        request,
        "air_blast/index.html",
        {
            "model_registry": MODEL_REGISTRY,
            "selected_model": selected_model,
            "model_form": model_form,
            "distance": distance,
            "weight": weight,
            "options_json": options_json,
        },
    )

def construct_model_metadata(request) -> pd.DataFrame:
    # ---- Extract stored metadata ----
    model_label = request.session.get("ab_model_label")
    model_params = request.session.get("ab_params", {})
    distance = request.session.get("ab_distance")
    weight = request.session.get("ab_weight")

    # ---- Build parameters DF (2-column tidy format) ----
    param_rows = [
        ["Model", model_label],
        ["Distance", distance],
        ["Weight", weight],
    ]

    for key, value in model_params.items():
        param_rows.append([key, value])

    df_params = pd.DataFrame(param_rows, columns=["Parameter", "Value"])
    return df_params


def export_excel(request):
    """
    Exports the last ground vibration dataframe stored in session as an Excel file.
    """
    if "ab_df" not in request.session:
        return HttpResponseBadRequest("No data available to export.")
    
    df_json = request.session["ab_df"]
    df = pd.read_json(StringIO(df_json))

    df_params = construct_model_metadata(request)

    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    filename = f"air_blast_export_{timestamp}.xlsx"
    return export_df_to_excel([df_params, df], filename)
