from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST
import pandas as pd
import plotly.graph_objs as go
from plotly.offline import plot
from uuid import UUID

from .forms import ScenarioUploadForm
from .models import ScenarioDataSet, ScenarioValue
from .services import parse_mapping_file, process_scenario_file


@login_required
def upload_scenarios(request):
    if request.method == "POST":
        form = ScenarioUploadForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist("files")
            mapping_file = form.cleaned_data["mapping_file"]

            try:
                mapping = parse_mapping_file(mapping_file)
            except Exception as e:
                form.add_error("mapping_file", f"Could not read mapping file: {e}")
                return render(
                    request, "scenario_analysis/upload-scenarios.html", {"form": form}
                )

            files_by_name = {f.name: f for f in files}

            for scenario_name, filename in mapping.items():
                file_obj = files_by_name.get(filename)

                if not file_obj:
                    messages.warning(
                        request,
                        f"Mapping specifies '{filename}' for scenario '{scenario_name}', but file was not uploaded.",
                    )
                    continue

                dataset, created = ScenarioDataSet.objects.get_or_create(
                    user=request.user,
                    name=scenario_name,
                    defaults={
                        "file": file_obj,
                        "status": "pending",
                    },
                )

                if not created:
                    dataset.file = file_obj  # Overwrite existing file
                    dataset.status = "pending"
                    dataset.save()

            messages.success(request, "Files uploaded. Processing will begin shortly.")
            return redirect("scenario_analysis:upload-scenarios")
    else:
        form = ScenarioUploadForm()

    return render(
        request,
        "scenario_analysis/upload-scenarios.html",
        {
            "form": form,
        },
    )


@login_required
def dataset_status_table(request):
    datasets = ScenarioDataSet.objects.filter(user=request.user).order_by(
        "-uploaded_at"
    )
    html = render_to_string(
        "scenario_analysis/partials/dataset_status_table.html",
        {"datasets": datasets},
        request=request,
    )
    return HttpResponse(html)


@login_required
def start_background_processing(request):
    datasets = ScenarioDataSet.objects.filter(user=request.user, status="pending")

    for dataset in datasets:
        try:
            dataset.status = "processing"
            dataset.log("Started background processing.")
            dataset.save(update_fields=["status", "logs"])

            process_scenario_file(dataset.file, dataset)

        except Exception as e:
            dataset.status = "error"
            dataset.log(f"Processing failed: {str(e)}")
            dataset.save(update_fields=["status", "logs"])

    return JsonResponse({"status": "ok"})


@ensure_csrf_cookie
@login_required
def clear_datasets(request):
    ScenarioDataSet.objects.filter(user=request.user).delete()
    messages.success(request, "All uploads have been cleared.")
    html = render_to_string(
        "scenario_analysis/partials/dataset_status_table.html",
        {"datasets": []},
        request=request,
    )
    return HttpResponse(html)


from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def compare_scenarios(request) -> HttpResponse:
    """
    Renders the main Compare Scenarios page with two-level autocomplete.
    """
    user = request.user

    # All scenarios available for the user
    all_scenarios = ScenarioDataSet.objects.filter(user=user, status="done")

    all_columns = sorted({
        column
        for scenario in all_scenarios
        for column in scenario.column_names or []
    }) 

    # Selected scenario IDs (from GET request)
    selected_scenario_ids = request.GET.getlist("selected_scenario_ids")
    # print(selected_scenario_ids)

    # Filter to get selected scenario objects
    selected_scenarios = (
        ScenarioDataSet.objects.filter(
            id__in=selected_scenario_ids, user=user, status="done"
        )
        if selected_scenario_ids
        else []
    )
    print(selected_scenarios)

    # Combine column names from selected scenarios
    column_options = set()
    for scenario in selected_scenarios:
        column_options.update(scenario.column_names or [])

    # Selected column names (from GET request)
    selected_column_names = request.GET.getlist("selected_column_names")
    single_selected_column = request.GET.get(
        "single-selected-culumn",
        selected_column_names[0] if selected_column_names else None
        )
    
    print(selected_scenarios, selected_column_names, single_selected_column, sep=" | ")

    if selected_column_names:
        qs = ScenarioValue.objects.filter(
                variable=single_selected_column,
                dataset_id__in=selected_scenarios,
            ).select_related("dataset")
    
        df = pd.DataFrame.from_records(
            qs.values("dataset__name", "timestep", "value")
            ).rename(columns={"dataset__name": "dataset"})
        
        df.drop_duplicates(subset=["dataset", "timestep"], keep="first", inplace=True)
        
        df_pivot = df.pivot(index="timestep", columns="dataset", values="value").sort_index()
        chart_html = generate_chart_html(df_pivot)
    else:
        chart_html = None

    context = {
        "line_chart": chart_html,
        "all_scenarios": all_scenarios,
        "all_columns": all_columns,
        "selected_scenario_ids": selected_scenario_ids,
        "selected_scenarios": selected_scenarios,
        "selected_column_names": selected_column_names,
        "single_selected_column": single_selected_column,
    }

    return render(request, "scenario_analysis/compare_scenarios.html", context)


