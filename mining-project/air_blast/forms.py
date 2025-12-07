from django import forms

NUMBER = forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "any"})


# ------------------------------------------------------------
# Model 1 — Holmberg & Persson (1978a)
# ------------------------------------------------------------
class Model1Form(forms.Form):
    """Model 1: Holmberg & Persson (1978a)."""
    k = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant k")
    P0 = forms.FloatField(required=True, widget=NUMBER, help_text="Reference pressure P₀")


# ------------------------------------------------------------
# Model 2 — Holmberg & Persson (1978b)
# ------------------------------------------------------------
class Model2Form(forms.Form):
    """Model 2: Holmberg & Persson (1978b)."""
    k = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant k")
    P0 = forms.FloatField(required=True, widget=NUMBER, help_text="Reference pressure P₀")
    a = forms.FloatField(required=True, widget=NUMBER, help_text="Exponent a")


# ------------------------------------------------------------
# Model 3 — Ollofson (1990) & Persson et al. (1994)
# ------------------------------------------------------------
class Model3Form(forms.Form):
    """Model 3: Ollofson (1990) & Persson et al. (1994)."""
    P0 = forms.FloatField(required=True, widget=NUMBER, help_text="Reference pressure P₀")


# ------------------------------------------------------------
# Model 4 — Kuzu et al. (2009)
# ------------------------------------------------------------
class Model4Form(forms.Form):
    """Model 4: Kuzu et al. (2009)."""
    k = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant k")
    beta = forms.FloatField(required=True, widget=NUMBER, help_text="Exponent β")


# ------------------------------------------------------------
# Model 5 — National Association of Australian State
# ------------------------------------------------------------
class Model5Form(forms.Form):
    """Model 5: National Association of Australian State."""
    P0 = forms.FloatField(required=True, widget=NUMBER, help_text="Reference pressure P₀")
