import json
from django.http import HttpRequest
from django.shortcuts import render
from typing import Optional, Any

import pandas as pd
import plotly.express as px


def overview(request: HttpRequest):
    # Example hardcoded date – this can come from a query param later
    date_str = "2025-06-20"
    file_path = fr"C:\Users\dwiredu\OneDrive - AGAM CAPITAL MANAGEMENT, LLC\Documents\repos\schema_reports\26N\{date_str}.json"

    with open(file_path) as f:
        data = json.load(f)

    # Extract core stats
    total_checks = data["statistics"]["evaluated_expectations"]
    passed = data["statistics"]["successful_expectations"]
    failed = data["statistics"]["unsuccessful_expectations"]
    success_rate = round(data["statistics"]["success_percent"], 1)
    total_records = next(
        r["result"]["element_count"] for r in data["results"] if "element_count" in r["result"]
    )
    run_date = data["meta"]["run_id"]["run_time"][:10]

    previous_stats = {
        "Passed": 5,
        "Failed": 7,
    }

    current_passed = data["statistics"]["successful_expectations"]
    current_failed = data["statistics"]["unsuccessful_expectations"]

    def pct_change(curr, prev) -> None | Any:
        if prev == 0:
            return None
        return round(((curr - prev) / prev) * 100, 1)

    delta_passed = pct_change(current_passed, previous_stats["Passed"])
    delta_failed = pct_change(current_failed, previous_stats["Failed"])

    # Define the cards
    stats_cards = [
        {
            "title": "Total Records",
            "icon": "fa-database",
            "value": f"{total_records:,}",
            "subtext": "Rows evaluated",
        },
        {
            "title": "Total Checks",
            "icon": "fa-clipboard-list",
            "value": total_checks,
            "subtext": "# of expectations",
        },
        {
            "title": "Passed Checks",
            "icon": "fa-circle-check",
            "value": passed,
            "subtext": f"{round(passed / total_checks * 100, 1)}% passed",
            "delta": delta_passed,
        },
        {
            "title": "Failed Checks",
            "icon": "fa-circle-xmark",
            "value": failed,
            "subtext": f"{round(failed / total_checks * 100, 1)}% failed",
            "delta": delta_failed,
        },
        {
            "title": "Success Rate",
            "icon": "fa-gauge-high",
            "value": f"{success_rate}%",
            "subtext": "Target ≥ 90%",
        },
    ]

    df = parse_validation_result_tests(data)
    bar_chart_html = build_plotly_bar(df)

    context = {
        "date_str": date_str,
        "run_date": run_date,
        "stats_cards": stats_cards,
        "results": data["results"],
        "bar_chart_html": bar_chart_html,
    }
    # print(stats_cards[2])

    return render(request, "data_quality/overview.html", context)


def parse_validation_result_tests(validation_result):
    tests = []

    for result in validation_result.get("results", []):
        expectation_type = result["expectation_config"].get("expectation_type", "")
        if "expect_table" in expectation_type:
            continue  # Skip table-level expectations

        column = result["expectation_config"].get("kwargs", {}).get("column", "")
        total_count = result["result"].get("element_count")
        unexpected_count = result["result"].get("unexpected_count")

        if total_count is None or unexpected_count is None:
            continue

        passed_count = total_count - unexpected_count
        failed_count = unexpected_count

        # Labeling logic
        if "expect_column_values" in expectation_type and column:
            suffix = expectation_type.replace("expect_column_values_", "")
            label = f"{column}_{suffix}"
        else:
            label = expectation_type

        tests.append({"Test": label, "Status": "Passed", "Count": passed_count})
        tests.append({"Test": label, "Status": "Failed", "Count": failed_count})

    return pd.DataFrame(tests)




def build_plotly_bar(df: pd.DataFrame) -> str:
    fig = px.bar(
        df,
        x="Test",
        y="Count",
        color="Status",
        barmode="group",
        text="Count",
        color_discrete_map={
            "Passed": "rgba(34, 197, 94, 0.6)",   # Tailwind green-500 w/ opacity
            "Failed": "rgba(239, 68, 68, 0.6)",   # Tailwind red-500 w/ opacity
        },
        hover_name="Test",
    )

    fig.update_layout(
        xaxis_title="Expectation",
        yaxis_title="Count",
        legend_title="Status",
        margin=dict(t=30, b=80, l=40, r=20),
        height=500 + len(df["Test"].unique()) * 12,  # Taller chart
        template="none",  # No background styling
        plot_bgcolor="white",  # Match card background
        paper_bgcolor="white",
        xaxis=dict(showgrid=False),  # No vertical grid
        yaxis=dict(
            showgrid=True, gridcolor="rgba(211, 211, 211, 0.3)"
        ),  # Faint horizontal grid
        font=dict(color="#1f2937"),  # Text color to match the card
    )

    fig.update_traces(
        texttemplate='%{text}',
        textposition='outside',
        # width=0.5  # Slimmer bars
    )

    return fig.to_html(full_html=False, include_plotlyjs='cdn')
