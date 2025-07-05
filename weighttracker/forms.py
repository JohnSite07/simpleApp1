from django import forms
from .models import WeightTrackerElements

class WeightEntryForm(forms.ModelForm):
    class Meta:
        model = WeightTrackerElements
        exclude = ['user']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'})
        }

class DateRangeFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'border rounded px-3 py-2'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'border rounded px-3 py-2'})
    )