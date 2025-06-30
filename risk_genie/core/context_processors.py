from django.http import HttpRequest
from typing import Optional, Any

def sidebar_nav_items(request: HttpRequest) -> dict[str, list[dict[str, Any]]]:
    current_url = request.resolver_match.url_name if request.resolver_match else None

    nav_items = [
        {
            "label": "Data Quality",
            "icon": "fa-shield-halved",
            "items": [
                {"label": "Overview", "url_name": "data_quality:overview", "icon": "fa-circle-check"},
            ],
        },
    ]

    for section in nav_items:
        section["active"] = any(item["url_name"] == current_url for item in section["items"])
        for item in section["items"]:
            item["active"] = item["url_name"] == current_url

    return {"sidebar_nav_items": nav_items}