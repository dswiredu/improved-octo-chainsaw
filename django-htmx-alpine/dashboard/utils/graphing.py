from typing import Dict

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource
from bokeh.models import ColumnDataSource, HoverTool

import pandas as pd
from ..constants import SPARKLINE_DAYS


def generate_summary_sparklines(df: pd.DataFrame) -> Dict[str, str]:
    """
    Creates Bokeh sparklines using one ColumnDataSource.
    Assumes 'date' is a column, not the index.
    """
    res = dict()
    spark_df = df.tail(SPARKLINE_DAYS)

    for col in spark_df.columns:
        if col != "date":
            source = ColumnDataSource(data={
                'date': spark_df["date"],
                'value': spark_df[col],
            })

            p = figure(
                width=140,
                height=50,
                toolbar_location=None,
                tools="",
                min_border=0,
                x_axis_type="datetime"
            )

            p.line('date', 'value', source=source, line_width=2, line_color="#0ea5e9")

            p.axis.visible = False
            p.grid.visible = False
            p.outline_line_color = None
            p.background_fill_color = None
            p.border_fill_color = None

            script, div = components(p)
            print(col == col.lower())
            res[f"{col.lower()}_sparkline_script"] = script
            res[f"{col.lower()}_sparkline_div"] = div

    return res


def generate_chart(df: pd.DataFrame, column="close_price") -> tuple:
    source = ColumnDataSource(df)

    p = figure(
        x_axis_type="datetime",
        height=450,
        sizing_mode="stretch_width",
        background_fill_color="white",
        toolbar_location="right",
        tools="box_zoom,reset,save",  # no hover here; we'll add it manually
    )

    # Main line
    p.line("date", column, source=source, line_width=2, color="#0ea5e9")

    # Crash markers
    crash_df = df[df["crash"]].copy()
    if not crash_df.empty:
        crash_source = ColumnDataSource(crash_df)
        crash_renderer = p.circle(
            "date", column,
            source=crash_source,
            size=4,
            color="red",
            legend_label="Crash"
        )

        # Styled crash hover tooltip (red text)
        crash_hover = HoverTool(
            tooltips="""
                <div style="color: #ef4444;">
                    <strong>Date:</strong> @date{%F}<br>
                    <strong>Crash Value:</strong> @""" + column + """{0.2f}
                </div>
            """,
            formatters={"@date": "datetime"},
            mode="vline",
            renderers=[crash_renderer]
        )
        p.add_tools(crash_hover)

    # Hover for main line
    main_hover = HoverTool(
        tooltips=[
            ("Date", "@date{%F}"),
            ("Value", f"@{column}{{0.2f}}")
        ],
        formatters={"@date": "datetime"},
        mode="vline"
    )
    p.add_tools(main_hover)

    # Axis & styling
    p.yaxis.visible = True
    p.xaxis.axis_label = None
    p.yaxis.axis_label = None
    p.xaxis.major_label_text_color = "#4A5568"
    p.yaxis.major_label_text_color = "#4A5568"
    p.xaxis.axis_line_color = "#E2E8F0"
    p.yaxis.axis_line_color = "#E2E8F0"
    p.ygrid.grid_line_color = "#EDF2F7"
    p.xgrid.visible = False
    p.outline_line_color = None

    # Toolbar
    p.toolbar.logo = None

    # Legend
    p.legend.label_text_font_size = "11pt"
    p.legend.location = "top_left"
    p.legend.background_fill_alpha = 0.0

    return components(p)