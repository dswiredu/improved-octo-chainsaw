from django.shortcuts import redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.http import url_has_allowed_host_and_scheme

@ensure_csrf_cookie
def post_login_redirect(request):
    redirect_to = request.GET.get("next") or "/"
    if not url_has_allowed_host_and_scheme(redirect_to, allowed_hosts={request.get_host()}):
        redirect_to = "/"
    return redirect(redirect_to)
