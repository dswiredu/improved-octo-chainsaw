import pandas as pd

def compute_percentage_changes(df: pd.DataFrame) -> None:
    for col in df.columns:
        if col != "date":
            df[f"{col}_pct_change"] = df[col].pct_change() * 100
            df[f"{col}_pct_change"] = df[f"{col}_pct_change"].round(2)