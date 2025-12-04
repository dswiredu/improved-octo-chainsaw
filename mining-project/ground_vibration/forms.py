from django import forms

NUMBER = forms.NumberInput(attrs={"class": "input input-bordered w-full", "step": "any"})


# ------------------------------------------------------------
# Model 1 — Morris (1950)
# ------------------------------------------------------------
class Model1Form(forms.Form):
    """Model 1: Morris (1950)."""
    K = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant")


# ------------------------------------------------------------
# Model 2 — USBM (1959)
# ------------------------------------------------------------
class Model2Form(forms.Form):
    """Model 2: USBM (1959)."""
    K = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant")
    beta = forms.FloatField(required=True, widget=NUMBER, help_text="Attenuation exponent")


# ------------------------------------------------------------
# Model 3 — Langefors–Kihlstrom (1963)
# ------------------------------------------------------------
class Model3Form(forms.Form):
    """Model 3: Langefors–Kihlstrom (1963)."""
    K = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant")
    beta = forms.FloatField(required=True, widget=NUMBER, help_text="Attenuation exponent")


# ------------------------------------------------------------
# Model 4 — Davies et al. (1963)
# ------------------------------------------------------------
class Model4Form(forms.Form):
    """Model 4: Davies et al. (1963)."""
    K = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant")
    alpha = forms.FloatField(required=True, widget=NUMBER, help_text="Distance exponent")
    beta = forms.FloatField(required=True, widget=NUMBER, help_text="Charge exponent")


# ------------------------------------------------------------
# Model 5 — Ambraseys–Hendron (1968)
# ------------------------------------------------------------
class Model5Form(forms.Form):
    """Model 5: Ambraseys–Hendron (1968)."""
    K = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant")
    beta = forms.FloatField(required=True, widget=NUMBER, help_text="Attenuation exponent")


# ------------------------------------------------------------
# Model 6 — Bureau of Indian Standard (1973)
# ------------------------------------------------------------
class Model6Form(forms.Form):
    """Model 6: BIS (1973)."""
    K = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant")
    beta = forms.FloatField(required=True, widget=NUMBER, help_text="Attenuation exponent")


# ------------------------------------------------------------
# Model 7 — Lundberg (1977)
# ------------------------------------------------------------
class Model7Form(forms.Form):
    """Model 7: Lundberg (1977).  No parameters required."""
    pass


# ------------------------------------------------------------
# Model 8 — Just & Free (1980)
# ------------------------------------------------------------
class Model8Form(forms.Form):
    """Model 8: Just & Free (1980)."""
    K = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant")
    beta = forms.FloatField(required=True, widget=NUMBER, help_text="Attenuation exponent")
    alpha = forms.FloatField(required=True, widget=NUMBER, help_text="Exponential factor")


# ------------------------------------------------------------
# Model 9 — Ghosh–Daemen (1983)
# ------------------------------------------------------------
class Model9Form(forms.Form):
    """Model 9: Ghosh–Daemen (1983)."""
    K = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant")
    beta = forms.FloatField(required=True, widget=NUMBER, help_text="Attenuation exponent")
    alpha = forms.FloatField(required=True, widget=NUMBER, help_text="Decay factor")


# ------------------------------------------------------------
# Model 10 — Ghosh–Daemen (1983) Alt
# ------------------------------------------------------------
class Model10Form(forms.Form):
    """Model 10: Ghosh–Daemen (alt)."""
    K = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant")
    beta = forms.FloatField(required=True, widget=NUMBER, help_text="Attenuation exponent")
    alpha = forms.FloatField(required=True, widget=NUMBER, help_text="Decay factor")


# ------------------------------------------------------------
# Model 11 — Ghosh (1983)
# ------------------------------------------------------------
class Model11Form(forms.Form):
    """Model 11: Ghosh (1983)."""
    K = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant")
    a = forms.FloatField(required=True, widget=NUMBER, help_text="Charge exponent")
    n = forms.FloatField(required=True, widget=NUMBER, help_text="Distance exponent")
    alpha = forms.FloatField(required=True, widget=NUMBER, help_text="Decay factor")


