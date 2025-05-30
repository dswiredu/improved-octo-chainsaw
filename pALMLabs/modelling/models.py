from django.db import models
from django.utils import timezone


class SDACurveInputs(models.Model):
    uploaded_at = models.DateTimeField(default=timezone.now)
    security_file = models.FileField(upload_to="sda_inputs/security/")
    curve_file = models.FileField(upload_to="sda_inputs/curves/")
    psa = models.FloatField()
    sda = models.FloatField()
    success = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"SDA Run {self.id} - {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"
    
    def has_cached_results(self) -> bool:
        return hasattr(self, "metrics") and self.metrics.cashflows.exists()


class SDACurveRunMetrics(models.Model):
    run = models.OneToOneField(
        "SDACurveInputs", on_delete=models.CASCADE, related_name="metrics"
    )
    original_balance = models.FloatField()
    WAL = models.FloatField()
    coupon_rate = models.FloatField()
    face_value = models.FloatField()

    def __str__(self):
        return f"Metrics for Run {self.run.id}"


class SDACurveCashFlows(models.Model):
    run_metrics = models.ForeignKey(
        SDACurveRunMetrics, on_delete=models.CASCADE, related_name="cashflows"
    )
    timestep = models.IntegerField()
    balance = models.FloatField()
    interest = models.FloatField()
    default = models.FloatField()
    prepayment = models.FloatField()
    principal = models.FloatField()
    totalcf = models.FloatField()

    def __str__(self):
        return f"Cashflow Period {self.timestep} (Run {self.run_metrics.run.id})"
