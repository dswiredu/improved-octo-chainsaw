from django.http import JsonResponse

class HTMXAuthMiddleware:
    """
    If an HTMX request is received and the user is not authenticated,
    respond with a 403 and an HX-Redirect header to the login page.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Before view logic
        if request.headers.get("HX-Request") == "true" and not request.user.is_authenticated:
            return JsonResponse(
                {"error": "Authentication required"},
                status=403,
                headers={"HX-Redirect": "/accounts/login/"}
            )

        # Proceed to view
        return self.get_response(request)