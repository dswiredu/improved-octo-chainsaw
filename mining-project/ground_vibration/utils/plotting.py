import plotly.graph_objects as go
import plotly.io as pio


def build_ppv_plot(df, D, W, weight_series):
    """
    Build a clean Plotly PPV vs Distance graph.
    Now expects dataframe columns to be numeric strings ("150", "100.5", etc.)
    """
    fig = go.Figure()

    x = df["Distance"]

    # global y-min/y-max across all numeric columns
    y_min = df.iloc[:, 1:].min().min()
    y_max = df.iloc[:, 1:].max().max()

    # ------------------------------------------------------
    # Add PPV curves
    # ------------------------------------------------------
    for weight in weight_series:
        col = str(weight)
        y = df[col]

        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                name=f"{weight} kg",
                line=dict(
                    width=4 if weight == W else 2,
                ),
            )
        )

    # ------------------------------------------------------
    # Highlight selected point
    # ------------------------------------------------------
    selected_ppv = df.loc[df["Distance"] == D, str(W)].iloc[0]

    fig.add_trace(
        go.Scatter(
            x=[D], y=[selected_ppv],
            mode="markers",
            marker=dict(size=12, color="red"),
            name="Selected Point",
            showlegend=False,
        )
    )

    # ------------------------------------------------------
    # Vertical dotted line
    # ------------------------------------------------------
    fig.add_trace(
        go.Scatter(
            x=[D, D],
            y=[y_min, y_max],
            mode="lines",
            line=dict(dash="dot", color="black", width=2),
            showlegend=False,
        )
    )

    # ------------------------------------------------------
    # Horizontal dotted lines for each curve
    # ------------------------------------------------------
    for weight in weight_series:
        y_value = df.loc[df["Distance"] == D, str(weight)].iloc[0]

        fig.add_trace(
            go.Scatter(
                x=[x.min(), x.max()],
                y=[y_value, y_value],
                mode="lines",
                line=dict(dash="dot", width=1, color="gray"),
                showlegend=False,
            )
        )

    # ------------------------------------------------------
    # Layout (clean dashboard look)
    # ------------------------------------------------------
    fig.update_layout(
        template="plotly_white",
        autosize=True,
        height=None,
        margin=dict(l=20, r=20, t=20, b=20),

        xaxis=dict(
            title="Distance (m)",
            showgrid=True,
            showline=True,
            linewidth=1,
            linecolor="black",
        ),
        yaxis=dict(
            title="PPV (mm/s)",
            showgrid=True,
            showline=True,
            linewidth=1,
            linecolor="black",
        ),

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),

        uirevision=True,
    )

    return pio.to_html(
        fig, full_html=False, include_plotlyjs="cdn", config={"responsive": True}
    )
