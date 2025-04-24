from django.shortcuts import render
from django.urls import resolve

# Create your views here.

def index(request):
    view_name = resolve(request.path).view_name
    context = {
        "view_name": view_name
    }
    return render(request, 'index.html', context=context)