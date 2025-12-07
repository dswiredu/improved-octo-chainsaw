from .forms import (
    Model1Form,
    Model2Form,
    Model3Form,
    Model4Form,
    Model5Form,
)

from .blast_models import (
    compute_model_1_holmberg_persson_a,
    compute_model_2_holmberg_persson_b,
    compute_model_3_ollofson_persson,
    compute_model_4_kuzu,
    compute_model_5_national_association,
)


MODEL_REGISTRY = {

    "model_1": {
        "label": "Holmberg & Persson (1978a)",
        "form": Model1Form,
        "compute": compute_model_1_holmberg_persson_a,
    },

    "model_2": {
        "label": "Holmberg & Persson (1978b)",
        "form": Model2Form,
        "compute": compute_model_2_holmberg_persson_b,
    },

    "model_3": {
        "label": "Ollofson (1990) & Persson et al. (1994)",
        "form": Model3Form,
        "compute": compute_model_3_ollofson_persson,
    },

    "model_4": {
        "label": "Kuzu et al. (2009)",
        "form": Model4Form,
        "compute": compute_model_4_kuzu,
    },

    "model_5": {
        "label": "National Association of Australian State",
        "form": Model5Form,
        "compute": compute_model_5_national_association,
    },
}
