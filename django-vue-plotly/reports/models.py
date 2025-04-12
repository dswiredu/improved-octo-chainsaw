from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class ReportRun(models.Model):
    REPORT_CHOICES = [
        ('performance', 'Performance Summary'),
        ('risk', 'Risk & Return'),
        ('compare', 'Compare With Peers'),
    ]

    ticker = models.CharField(max_length=10)
    report_type = models.CharField(max_length=50, choices=REPORT_CHOICES)
    run_by = models.ForeignKey(User, on_delete=models.CASCADE)
    run_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('success', 'Success'), ('fail', 'Fail')], default='success')
    pdf_file = models.FileField(upload_to='reports/', null=True, blank=True)  # Optional
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.ticker} - {self.report_type} - {self.run_at.strftime('%Y-%m-%d %H:%M')}"
