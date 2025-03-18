import os
import time
import datetime
import subprocess

from django.shortcuts import render
from django.utils.html import escape
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .models import ScriptExecution


# TODO : Improve the UI for streamed logs?
#      : Allow filtering logs by execution status?
#      : Implement a frontend message when a script is killed due to timeout?
#      : Let users customize the timeout for each script?
#      : Add a "Stop Script" button to cancel execution?
#      : Format logs better (timestamps, colors, etc.)?
#      : Allow admins to view all user logs?
#      : Download logs as a CSV file?
#      : Allow UI selection of log levels instead of typing them manually?
#      : Ensure script execution updates the UI dynamically when it finishes?
#      : Show a "Running..." indicator when executing a script?
#      : How should I structure permissions for multi-user access in my Django app?


SCRIPTS_DIR = os.path.join(settings.BASE_DIR, "rundeck", "scripts")


def _get_ui_friendly_scriptname(filename: str) -> str:
    return filename.replace("_", " ").replace(".py", "").title()


def list_scripts():
    """Return a list of available scripts with user-friendly names, or raise an error if none exist."""

    if not os.path.isdir(SCRIPTS_DIR):
        raise FileNotFoundError(f"Scripts directory '{SCRIPTS_DIR}' not found!")

    script_files = [f for f in os.listdir(SCRIPTS_DIR) if f.endswith(".py") and "utils" not in f]

    if not script_files:
        raise FileNotFoundError("No scripts found in the scripts directory!")

    # Return user-friendly names
    return [
        {"filename": f, "friendly_name": _get_ui_friendly_scriptname(f)}
        for f in script_files
    ]


@login_required
def rundeck_view(request):
    """Render the script execution page with user-friendly script names."""
    error_message = None

    try:
        scripts = list_scripts()
    except FileNotFoundError as e:
        scripts = []
        error_message = str(e)

    return render(request, "rundeck/index.html", {"scripts": scripts, "error": error_message})



@login_required
def execute_script(request):
    """Run the script, save logs, and return an HTML snippet for HTMX to swap in."""
    if request.method != "POST":
        return HttpResponse("<p class='text-red-600'>❌ Invalid request method.</p>")

    script_name = request.POST.get("script")
    arguments = request.POST.get("arguments", "").strip()

    if not script_name:
        return HttpResponse("<p class='text-red-600'>❌ No script selected.</p>")

    script_path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.isfile(script_path):
        return HttpResponse(f"<p class='text-red-600'>❌ Script '{script_name}' not found.</p>")

    # Start timing
    start_time = datetime.datetime.now()
    logs = []
    try:
        # Run script
        arg_list = arguments.split() if arguments else []
        process = subprocess.Popen(
            ["python3", script_path] + arg_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Capture stdout
        stdout, stderr = process.communicate()
        if stdout:
            logs.append(stdout.strip())
        if stderr:
            logs.append(f"ERROR: {stderr.strip()}")

        # Check success
        success = (process.returncode == 0)

    except Exception as e:
        logs.append(f"Unexpected Execution Error: {str(e)}")
        success = False

    duration = datetime.datetime.now() - start_time

    # Save logs to database
    execution = ScriptExecution.objects.create(
        user=request.user,
        script_name=script_name,
        arguments=arguments,
        output="\n".join(logs),
        success=success,
        duration=duration.total_seconds()
    )

    if success:
        # Return an HTML snippet that includes a hidden <div> to auto-fetch logs
        return HttpResponse(
            f"""
            <div class="text-green-700 font-semibold">✅ Script executed successfully!</div>
            <div hx-get="/rundeck/execution-logs/{execution.id}/"
                 hx-trigger="load"
                 hx-target="#log-container"
                 hx-swap="innerHTML"></div>
            """,
            content_type="text/html"
        )
    else:
        return HttpResponse(
            f"""
            <div class="text-red-600 font-semibold">❌ Script execution failed!</div>
            <div hx-get="/rundeck/execution-logs/{execution.id}/"
                 hx-trigger="load"
                 hx-target="#log-container"
                 hx-swap="innerHTML"></div>
            """,
            content_type="text/html"
        )

@login_required
def get_execution_logs(request, execution_id):
    """Fetch logs for a completed script execution."""
    try:
        execution = ScriptExecution.objects.get(id=execution_id, user=request.user)
        safe_logs = escape(execution.output)  # Escape logs to prevent HTML issues
        return HttpResponse(safe_logs, content_type="text/plain")
    except ScriptExecution.DoesNotExist:
        return HttpResponse("<p class='text-red-600'>Logs not found.</p>", content_type="text/html")

@login_required
def execution_logs(request):
    """Show past script execution logs."""
    logs = ScriptExecution.objects.filter(user=request.user).order_by("-timestamp")[:20]
    return render(request, "rundeck/logs.html", {"logs": logs})