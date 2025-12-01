"""
model_registry.py

Central registry mapping model keys → label, form class, compute function.

This provides:
- Clean lookup for HTMX partial form rendering
- Clean mapping for backend compute routing
- Easy extensibility for adding new PPV models
"""

from .forms import (
    Model10Form,
    Model11Form,
    Model12Form,
    Model13Form,
    Model14Form,
    Model15Form,
    Model16Form,
    Model17Form,
    Model18Form,
    Model19Form,
)

from .vibration_models import (
    compute_model_10_ghosh_daemen_1983,
    compute_model_11_ghosh_1983,
    compute_model_12_gupta_1987,
    compute_model_13_gupta_1988,
    compute_model_14_cmri_1991,
    compute_model_15_bilgin_1998,
    compute_model_16_arshadnejad_2013,
    compute_model_17_yilmaz_2016_A,
    compute_model_18_yilmaz_2016_B,
    compute_model_19_afum_amegbery_2016,
)


# ============================================================
# MODEL REGISTRY
# ============================================================

MODEL_REGISTRY = {
    "model_10": {
        "label": "Ghosh-Daemen (1983)",
        "form": Model10Form,
        "compute": compute_model_10_ghosh_daemen_1983,
    },

    "model_11": {
        "label": "Ghosh (1983)",
        "form": Model11Form,
        "compute": compute_model_11_ghosh_1983,
    },

    "model_12": {
        "label": "Gupta et al. (1987)",
        "form": Model12Form,
        "compute": compute_model_12_gupta_1987,
    },

    "model_13": {
        "label": "Gupta et al. (1988)",
        "form": Model13Form,
        "compute": compute_model_13_gupta_1988,
    },

    "model_14": {
        "label": "CMRI / CMSR (1991/1993)",
        "form": Model14Form,
        "compute": compute_model_14_cmri_1991,
    },

    "model_15": {
        "label": "Bilgin et al. (1998)",
        "form": Model15Form,
        "compute": compute_model_15_bilgin_1998,
    },

    "model_16": {
        "label": "Arshadnejad et al. (2013)",
        "form": Model16Form,
        "compute": compute_model_16_arshadnejad_2013,
    },

    "model_17": {
        "label": "Yilmaz (2016) – Variant A",
        "form": Model17Form,
        "compute": compute_model_17_yilmaz_2016_A,
    },

    "model_18": {
        "label": "Yilmaz (2016) – Variant B",
        "form": Model18Form,
        "compute": compute_model_18_yilmaz_2016_B,
    },

    "model_19": {
        "label": "Afum & Amegbery (2016)",
        "form": Model19Form,
        "compute": compute_model_19_afum_amegbery_2016,
    },
}
