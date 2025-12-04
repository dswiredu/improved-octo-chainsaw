import numpy as np

# ------------------------------------------------------------
# Model 1 — Morris (1950)
# ------------------------------------------------------------
def compute_model_1_morris(D, W, K):
    """Model 1: Morris (1950).  A = K * sqrt(W) / D."""
    return K * np.sqrt(W) / D


# ------------------------------------------------------------
# Model 2 — USBM (1959)
# ------------------------------------------------------------
def compute_model_2_usbm(D, W, K, beta):
    """Model 2: USBM (1959).  PPV = K * (D / W^(1/2))^(-β)."""
    return K * (D / (W ** 0.5)) ** (-beta)


# ------------------------------------------------------------
# Model 3 — Langefors–Kihlstrom (1963)
# ------------------------------------------------------------
def compute_model_3_lk(D, W, K, beta):
    """Model 3: Langefors–Kihlstrom (1963).  PPV = K * (sqrt(W / D^(3/2)))^β."""
    return K * ((W / (D ** 1.5)) ** 0.5) ** beta


# ------------------------------------------------------------
# Model 4 — Davies et al. (1963)
# ------------------------------------------------------------
def compute_model_4_davies(D, W, K, alpha, beta):
    """Model 4: Davies et al. (1963).  PPV = K * D^(-α) * W^β."""
    return K * (D ** -alpha) * (W ** beta)


# ------------------------------------------------------------
# Model 5 — Ambraseys–Hendron (1968)
# ------------------------------------------------------------
def compute_model_5_ah(D, W, K, beta):
    """Model 5: Ambraseys–Hendron (1968).  PPV = K * (D / W^(1/3))^(-β)."""
    return K * (D / (W ** (1/3))) ** (-beta)


# ------------------------------------------------------------
# Model 6 — Bureau of Indian Standard (1973)
# ------------------------------------------------------------
def compute_model_6_bis(D, W, K, beta):
    """Model 6: BIS (1973).  PPV = K * (W^(2/3) / D)^β."""
    return K * ((W ** (2/3)) / D) ** beta


# ------------------------------------------------------------
# Model 7 — Lundberg (1977)
# ------------------------------------------------------------
def compute_model_7_lundberg(D, W):
    """Model 7: Lundberg (1977).  log(V) = 2.86 + 0.66 log(W) – 1.54 log(D)."""
    return 10 ** (2.86 + 0.66 * np.log10(W) - 1.54 * np.log10(D))


# ------------------------------------------------------------
# Model 8 — Just & Free (1980)
# ------------------------------------------------------------
def compute_model_8_just_free(D, W, K, beta, alpha):
    """Model 8: Just & Free (1980).  
    PPV = K * (D / W^(1/3))^β * exp( α D / W^(1/3) )."""
    return K * (D / (W ** (1/3))) ** beta * np.exp(alpha * D / (W ** (1/3)))


# ------------------------------------------------------------
# Model 9 — Ghosh–Daemen (1983)
# ------------------------------------------------------------
def compute_model_9_gd(D, W, K, beta, alpha):
    """Model 9: Ghosh–Daemen (1983).  
    PPV = K * (D / W^(1/2))^(-β) * exp(-αD)."""
    return K * (D / (W ** 0.5)) ** (-beta) * np.exp(-alpha * D)


# ------------------------------------------------------------
# Model 10 — Ghosh–Daemen (1983) alt
# ------------------------------------------------------------
def compute_model_10_gd_alt(D, W, K, beta, alpha):
    """Model 10: Ghosh–Daemen alt.  
    PPV = K * (D / W^(1/3))^(-β) * exp(-αD)."""
    return K * (D / (W ** (1/3))) ** (-beta) * np.exp(-alpha * D)


# ------------------------------------------------------------
# Model 11 — Ghosh (1983)
# ------------------------------------------------------------
def compute_model_11_ghosh(D, W, K, a, n, alpha):
    """Model 11: Ghosh (1983).  
    PPV = K * W^a * D^n * exp(-αD)."""
    return K * (W ** a) * (D ** n) * np.exp(-alpha * D)


