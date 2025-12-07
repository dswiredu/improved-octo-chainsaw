from core.utils.echarts.base import BaseEChart


def build_blast_chart_options(df, D, W, weight_series):
    """
    Build PPV chart options for ECharts.
    Returns a Python dict.
    """

    chart = BaseEChart(
        title=None,
        x_type="value",              # numeric X-axis
        x_label="Distance (m)",
        y_label="Air Blast (mm/s)",
    )

    x = df["Distance"].tolist()

    # -----------------------------------------
    # Add weight-series curves (colored lines)
    # -----------------------------------------
    for weight in weight_series:
        y = df[str(weight)].tolist()
        xy_pairs = list(zip(x, y))

        chart.add_line_series(
            name=f"{weight:.1f} kg",
            xy_pairs=xy_pairs,
            smooth=True,
            width=4 if weight == W else 2,
        )

    # -----------------------------------------
    # Add the RED selected point
    # -----------------------------------------
    selected_ppv = df.loc[df["Distance"] == D, str(W)].iloc[0]
    chart.add_scatter_series(
        name="Selected Point",
        xy_pairs=[(D, selected_ppv)],
        size=12,
        color="red",
    )

    # -----------------------------------------
    # Add vertical reference line at D
    # -----------------------------------------
    # chart.add_reference_line(
    #     x_value=D,
    #     color="#000",
    #     width=2,
    #     style="dotted",
    # )

    # -----------------------------------------
    # Add horizontal reference lines for PPV(D) for all curves
    # -----------------------------------------
    for weight in weight_series:
        y_value = df.loc[df["Distance"] == D, str(weight)].iloc[0]
        chart.add_reference_line(
            y_value=y_value,
            color="#aaa",
            width=1,
            style="dotted",
        )

    return chart.build()
