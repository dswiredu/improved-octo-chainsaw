from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource, HoverTool, NumeralTickFormatter
import pandas as pd

def plot_mortgage_floating_cashflows(qs):
    df = pd.DataFrame(list(qs.values(
        'timestep', 'balance', 'interest', 'default', 'prepayment', 'principal', 'totalcf'
    )))

    source = ColumnDataSource(df)

    fields = ['balance', 'interest', 'default', 'prepayment', 'principal', 'totalcf']
    colors = ['#1f77b4', '#2ca02c', '#d62728', '#ff7f0e', '#9467bd', '#7f7f7f']

    p = figure(
        x_axis_label="Timestep",
        height=500,
        sizing_mode="stretch_width",
        background_fill_color="white",
        toolbar_location="right",
        tools="box_zoom,reset,save"
    )

    for field, color in zip(fields, colors):
        p.line(
            x='timestep',
            y=field,
            source=source,
            line_width=2,
            color=color,
            legend_label=field.capitalize(),
            muted_alpha=0.1  # Optional: fade instead of full hide
        )

    # Shared hover
    hover = HoverTool(
        tooltips=[
            ("Timestep", "@timestep"),
            ("Balance", "@balance{0,0.00}"),
            ("Interest", "@interest{0,0.00}"),
            ("Default", "@default{0,0.00}"),
            ("Prepayment", "@prepayment{0,0.00}"),
            ("Principal", "@principal{0,0.00}"),
            ("Total CF", "@totalcf{0,0.00}"),
        ],
        mode="vline"
    )
    p.add_tools(hover)

    # Axis + grid styling
    p.yaxis.formatter = NumeralTickFormatter(format="$0,0")
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
    p.toolbar.logo = None

    # Interactive legend inside chart
    p.legend.click_policy = "hide"
    p.legend.location = "top_right"
    p.legend.label_text_font_size = "11pt"
    p.legend.background_fill_alpha = 0.0

    return components(p)
