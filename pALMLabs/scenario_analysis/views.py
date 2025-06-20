from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST

from .forms import ScenarioUploadForm
from .models import ScenarioDataSet
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
def compare_scenarios(request):
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

    context = {
        "all_scenarios": all_scenarios,
        "all_columns": all_columns,
        "selected_scenario_ids": selected_scenario_ids,
        "selected_scenarios": selected_scenarios,
        "selected_column_names": selected_column_names,
    }

    return render(request, "scenario_analysis/compare_scenarios.html", context)


@login_required
@require_GET
def search_scenarios(request):
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
def search_columns(request):
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


from uuid import UUID


@require_POST
@login_required
def add_scenario_to_pill(request):
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
def add_column_to_pill(request):
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
