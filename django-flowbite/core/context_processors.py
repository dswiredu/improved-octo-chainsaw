from django.http import HttpRequest


def sidebar_nav_items(request: HttpRequest):
    current_view = (
        request.resolver_match.view_name if request.resolver_match else None
    )  # <- CHANGED

    nav_items = [
        # ─────────────────────────  your existing structure  ───────────────────────── #
        {
            "label": "Modelling",
            "icon": "fa-flask-vial",
            "items": [
                {
                    "label": "SDA Curve",
                    "url_name": "main:s-curve-load",
                    "icon": "fa-chart-line",
                },
                {"label": "Run Model", "url_name": "main:run-model", "icon": "fa-play"},
            ],
        },
        {
            "label": "Scenario Analysis",
            "icon": "fa-diagram-project",
            "items": [
                {
                    "label": "Upload Scenarios",
                    "url_name": "main:upload-scenarios",
                    "icon": "fa-upload",
                },
                {
                    "label": "Compare Scenarios",
                    "url_name": "main:compare-scenarios",
                    "icon": "fa-code-compare",
                },
                {
                    "label": "Reports",
                    "url_name": "main:reports",
                    "icon": "fa-file-lines",
                },
            ],
        },
        {
            "label": "Data Management",
            "icon": "fa-database",
            "url_name": "main:load",  # single-item section
        },
        {
            "label": "Documentation",
            "icon": "fa-book",
            "url_name": "main:docs",
        },
        {
            "label": "Admin",
            "icon": "fa-user-shield",
            "items": [
                {
                    "label": "Manage Users",
                    "url_name": "main:manage-users",
                    "icon": "fa-users-cog",
                },
                {"label": "Logs", "url_name": "main:view-logs", "icon": "fa-scroll"},
            ],
        },
        {
            "label": "Settings",
            "icon": "fa-gear",
            "items": [
                {
                    "label": "Preferences",
                    "url_name": "main:preferences",
                    "icon": "fa-sliders",
                },
                {"label": "API Keys", "url_name": "main:api-keys", "icon": "fa-key"},
            ],
        },
    ]

    # ───────────────────────  set active flags  ─────────────────────── #
    for section in nav_items:
        if "items" in section:
            for item in section["items"]:
                item["active"] = item["url_name"] == current_view
            section["active"] = any(item["active"] for item in section["items"])
        else:
            section["active"] = section["url_name"] == current_view

    return {"sidebar_nav_items": nav_items}
