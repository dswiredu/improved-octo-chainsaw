import io
import pandas as pd
from django.http import HttpResponse


def export_df_to_excel(df: pd.DataFrame, filename: str = "export.xlsx") -> HttpResponse:
    """
    Reusable Excel export utility function.
    Takes a DataFrame and returns an Excel file response.
    """

    buffer = io.BytesIO()

    # Write using ExcelWriter
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")

    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response
