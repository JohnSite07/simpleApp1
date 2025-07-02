from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import WeightEntryForm
from .models import WeightTrackerElements
import json
from typing import List

# Create your views here.
@login_required
def weighttrakerhome(request):
    if request.method == 'POST':
        weight_form = WeightEntryForm(request.POST)
        if weight_form.is_valid():
            entry = weight_form.save(commit=False)
            entry.user = request.user
            entry.save()
            return redirect('weighttrackerhome')
    else:
        weight_form = WeightEntryForm()
    
    existing_entries = WeightTrackerElements.objects.filter(user=request.user)
    entries = WeightTrackerElements.objects.filter(user=request.user).order_by('date')
    dates = [entry.date.strftime("%Y-%m-%d") for entry in entries]
    weights = [float(entry.weight_kg) for entry in entries]

    context = {
        'weight_form': weight_form,
        'entries': existing_entries,
        'weight_entries': entries,
        'chart_labels': json.dumps(dates),
        'chart_data': json.dumps(weights)
    }
    return render(request, "weighttracker/weighttrackerhome.html", context)

# Delete entry
@login_required
def delete_entry(request, entry_id):
    entry = get_object_or_404(WeightTrackerElements, id=entry_id, user=request.user)
    entry.delete()
    return redirect('weighttrackerhome')