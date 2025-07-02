from django import forms
from .models import WeightTrackerElements

class WeightEntryForm(forms.ModelForm):
    class Meta:
        model = WeightTrackerElements
        exclude = ['user']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }