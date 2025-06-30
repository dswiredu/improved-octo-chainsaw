import pandas as pd

def min_max_normalize(df: pd.DataFrame, exclude: list[str] = None) -> pd.DataFrame:
    """
    Normalize a DataFrame using min-max scaling to [0, 1].
    
    Parameters:
    - df: The DataFrame to normalize.
    - exclude: Columns to exclude from normalization (e.g., ['timestep', 'id', 'date'])

    Returns:
    - Normalized DataFrame with same shape/index
    """
    exclude = exclude or []
    df_norm = df.copy()
    
    for col in df.columns:
        if col in exclude:
            continue
        min_val = df[col].min()
        max_val = df[col].max()
        if max_val != min_val:
            df_norm[col] = (df[col] - min_val) / (max_val - min_val)
        else:
            df_norm[col] = 0.0  # Or np.nan if you want to show missing values
    return df_norm