import numpy as np
import pandas as pd
import json
from io import StringIO
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.utils import timezone
from .utils.plotting import build_ppv_chart_options
from core.utils.exporter import export_df_to_excel
from .model_registry import MODEL_REGISTRY

def load_model_form(request):
    """
    HTMX loader: returns the form fields for the selected PPV model.
    """
    model_key = request.GET.get("model")
    if not model_key or model_key not in MODEL_REGISTRY:
        return HttpResponse("")  # return empty placeholder

    model_def = MODEL_REGISTRY[model_key]
    form_class = model_def["form"]
    form = form_class()

    return render(
        request,
        "ground_vibration/partials/model_form.html",
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

def compute_ppv_dataframe_from_model(D, W, compute_fn, params):
    """
    Builds a PPV dataframe for the selected model.
    Uses:
        - distance range = D ± 200
        - weight series = [W-100, W-50, W, W+50, W+100]
    """
    distances = compute_distance_range(D)
    weight_series = compute_weight_series(W)

    df = pd.DataFrame({"Distance": distances})

    for weight in weight_series:
        # Compute PPV curve: vectorized over distance array
        ppv_values = compute_fn(distances, weight, **params)
        df[str(weight)] = ppv_values

    return df, weight_series, distances



@require_http_methods(["GET", "POST"])
def index(request):

    # --------------------------
    # POST → compute & persist
    # --------------------------
    if request.method == "POST":
        distance = float(request.POST.get("distance"))
        weight = float(request.POST.get("weight"))
        selected_model = request.POST.get("model")

        # Validate model key
        if selected_model not in MODEL_REGISTRY:
            return HttpResponseBadRequest("Invalid model selected.")

        model_def = MODEL_REGISTRY[selected_model]
        form_class = model_def["form"]
        compute_fn = model_def["compute"]

        # Validate model-specific fields
        model_form = form_class(request.POST)
        if not model_form.is_valid():
            # render page with model_form errors + base inputs
            return render(
                request,
                "ground_vibration/index.html",
                {
                    "model_registry": MODEL_REGISTRY,
                    "selected_model": selected_model,
                    "model_form": model_form,
                    "distance": distance,
                    "weight": weight,
                    "options_json": None,
                },
            )

        model_params = model_form.cleaned_data

        # --- Build PPV dataframe using selected model ---
        df, weight_series, dist_series = compute_ppv_dataframe_from_model(
            distance, weight, compute_fn, model_params
        )

        # Persist data to session
        request.session["gv_distance"] = distance
        request.session["gv_weight"] = weight
        request.session["gv_model"] = selected_model
        request.session["gv_params"] = model_params
        request.session["gv_df"] = df.to_json()

        return redirect("ground-vibration-index")

    # --------------------------
    # GET → load session state
    # --------------------------
    distance = request.session.get("gv_distance")
    weight = request.session.get("gv_weight")
    selected_model = request.session.get("gv_model")
    model_params = request.session.get("gv_params")

    df = None
    model_form = None

    if selected_model:
        form_class = MODEL_REGISTRY[selected_model]["form"]
        model_form = form_class(initial=model_params)

    if request.session.get("gv_df"):
        df = pd.read_json(StringIO(request.session["gv_df"]))

    options_json = None
    if df is not None:
        weight_series = compute_weight_series(weight)
        option = build_ppv_chart_options(df, distance, weight, weight_series)
        options_json = json.dumps(option)

    return render(
        request,
        "ground_vibration/index.html",
        {
            "model_registry": MODEL_REGISTRY,
            "selected_model": selected_model,
            "model_form": model_form,
            "distance": distance,
            "weight": weight,
            "options_json": options_json,
        },
    )



def export_excel(request):
    """
    Exports the last ground vibration dataframe stored in session as an Excel file.
    """
    if "gv_df" not in request.session:
        return HttpResponseBadRequest("No data available to export.")
    
    df_json = request.session["gv_df"]
    df = pd.read_json(StringIO(df_json))

    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ground_vibration_export_{timestamp}.xlsx"
    return export_df_to_excel(df, filename)
