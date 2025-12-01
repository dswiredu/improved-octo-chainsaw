"""
vibration_models.py

Computation functions for Ground Vibration PPV prediction models.
Each model corresponds to the numbered equations in the reference table.

Only models with fully or partially legible formulas have been implemented here.
Each function includes a docstring with the model number for easy traceability.

Models requiring clarification are marked with TODO.
"""

import math


# ============================================================
# Model 10 — Ghosh-Daemen (1983)
# ============================================================

def compute_model_10_ghosh_daemen_1983(D, W, K, beta, alpha):
    """
    Model 10: Ghosh-Daemen (1983)
    Equation: PPV = K * (D / W^(1/2))^(-β) * exp(-αD)
    """
    return K * ((D / (W ** 0.5)) ** (-beta)) * math.exp(-alpha * D)



# ============================================================
# Model 11 — Ghosh (1983)
# ============================================================

def compute_model_11_ghosh_1983(D, W, K, a, n, alpha):
    """
    Model 11: Ghosh (1983)
    Equation: PPV = K * W^a * D^n * exp(-αD)
    """
    return K * (W ** a) * (D ** n) * math.exp(-alpha * D)



# ============================================================
# Model 12 — Gupta et al. (1987)
# ============================================================
# NOTE: The exponent term "e^{-αK}" is unclear due to low image resolution.
#       Using literal interpretation until corrected.

def compute_model_12_gupta_1987(D, W, K, beta, alpha):
    """
    Model 12: Gupta et al. (1987)
    Approx. Equation: PPV = K * ((W / D^1.5)^0.5)^β * exp(-αK)
    TODO: Confirm exponent term exp(-αK). Might be exp(-αD) or exp(-α(D/W)).
    """
    return K * (((W / (D ** 1.5)) ** 0.5) ** beta) * math.exp(-alpha * K)



# ============================================================
# Model 13 — Gupta et al. (1988)
# ============================================================

def compute_model_13_gupta_1988(D, W, K, beta, alpha):
    """
    Model 13: Gupta et al. (1988)
    Equation: PPV = K * (D / W^(1/2))^(-β) * exp(α(D/W))
    """
    return K * ((D / (W ** 0.5)) ** (-beta)) * math.exp(alpha * (D / W))



# ============================================================
# Model 14 — CMRI / CMSR (1991, 1993)
# ============================================================

def compute_model_14_cmri_1991(D, W, n, K):
    """
    Model 14: CMRI/CMSR (1991/1993)
    Equation: PPV = n + K * (D / sqrt(W))^(-1)
    """
    return n + K * ((D / (W ** 0.5)) ** -1)



# ============================================================
# Model 15 — Bilgin et al. (1998)
# ============================================================
# NOTE: Formula not fully clear (d and B terms ambiguous).
#       Placeholder implementation based on partial reading.

def compute_model_15_bilgin_1998(D, W, K, d, B, beta):
    """
    Model 15: Bilgin et al. (1998)
    Approx. Equation: PPV = K * (D / W^0.5)^d * B^β
    TODO: Confirm the actual formula and exponent placement.
    """
    return K * ((D / (W ** 0.5)) ** d) * (B ** beta)



# ============================================================
# Model 16 — Arshadnejad et al. (2013)
# ============================================================

def compute_model_16_arshadnejad_2013(D, W, a, RMR, b, B, alpha):
    """
    Model 16: Arshadnejad et al. (2013)
    Approx. Equation: PPV = a * RMR^b * (D^6 / (W * B))^(-2) * exp(-αD)
    TODO: Confirm exponent structure and B term.
    """
    return a * (RMR ** b) * ((D ** 6) / (W * B)) ** (-2) * math.exp(-alpha * D)



# ============================================================
# Model 17 — Yilmaz (2016), Variant A
# ============================================================
# NOTE: D exponent unclear in table (looks like D^(2/3W) or D^3/W).
#       Placeholder implementation.

def compute_model_17_yilmaz_2016_A(D, W, K, beta, alpha):
    """
    Model 17: Yilmaz (2016) — Variant A
    Approx. Equation: PPV = K * (D^(1/4) / W^(1/6))^(-β) * exp(α(D^3/W))
    TODO: Confirm exponent of D inside exp().
    """
    return K * ((D ** 0.25 / W ** (1/6)) ** (-beta)) * math.exp(alpha * ((D ** 3) / W))



# ============================================================
# Model 18 — Yilmaz (2016), Variant B
# ============================================================
# NOTE: Appears similar to model 17 but with D^(1/4)/W^(1/6) inside exp().

def compute_model_18_yilmaz_2016_B(D, W, K, beta, alpha):
    """
    Model 18: Yilmaz (2016) — Variant B
    Approx. Equation: PPV = K * (D^(1/4) / W^(1/6))^(-β) * exp(α(D^(1/4)/W^(1/6)))
    TODO: Confirm exact exponent relationship.
    """
    return K * ((D ** 0.25 / W ** (1/6)) ** (-beta)) * math.exp(alpha * (D ** 0.25 / (W ** (1/6))))



# ============================================================
# Model 19 — Afum & Amegbery (2016)
# ============================================================

def compute_model_19_afum_amegbery_2016(D, W, a, d, c, K, b, e):
    """
    Model 19: Afum & Amegbery (2016)
    Equation: 
        PPV = a*(W^d / D^c) 
            + K^b * (D^c / W^d)^(-b) * exp(-e * D/W)
    """
    term1 = a * ((W ** d) / (D ** c))
    term2 = (K ** b) * (((D ** c) / (W ** d)) ** (-b)) * math.exp(-e * (D / W))
    return term1 + term2
