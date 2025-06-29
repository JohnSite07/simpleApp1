from django.shortcuts import render, redirect, get_object_or_404
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

# Delete entry
def delete_entry(request, entry_id):
    entry = get_object_or_404(WeightTrackerElements, id=entry_id)
    entry.delete()
    return redirect('weighttrackerhome')