@login_required
@require_GET
def search_scenarios(request) -> HttpResponse:
    """
    HTMX view to return filtered scenario names based on input text.
    Only scenarios with status='done' and owned by the user are shown.
    """
    query = request.GET.get("scenario_search", "").strip()
    user = request.user

    results = ScenarioDataSet.objects.filter(user=user, status="done")
    if query:
        results = results.filter(name__icontains=query)

    return render(
        request,
        "scenario_analysis/partials/scenario_suggestions.html",
        {
            "scenarios": results,
        },
    )


@login_required
@require_GET
def search_columns(request) -> HttpResponse:
    """
    HTMX view to return column names based on selected scenarios.
    """
    scenario_ids = request.GET.getlist("scenario_ids")
    user = request.user

    # Collect column names from selected scenarios
    columns = set()
    datasets = ScenarioDataSet.objects.filter(
        id__in=scenario_ids, user=user, status="done"
    )
    for ds in datasets:
        columns.update(ds.column_names or [])

    query = request.GET.get("column_search", "").strip().lower()
    filtered = sorted([col for col in columns if query in col.lower()])

    return render(
        request,
        "scenario_analysis/partials/column_suggestions.html",
        {
            "columns": filtered,
        },
    )


@require_POST
@login_required
def add_scenario_to_pill(request) -> HttpResponse:
    """
    Renders all selected scenarios as pills.
    Expects GET param: scenario_ids (UUID list)
    """
    scenario_ids = request.GET.getlist("scenario_ids")
    scenario_ids = [UUID(sid) for sid in scenario_ids if sid]  # validate UUIDs

    datasets = ScenarioDataSet.objects.filter(
        id__in=scenario_ids, user=request.user, status="done"
    )

    return render(
        request,
        "scenario_analysis/partials/scenario_pills.html",
        {
            "scenarios": datasets,
        },
    )


@login_required
@require_GET
def add_column_to_pill(request) -> HttpResponse:
    """
    Renders all selected columns as pills.
    Expects GET param: column_names (string list)
    """
    column_names = request.GET.getlist("column_names")

    return render(
        request,
        "scenario_analysis/partials/column_pills.html",
        {
            "columns": column_names,
        },
    )

@login_required
def update_line_chart(request) -> HttpResponse:
    selected_column   = request.GET.get("single-selected-column")
    selected_scenarios = request.GET.getlist("selected_scenario_ids")

    if not selected_column or not selected_scenarios:
        return HttpResponse("<p class='text-center text-gray-500'>No data selected.</p>")

    qs = ScenarioValue.objects.filter(
        variable=selected_column,
        dataset_id__in=selected_scenarios
    ).select_related("dataset")

    df = (
        pd.DataFrame.from_records(
            qs.values("dataset__name", "timestep", "value")
        )
        .rename(columns={"dataset__name": "dataset"})
        .drop_duplicates(subset=["dataset", "timestep"], keep="first")
    )

    if df.empty:
        return HttpResponse("<p class='text-center text-gray-500'>No data to plot.</p>")

    pivot = (
        df.pivot(index="timestep", columns="dataset", values="value").sort_index()
    )

    return HttpResponse(generate_chart_html(pivot))



def generate_chart_html(df):
    fig = go.Figure()

    for scenario in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df[scenario],
            mode="lines", name=scenario
        ))

    fig.update_layout(
        title="Scenario Comparison",
        xaxis_title="Timestep",
        yaxis_title="Value",
        template="plotly_white",
        autosize=True,          # let Plotly fill width
        height=500,
        margin=dict(l=40, r=20, t=40, b=40),
    )
    return fig.to_html(full_html=False)
