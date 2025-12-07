import numpy as np

# ------------------------------------------------------------
# Model 1 — Holmberg & Persson (1978a)
# ------------------------------------------------------------
def compute_model_1_holmberg_persson_a(D, W, k, P0):
    """
    Model 1: Holmberg & Persson (1978a)
    P = 20 * log10( (0.7 * k * W^(1/3)) / (D * P0) )
    """
    numerator = 0.7 * k * (W ** (1/3))
    denominator = D * P0
    return 20 * np.log10(numerator / denominator)


# ------------------------------------------------------------
# Model 2 — Holmberg & Persson (1978b)
# ------------------------------------------------------------
def compute_model_2_holmberg_persson_b(D, W, k, P0, a):
    """
    Model 2: Holmberg & Persson (1978b)
    P = 20 * log10( (k / P0) * (D / W^(1/3))^a )
    """
    ratio = (D / (W ** (1/3))) ** a
    return 20 * np.log10((k / P0) * ratio)


# ------------------------------------------------------------
# Model 3 — Ollofson (1990) & Persson et al. (1994)
# ------------------------------------------------------------
def compute_model_3_ollofson_persson(D, W, P0):
    """
    Model 3: Ollofson (1990) & Persson et al. (1994)
    P = 20 * log10( (0.7 * W^(1/3)) / (D * P0) )
    """
    numerator = 0.7 * (W ** (1/3))
    denominator = D * P0
    return 20 * np.log10(numerator / denominator)


# ------------------------------------------------------------
# Model 4 — Kuzu et al. (2009)
# ------------------------------------------------------------
def compute_model_4_kuzu(D, W, k, beta):
    """
    Model 4: Kuzu et al. (2009)
    Equation: k * (W / W^0.33)^(-β)
    Simplifies to: k * W^(-0.67 * β)
    (Note: D does not appear explicitly but included for consistency.)
    """
    effective = W ** (-0.67 * beta)
    return k * effective


# ------------------------------------------------------------
# Model 5 — National Association of Australian State
# ------------------------------------------------------------
def compute_model_5_national_association(D, W, P0):
    """
    Model 5: National Association of Australian State
    P = 20 * log10( (140 * (W/200)^(1/3)) / (D * P0) )
    """
    numerator = 140 * ((W / 200) ** (1/3))
    denominator = D * P0
    return 20 * np.log10(numerator / denominator)
