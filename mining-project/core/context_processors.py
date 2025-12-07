from django.http import HttpRequest

def sidebar_nav_items(request):
    current_url = request.resolver_match.url_name if request.resolver_match else None

    nav_items = [
        {
            "label": "Ground Vibration",
            "icon": "fa-wave-square",
            "items": [
                {
                    "label": "Modelling",
                    "url_name": "ground-vibration-index",
                    "icon": "fa-chart-line"
                },
            ],
        },
        {
            "label": "Air Blast",
            "icon": "fa-wind",
            "items": [
                {
                    "label": "Modelling",
                    "url_name": "air-blast-index",
                    "icon": "fa-chart-line"
                },
            ],
        },
    ]

    # highlight logic
    for section in nav_items:
        section["active"] = any(item["url_name"] == current_url for item in section["items"])
        for item in section["items"]:
            item["active"] = (item["url_name"] == current_url)

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
