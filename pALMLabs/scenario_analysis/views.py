from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
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
                return render(request, "scenario_analysis/upload.html", {"form": form})

            files_by_name = {f.name: f for f in files}

            for scenario_name, filename in mapping.items():
                file_obj = files_by_name.get(filename)

                if not file_obj:
                    messages.warning(
                        request,
                        f"Mapping specifies '{filename}' for scenario '{scenario_name}', but file was not uploaded."
                    )
                    continue

                dataset = ScenarioDataSet.objects.create(
                    user=request.user,
                    name=scenario_name,
                    filename=filename,
                    status="processing"
                )
                dataset.log("Starting processing.")

                try:
                    process_scenario_file(file_obj, dataset)
                    messages.info(request, f"Processed scenario: {scenario_name}")
                except Exception as e:
                    dataset.status = "error"
                    dataset.log(f"❌ Processing failed: {str(e)}")
                    dataset.save(update_fields=["status", "logs"])
                    messages.error(request, f"Failed to process '{filename}' for scenario '{scenario_name}'.")

            messages.success(request, "Upload complete.")
            return redirect("scenario_analysis:upload_scenarios")
    else:
        form = ScenarioUploadForm()

    return render(request, "scenario_analysis/upload.html", {"form": form})

def compare_scenarios(request):
    pass