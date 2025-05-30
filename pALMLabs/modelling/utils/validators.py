def validate_scurve_upload(sa_file: str, curve_file: str, psa: str, sda: str):
    errors = []

    # File type checks
    if not (sa_file and sa_file.name.endswith(".csv")):
        errors.append("Security Assumptions must be a .csv file.")
    if not (curve_file and curve_file.name.endswith(".csv")):
        errors.append("Curve input file must be a .csv file.")

    # Numeric validation
    try:
        psa_val = float(psa)
        sda_val = float(sda)
        if psa_val < 0 or sda_val < 0:
            errors.append("PSA and SDA values must be non-negative.")
    except ValueError:
        errors.append("PSA and SDA must be numbers.")

    return errors
