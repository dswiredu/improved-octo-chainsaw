from .forms import (
    Model1Form, Model2Form, Model3Form, Model4Form, Model5Form,
    Model6Form, Model7Form, Model8Form, Model9Form, Model10Form,
    Model11Form, Model12Form, Model13Form, Model14Form, Model15Form,
    Model16Form, Model17Form, Model18Form, Model19Form, Model20Form
)

from .vibration_models import (
    compute_model_1_morris,
    compute_model_2_usbm,
    compute_model_3_lk,
    compute_model_4_davies,
    compute_model_5_ah,
    compute_model_6_bis,
    compute_model_7_lundberg,
    compute_model_8_just_free,
    compute_model_9_gd,
    compute_model_10_gd_alt,
    compute_model_11_ghosh,
    compute_model_12_gupta87,
    compute_model_13_gupta88,
    compute_model_14_cmri,
    compute_model_15_bilgin,
    compute_model_16_arshad,
    compute_model_17_yilmaz,
    compute_model_18_yilmaz_alt,
    compute_model_19_gustaffson,
    compute_model_20_afum
)


MODEL_REGISTRY = {

    "model_1": {
        "label": "Morris (1950)",
        "form": Model1Form,
        "compute": compute_model_1_morris,
    },

    "model_2": {
        "label": "USBM (1959)",
        "form": Model2Form,
        "compute": compute_model_2_usbm,
    },

    "model_3": {
        "label": "Langefors–Kihlstrom (1963)",
        "form": Model3Form,
        "compute": compute_model_3_lk,
    },

    "model_4": {
        "label": "Davies et al. (1963)",
        "form": Model4Form,
        "compute": compute_model_4_davies,
    },

    "model_5": {
        "label": "Ambraseys–Hendron (1968)",
        "form": Model5Form,
        "compute": compute_model_5_ah,
    },

    "model_6": {
        "label": "Bureau of Indian Standard (1973)",
        "form": Model6Form,
        "compute": compute_model_6_bis,
    },

    "model_7": {
        "label": "Lundberg (1977)",
        "form": Model7Form,
        "compute": compute_model_7_lundberg,
    },

    "model_8": {
        "label": "Just & Free (1980)",
        "form": Model8Form,
        "compute": compute_model_8_just_free,
    },

    "model_9": {
        "label": "Ghosh–Daemen (1983)",
        "form": Model9Form,
        "compute": compute_model_9_gd,
    },

    "model_10": {
        "label": "Ghosh–Daemen Alt (1983)",
        "form": Model10Form,
        "compute": compute_model_10_gd_alt,
    },

    "model_11": {
        "label": "Ghosh (1983)",
        "form": Model11Form,
        "compute": compute_model_11_ghosh,
    },

    "model_12": {
        "label": "Gupta et al. (1987)",
        "form": Model12Form,
        "compute": compute_model_12_gupta87,
    },

    "model_13": {
        "label": "Gupta et al. (1988)",
        "form": Model13Form,
        "compute": compute_model_13_gupta88,
    },

    "model_14": {
        "label": "CMRI / CMSR (1991/1993)",
        "form": Model14Form,
        "compute": compute_model_14_cmri,
    },

    "model_15": {
        "label": "Bilgin et al. (1998)",
        "form": Model15Form,
        "compute": compute_model_15_bilgin,
    },

    "model_16": {
        "label": "Arshadnejad et al. (2013)",
        "form": Model16Form,
        "compute": compute_model_16_arshad,
    },

    "model_17": {
        "label": "Yilmaz (2016)",
        "form": Model17Form,
        "compute": compute_model_17_yilmaz,
    },

    "model_18": {
        "label": "Yilmaz (2016a)",
        "form": Model18Form,
        "compute": compute_model_18_yilmaz_alt,
    },

    "model_19": {
        "label": "Gustaffson",
        "form": Model19Form,
        "compute": compute_model_19_gustaffson,
    },

    "model_20": {
        "label": "Afum & Amegbey (2016)",
        "form": Model20Form,
        "compute": compute_model_20_afum,
    },
}
