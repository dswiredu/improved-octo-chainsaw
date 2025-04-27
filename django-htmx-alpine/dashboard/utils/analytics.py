import pandas as pd

def compute_percentage_changes(df: pd.DataFrame, col=None, index=False) -> None:

    def compute_percentage(df: pd.DataFrame, col: str):
        df[f"{col}_pct_change"] = df[col].pct_change() * 100
        df[f"{col}_pct_change"] = df[f"{col}_pct_change"].round(2)

    if index:
        for col in df.columns:
            if col != "date":
                compute_percentage(df, col)
    elif col:
        compute_percentage(df, col)
