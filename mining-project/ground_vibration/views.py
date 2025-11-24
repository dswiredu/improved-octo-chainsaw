from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

# Create your views here.
def index(request: HttpRequest) -> HttpResponse:
    models = ["Ghosh (1983)", "Tarkwa Model"]
    context = {
        "models": models
    }
    return render(request, "ground_vibration/index.html", context=context)