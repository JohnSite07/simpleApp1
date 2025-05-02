from django.shortcuts import render, redirect
from .forms import WeightEntryForm
from .models import WeightTrackerElements

# Create your views here.
def weighttrakerhome(request):
    if request.method == 'POST':
        weight_form = WeightEntryForm(request.POST)
        if weight_form.is_valid():
            weight_form.save()
            return redirect('weighttrackerhome')
    else:
        weight_form = WeightEntryForm()
    
    existing_entries = WeightTrackerElements.objects.all()

    context = {
        'weight_form': weight_form,
        'entries': existing_entries
    }
    return render(request, "weighttracker\weighttrackerhome.html", context)