# ------------------------------------------------------------
# Model 12 — Gupta et al. (1987)
# ------------------------------------------------------------
def compute_model_12_gupta87(D, W, K, beta, alpha):
    """Model 12: Gupta et al. (1987).  
    PPV = K * ((W / D^1.5)^0.5)^β * exp(-αK)."""
    return K * ((W / (D ** 1.5)) ** 0.5) ** beta * np.exp(-alpha * K)


# ------------------------------------------------------------
# Model 13 — Gupta et al. (1988)
# ------------------------------------------------------------
def compute_model_13_gupta88(D, W, K, beta, alpha):
    """Model 13: Gupta et al. (1988).  
    PPV = K * (D / W^(1/2))^(-β) * exp( α D / W )."""
    return K * (D / (W ** 0.5)) ** (-beta) * np.exp(alpha * (D / W))


# ------------------------------------------------------------
# Model 14 — CMRI / CMSR (1991/1993)
# ------------------------------------------------------------
def compute_model_14_cmri(D, W, n, K):
    """Model 14: CMRI/CMSR.  
    PPV = n + K * (D / sqrt(W))^(-1)."""
    return n + K * (D / (W ** 0.5)) ** (-1)


# ------------------------------------------------------------
# Model 15 — Bilgin et al. (1998)
# ------------------------------------------------------------
def compute_model_15_bilgin(D, W, K, alpha, B, beta):
    """Model 15: Bilgin et al. (1998).  
    PPV = K * (D / W^(0.5))^α * B^β."""
    return K * (D / (W ** 0.5)) ** alpha * (B ** beta)


# ------------------------------------------------------------
# Model 16 — Arshadnejad et al. (2013)
# ------------------------------------------------------------
def compute_model_16_arshad(D, W, a, RMR, b, delta, beta, alpha):
    """Model 16: Arshadnejad et al. (2013).  
    PPV = a RMR^b * (D^δ / W^β)^(-2) * exp(-αD)."""
    return a * (RMR ** b) * ((D ** delta) / (W ** beta)) ** (-2) * np.exp(-alpha * D)


# ------------------------------------------------------------
# Model 17 — Yilmaz (2016)
# ------------------------------------------------------------
def compute_model_17_yilmaz(D, W, K, beta, alpha):
    """Model 17: Yilmaz (2016).  
    PPV = K * (D^(1/4) / W^(1/6))^(-β) * exp( α D / W^(1/3) )."""
    return K * (D ** 0.25 / W ** (1/6)) ** (-beta) * np.exp(alpha * (D / W ** (1/3)))


# ------------------------------------------------------------
# Model 18 — Yilmaz (2016a)
# ------------------------------------------------------------
def compute_model_18_yilmaz_alt(D, W, K, beta, alpha):
    """Model 18: Yilmaz (2016a).  
    PPV = K * (D^(1/4) / W^(1/6))^(-β) * exp( α D^(1/4) / W^(1/6) )."""
    return K * (D ** 0.25 / W ** (1/6)) ** (-beta) * np.exp(alpha * (D ** 0.25 / W ** (1/6)))


# ------------------------------------------------------------
# Model 19 — Gustaffson
# ------------------------------------------------------------
def compute_model_19_gustaffson(D, W, K):
    """Model 19: Gustaffson.  
    PPV = K * sqrt(W / D^1.5)."""
    return K * np.sqrt(W / (D ** 1.5))


# ------------------------------------------------------------
# Model 20 — Afum & Amegbey (2016)
# ------------------------------------------------------------
def compute_model_20_afum(D, W, a, d, c, K, b, g, e):
    """Model 20: Afum & Amegbey (2016).  
    PPV = a (W^d/D^c) + K^b (W^d/D^c)^g * exp(-eD/W)."""
    ratio = (W ** d) / (D ** c)
    return a * ratio + (K ** b) * (ratio ** g) * np.exp(-e * (D / W))