# ------------------------------------------------------------
# Model 12 — Gupta et al. (1987)
# ------------------------------------------------------------
class Model12Form(forms.Form):
    """Model 12: Gupta et al. (1987)."""
    K = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant")
    beta = forms.FloatField(required=True, widget=NUMBER, help_text="Attenuation exponent")
    alpha = forms.FloatField(required=True, widget=NUMBER, help_text="Exponential factor")


# ------------------------------------------------------------
# Model 13 — Gupta et al. (1988)
# ------------------------------------------------------------
class Model13Form(forms.Form):
    """Model 13: Gupta et al. (1988)."""
    K = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant")
    beta = forms.FloatField(required=True, widget=NUMBER, help_text="Attenuation exponent")
    alpha = forms.FloatField(required=True, widget=NUMBER, help_text="Exponential factor")


# ------------------------------------------------------------
# Model 14 — CMRI/CMSR (1991/1993)
# ------------------------------------------------------------
class Model14Form(forms.Form):
    """Model 14: CMRI/CMSR."""
    n = forms.FloatField(required=True, widget=NUMBER, help_text="Offset term")
    K = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant")


# ------------------------------------------------------------
# Model 15 — Bilgin et al. (1998)
# ------------------------------------------------------------
class Model15Form(forms.Form):
    """Model 15: Bilgin et al. (1998)."""
    K = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant")
    alpha = forms.FloatField(required=True, widget=NUMBER, help_text="Distance exponent")
    B = forms.FloatField(required=True, widget=NUMBER, help_text="Site factor B")
    beta = forms.FloatField(required=True, widget=NUMBER, help_text="Exponent on B")


# ------------------------------------------------------------
# Model 16 — Arshadnejad et al. (2013)
# ------------------------------------------------------------
class Model16Form(forms.Form):
    """Model 16: Arshadnejad et al. (2013)."""
    a = forms.FloatField(required=True, widget=NUMBER, help_text="Scale constant")
    RMR = forms.FloatField(required=True, widget=NUMBER, help_text="Rock Mass Rating")
    b = forms.FloatField(required=True, widget=NUMBER, help_text="Exponent on RMR")
    delta = forms.FloatField(required=True, widget=NUMBER, help_text="Exponent δ")
    beta = forms.FloatField(required=True, widget=NUMBER, help_text="Exponent β")
    alpha = forms.FloatField(required=True, widget=NUMBER, help_text="Decay factor")


# ------------------------------------------------------------
# Model 17 — Yilmaz (2016)
# ------------------------------------------------------------
class Model17Form(forms.Form):
    """Model 17: Yilmaz (2016)."""
    K = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant")
    beta = forms.FloatField(required=True, widget=NUMBER, help_text="Attenuation exponent")
    alpha = forms.FloatField(required=True, widget=NUMBER, help_text="Exponential factor")


# ------------------------------------------------------------
# Model 18 — Yilmaz (2016a)
# ------------------------------------------------------------
class Model18Form(forms.Form):
    """Model 18: Yilmaz (2016a)."""
    K = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant")
    beta = forms.FloatField(required=True, widget=NUMBER, help_text="Attenuation exponent")
    alpha = forms.FloatField(required=True, widget=NUMBER, help_text="Exponential factor")


# ------------------------------------------------------------
# Model 19 — Gustaffson
# ------------------------------------------------------------
class Model19Form(forms.Form):
    """Model 19: Gustaffson."""
    K = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant")


# ------------------------------------------------------------
# Model 20 — Afum & Amegbey (2016)
# ------------------------------------------------------------
class Model20Form(forms.Form):
    """Model 20: Afum & Amegbey (2016)."""
    a = forms.FloatField(required=True, widget=NUMBER, help_text="First-term constant")
    d = forms.FloatField(required=True, widget=NUMBER, help_text="Exponent on W")
    c = forms.FloatField(required=True, widget=NUMBER, help_text="Exponent on D")
    K = forms.FloatField(required=True, widget=NUMBER, help_text="Site constant")
    b = forms.FloatField(required=True, widget=NUMBER, help_text="Exponent on K")
    g = forms.FloatField(required=True, widget=NUMBER, help_text="Exponent g")
    e = forms.FloatField(required=True, widget=NUMBER, help_text="Exponential factor")
