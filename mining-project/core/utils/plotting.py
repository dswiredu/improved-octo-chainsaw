from bokeh.plotting import figure

# Global color palette accessible to all plotting functions
COLOR_PALETTE = [
    "#1f77b4",  # blue
    "#ff7f0e",  # orange
    "#2ca02c",  # green
    "#d62728",  # red
    "#9467bd",  # purple
    "#8c564b",  # brown
    "#e377c2",  # pink
    "#7f7f7f",  # gray
    "#bcbd22",  # olive
    "#17becf",  # teal
]


def base_figure(
    x_axis_label=None,
    y_axis_label=None,
    title=None,
    tools="pan,wheel_zoom,box_zoom,reset,save",
):
    """
    Generic base Bokeh figure used across the entire project.
    Does NOT assume domain data (no tooltips, no PPV logic, etc).
    Provides clean styling and responsive sizing suitable for cards.
    """

    fig = figure(
        sizing_mode="stretch_both",   # responsive width + responsive height
        tools=tools,
        title=title,
        x_axis_label=x_axis_label,
        y_axis_label=y_axis_label,
    )

    # Clean, modern styling
    fig.toolbar.autohide = True
    fig.outline_line_color = None

    # Axis formatting
    fig.xaxis.axis_line_color = "black"
    fig.yaxis.axis_line_color = "black"

    fig.xaxis.major_label_text_font_size = "11pt"
    fig.yaxis.major_label_text_font_size = "11pt"

    fig.grid.grid_line_color = "#e5e7eb"
    fig.grid.grid_line_alpha = 0.6

    return fig
