from django.db import models
from django.utils import timezone


class Alert(models.Model):
    class Severity(models.TextChoices):
        CRITICAL = "critical", "Critical"
        WARNING = "warning", "Warning"
        INFO = "info", "Info"

    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    severity = models.CharField(max_length=8, choices=Severity.choices)
    source = models.CharField(max_length=255)
    metric_name = models.CharField(max_length=255)
    metric_value = models.FloatField()
    threshold = models.FloatField()
    created_at = models .DateTimeField(default=timezone.now)

    class Meta:
        db_table = "alerts"
        ordering = ["id"]