from django.shortcuts import render

# Create your views here.
def weighttrakerhome(request):
    context = {}
    return render(request, "weighttracker\weighttrackerhome.html", context)