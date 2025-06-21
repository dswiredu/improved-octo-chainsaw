import pandas as pd

def check_total_cf_positive(df : pd.DataFrame):
    """
    Custom check to ensure totalCF_ column has only positive values.
    """
    failed_indices = df.index[df["totalCF_"] <= 0].tolist()
    return {
        "check_name": "check_total_cf_positive",
        "success": len(failed_indices) == 0,
        "failed_indices": failed_indices,
        "message": f"{len(failed_indices)} rows found with non-positive totalCF_ values."
    }

def check_interest_not_exceed_balance(df: pd.DataFrame):
    """
    Custom check to ensure interest_ does not exceed outstandingBalance_ in any row.
    """
    failed_indices = df.index[df["interest_"] > df["outstandingBalance_"]].tolist()
    return {
        "check_name": "check_interest_not_exceed_balance",
        "success": len(failed_indices) == 0,
        "failed_indices": failed_indices,
        "message": f"{len(failed_indices)} rows where interest_ exceeds outstandingBalance_."
    }
