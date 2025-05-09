import pandas as pd
from decimal import Decimal

def convert_decimals_to_floats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts all Decimal-valued columns in a DataFrame to float.
    Leaves other column types untouched.
    """
    for col in df.columns:
        if pd.api.types.is_object_dtype(df[col]):
            if df[col].apply(lambda x: isinstance(x, Decimal)).any():
                df[col] = df[col].astype(float)
    return df
