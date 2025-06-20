from django.http import HttpRequest

def sidebar_nav_items(request: HttpRequest):
    current_url = request.resolver_match.url_name if request.resolver_match else None

    nav_items = [
        {
            "label": "Modelling",
            "icon": "fa-flask-vial",
            "items": [
                {"label": "SDA Curve", "url_name": "modelling:s-curve-load", "icon": "fa-chart-line"},
            ],
        },
        {
            "label": "Scenario Analysis",
            "icon": "fa-diagram-project",
            "items": [
                {"label": "Load Scenario Data", "url_name": "scenario_analysis:upload-scenarios", "icon": "fa-upload"},
                {"label": "Compare Scenarios", "url_name": "scenario_analysis:compare-scenarios", "icon": "fa-code-compare"},
            ],
        },
    ]

    for section in nav_items:
        section["active"] = any(item["url_name"] == current_url for item in section["items"])
        for item in section["items"]:
            item["active"] = item["url_name"] == current_url

    return {"sidebar_nav_items": nav_items}


# Can be used to specify what users see based on permissions.
# if user.is_superuser:
#         # Admin-only section
#         nav.append({
#             "label": "Admin Tools",
#             "icon": "fa-tools",
#             "items": [
#                 {"label": "User Logs", "url_name": "admin-logs", "icon": "fa-scroll"},
#                 {"label": "Data Review", "url_name": "admin-data-review", "icon": "fa-database"},
#             ],
#         })
