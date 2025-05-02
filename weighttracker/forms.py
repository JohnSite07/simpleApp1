from django import forms
from .models import WeightTrackerElements

class WeightEntryForm(forms.ModelForm):
    class Meta:
        model = WeightTrackerElements
        fields = ['date', 'weight_kg', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }