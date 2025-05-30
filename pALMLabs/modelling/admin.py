from django.contrib import admin
from .models import *

# Register your models here.
class SDACurveInputsAdmin(admin.ModelAdmin):
    list_display = (
        "uploaded_at",
        "security_file",
        "curve_file",
        "psa",
        "sda",
        "success",
    )

class SDACurveRunMetricsAdmin(admin.ModelAdmin):
    list_display = (
        "run__uploaded_at",
        "original_balance",
        "WAL",
        "coupon_rate",
        "face_value",
    )

class SSDACurveCashFlowsAdmin(admin.ModelAdmin):
    list_display = (
        "run_metrics__run__uploaded_at",
        "timestep",
        "balance",
        "interest",
        "default",
        "prepayment",
        "principal",
        "totalcf",
    )


admin.site.register(SDACurveInputs, SDACurveInputsAdmin)
admin.site.register(SDACurveRunMetrics, SDACurveRunMetricsAdmin)
admin.site.register(SDACurveCashFlows, SSDACurveCashFlowsAdmin)
