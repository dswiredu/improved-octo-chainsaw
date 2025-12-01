"""
forms.py

Django Form classes for the Ground Vibration PPV models 10–19.
Each form corresponds directly to a compute function in vibration_models.py.

All fields are required. Validation is handled automatically by Django.
"""

from django import forms


# ============================================================
# Model 10 — Ghosh-Daemen (1983)
# ============================================================

class Model10Form(forms.Form):
    K = forms.FloatField(required=True, help_text="Site constant K")
    beta = forms.FloatField(required=True, help_text="Attenuation exponent β")
    alpha = forms.FloatField(required=True, help_text="Damping factor α")



# ============================================================
# Model 11 — Ghosh (1983)
# ============================================================

class Model11Form(forms.Form):
    K = forms.FloatField(required=True)
    a = forms.FloatField(required=True, help_text="Exponent on W")
    n = forms.FloatField(required=True, help_text="Exponent on D")
    alpha = forms.FloatField(required=True)



# ============================================================
# Model 12 — Gupta et al. (1987)
# ============================================================

class Model12Form(forms.Form):
    K = forms.FloatField(required=True)
    beta = forms.FloatField(required=True)
    alpha = forms.FloatField(required=True, help_text="Exponent in exp(-αK). To verify.")



# ============================================================
# Model 13 — Gupta et al. (1988)
# ============================================================

class Model13Form(forms.Form):
    K = forms.FloatField(required=True)
    beta = forms.FloatField(required=True)
    alpha = forms.FloatField(required=True, help_text="Multiplier for D/W inside exponential")



# ============================================================
# Model 14 — CMRI / CMSR (1991/1993)
# ============================================================

class Model14Form(forms.Form):
    n = forms.FloatField(required=True, help_text="Constant n")
    K = forms.FloatField(required=True, help_text="Coefficient K")



# ============================================================
# Model 15 — Bilgin et al. (1998)
# ============================================================

class Model15Form(forms.Form):
    K = forms.FloatField(required=True)
    d = forms.FloatField(required=True, help_text="Exponent d on (D / W^0.5)")
    B = forms.FloatField(required=True, help_text="Site constant B")
    beta = forms.FloatField(required=True, help_text="Exponent β on B")



# ============================================================
# Model 16 — Arshadnejad et al. (2013)
# ============================================================

class Model16Form(forms.Form):
    a = forms.FloatField(required=True, help_text="Scale factor a")
    RMR = forms.FloatField(required=True, help_text="Rock Mass Rating (RMR)")
    b = forms.FloatField(required=True, help_text="Exponent on RMR")
    B = forms.FloatField(required=True, help_text="Site factor B")
    alpha = forms.FloatField(required=True, help_text="Damping factor α")



# ============================================================
# Model 17 — Yilmaz (2016), Variant A
# ============================================================

class Model17Form(forms.Form):
    K = forms.FloatField(required=True)
    beta = forms.FloatField(required=True)
    alpha = forms.FloatField(required=True, help_text="Multiplier in exp(α*(...))")



# ============================================================
# Model 18 — Yilmaz (2016), Variant B
# ============================================================

class Model18Form(forms.Form):
    K = forms.FloatField(required=True)
    beta = forms.FloatField(required=True)
    alpha = forms.FloatField(required=True)



# ============================================================
# Model 19 — Afum & Amegbery (2016)
# ============================================================

class Model19Form(forms.Form):
    a = forms.FloatField(required=True, help_text="Coefficient for first term a*(W^d / D^c)")
    d = forms.FloatField(required=True, help_text="Exponent d on W in both terms")
    c = forms.FloatField(required=True, help_text="Exponent c on D in both terms")
    K = forms.FloatField(required=True, help_text="Coefficient K used in second term K^b")
    b = forms.FloatField(required=True, help_text="Exponent b applied to K and inner ratio")
    e = forms.FloatField(required=True, help_text="Exponent coefficient in exp(-e * D/W)")
