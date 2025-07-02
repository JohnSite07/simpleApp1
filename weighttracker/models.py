from django.db import models
from django.utils import timezone
from django.conf import settings

# Create your models here.
class WeightTrackerElements(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='weight_entries', null=True, blank=True)
    date = models.DateField(default=timezone.now, help_text="Date of measurement")
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in Kilograms")
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.date.strftime('%Y-%m-%d')}: {self.weight_kg} Kg ({self.notes})"
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Weight Entries"