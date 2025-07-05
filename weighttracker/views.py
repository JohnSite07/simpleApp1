from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .forms import WeightEntryForm, DateRangeFilterForm
from .models import WeightTrackerElements
import json
from typing import List
from datetime import datetime

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
    
    # Handle date range filtering
    filter_form = DateRangeFilterForm(request.GET)
    entries = WeightTrackerElements.objects.filter(user=request.user).order_by('date')
    
    if filter_form.is_valid():
        start_date = filter_form.cleaned_data.get('start_date')
        end_date = filter_form.cleaned_data.get('end_date')
        
        if start_date:
            entries = entries.filter(date__gte=start_date)
        if end_date:
            entries = entries.filter(date__lte=end_date)
    
    existing_entries = WeightTrackerElements.objects.filter(user=request.user)
    dates = [entry.date.strftime("%Y-%m-%d") for entry in entries]
    weights = [float(entry.weight_kg) for entry in entries]

    context = {
        'weight_form': weight_form,
        'filter_form': filter_form,
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