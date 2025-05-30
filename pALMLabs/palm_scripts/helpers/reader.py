import pandas as pd


def read_security_file(file: str):
    df = pd.read_csv(file, dtype=str)

    # Expecting exactly one row
    if df.shape[0] != 1:
        raise ValueError("Security file must contain exactly one row")

    # Convert that one row to a dictionary
    record = df.iloc[0].to_dict()
    return record


def read_curve_data(file: str) -> pd.DataFrame:
    df = pd.read_csv(file, dtype={"Period": int})
    return df
