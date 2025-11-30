import numpy as np
import pandas as pd
import json
from io import StringIO
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.http import HttpResponseBadRequest
from django.utils import timezone
from .utils.plotting import build_ppv_chart_options
from core.utils.exporter import export_df_to_excel


# ---------------------------------------------------------
# 1. Ghosh (1983) PPV Model
# ---------------------------------------------------------
def ghosh_ppv(D, W):
    """
    Computes PPV using:
    PPV = 0.0134 * W^0.8179 * D^0.1788 * e^(-0.001 * D)
    Vectorized: D may be a numpy array.
    """
    return 0.0134 * (W ** 0.8179) * (D ** 0.1788) * np.exp(-0.001 * D)


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


# ---------------------------------------------------------
# 4. Build DataFrame for plotting
# ---------------------------------------------------------
def compute_ppv_dataframe(D, W):
    """
    Build dataframe where:
    - Index = distances
    - Columns = string versions of centered weights (no 'kg' suffix)
    """
    distances = compute_distance_range(D)
    weight_series = compute_weight_series(W)

    df = pd.DataFrame({"Distance": distances})

    # Use pure string numeric column names (e.g. "150", "150.0", "445.5")
    for weight in weight_series:
        df[str(weight)] = ghosh_ppv(distances, weight)

    return df, weight_series, distances


# ---------------------------------------------------------
# 5. Main View (GET + POST + Session persistence)
# ---------------------------------------------------------
@require_http_methods(["GET", "POST"])
def index(request):
    models = ["Ghosh (1983)"]

    # --------------------------
    # POST → compute & persist
    # --------------------------
    if request.method == "POST":
        distance = float(request.POST.get("distance"))
        weight = float(request.POST.get("weight"))
        selected_model = request.POST.get("model")

        df, weight_series, dist_series = compute_ppv_dataframe(distance, weight)

        # Persist full numeric dataframe to session
        request.session["gv_distance"] = distance
        request.session["gv_weight"] = weight
        request.session["gv_model"] = selected_model
        request.session["gv_df"] = df.to_json()

        return redirect("ground-vibration-index")

    # --------------------------
    # GET → load existing state
    # --------------------------
    distance = request.session.get("gv_distance")
    weight = request.session.get("gv_weight")
    selected_model = request.session.get("gv_model")

    df = None
    if request.session.get("gv_df"):
        json_str = request.session["gv_df"]
        df = pd.read_json(StringIO(json_str))

    options_json = None
    if df is not None and distance is not None and weight is not None:
        weight_series = compute_weight_series(weight)
        option = build_ppv_chart_options(df, distance, weight, weight_series)
        options_json = json.dumps(option)

    context = {
        "models": models,
        "selected_model": selected_model,
        "distance": distance,
        "weight": weight,
        "df": df,
        "options_json": options_json,
    }

    return render(request, "ground_vibration/index.html", context)


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
