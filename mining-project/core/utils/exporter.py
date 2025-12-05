import io
import pandas as pd
from django.http import HttpResponse
from typing import Union, List


def export_df_to_excel(
    dataframes: Union[pd.DataFrame, List[pd.DataFrame]], filename: str = "export.xlsx"
) -> HttpResponse:
    """
    Reusable Excel export utility function.
    Takes DataFrames and returns an Excel file response.
    """

    buffer = io.BytesIO()
    if isinstance(dataframes, pd.DataFrame):
        df_list = [dataframes]
    elif isinstance(dataframes, list):
        df_list = dataframes
    else:
        raise ValueError(
            "export_df_to_excel accepts either a dataframe or list of dataframes!"
        )

    if not all(isinstance(df, pd.DataFrame) for df in df_list):
        raise ValueError("All items in the list must be DataFrames")

    # Write using ExcelWriter
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for idx, df in enumerate(df_list, start=1):
            sheet_name = f"Sheet{idx}"
            df.to_excel(writer, index=False, sheet_name=sheet_name)

    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response
