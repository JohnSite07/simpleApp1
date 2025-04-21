from django.shortcuts import render

# Create your views here.
def homepage(request):
    context = {}
    return render(request, "home\homepage.html", context)