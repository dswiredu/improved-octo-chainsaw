from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

# Create your views here.

def index(request: HttpRequest) -> HttpResponse:
    context = {
        "curr_url": request.resolver_match.url_name
    }
    return render(request, "index.html", context=context)