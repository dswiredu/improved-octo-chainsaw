# core/utils/echarts/base.py

class BaseEChart:
    COLOR_PALETTE = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    ]

    def __init__(
        self,
        title=None,
        x_type="value",
        x_label=None,
        y_label=None,
        grid=None,
    ):
        """
        Base ECharts option builder.
        """

        self.title = title
        self.x_type = x_type
        self.x_label = x_label
        self.y_label = y_label

        # -----------------------------
        # X-AXIS (value axis defaults)
        # -----------------------------
        x_axis = {
            "type": x_type,
            "name": x_label,
            "nameLocation": "middle",   # centered under axis line
            "nameGap": 20,              # space between label and axis
            "min": "dataMin",
            "max": "dataMax",
            "boundaryGap": [0, 0],      # no padding left/right
        }

        # -----------------------------
        # Y-AXIS (vertical label)
        # -----------------------------
        y_axis = {
            "type": "value",
            "name": y_label,
            "nameLocation": "middle",   # centered vertically
            "nameGap": 30,
            "nameRotate": 90,           # rotate vertical label
            # "min": "dataMin",
            # "max": "dataMax",
            "boundaryGap": [0, 0],      # no padding top/bottom
        }

        # -----------------------------
        # TITLE
        # -----------------------------
        if title is not None:
            title_block = {
                "text": title,
                "left": "center",
                "top": 10,
                "textStyle": {
                    "fontSize": 16,
                    "fontWeight": "bold",
                },
            }
        else:
            title_block = {}

        # -----------------------------
        # LEGEND (scroll + tight top)
        # -----------------------------
        legend_block = {
            "top": 10,
            "type": "scroll",
        }

        # -----------------------------
        # GRID (tight engineering layout)
        # -----------------------------
        default_grid = {
            "left": 20,                     # room for vertical y-axis label
            "right": 20,
            "top": 40 if title else 10,     # extra room only when title exists
            "bottom": 10,                   # room for x-axis label
            "containLabel": True,
        }

        # -----------------------------
        # FINAL OPTION STRUCTURE
        # -----------------------------
        self.option = {
            "title": title_block,
            "color": self.COLOR_PALETTE,
            "tooltip": {"trigger": "axis"},
            "toolbox": {
                "feature": {
                    "saveAsImage": {},
                    "dataZoom": {},
                    "restore": {},
                }
            },
            "xAxis": x_axis,
            "yAxis": y_axis,
            "legend": legend_block,
            "grid": grid or default_grid,
            "series": [],
            "dataZoom": [
                {"type": "inside"},   # no slider by default
            ],
            "axisPointer": {
                "type": "cross",
                "crossStyle": {"color": "#999"},
            },
            "animation": True,
        }

    # ---------------------------------------------------------
    # Generic ADD SERIES
    # ---------------------------------------------------------
    def add_series(self, name, series_type, data, extra_opts=None):
        """
        Low-level series adder. data is typically a list of [x, y] pairs.
        """
        series = {
            "name": name,
            "type": series_type,
            "data": data,
            "smooth": True if series_type == "line" else False,
            "symbol": "circle",
        }
        if extra_opts:
            series.update(extra_opts)
        self.option["series"].append(series)

    # ---------------------------------------------------------
    # LINE SERIES
    # ---------------------------------------------------------
    def add_line_series(self, name, xy_pairs, smooth=True, width=2):
        """
        xy_pairs = [(x1, y1), (x2, y2), ...]
        """
        self.add_series(
            name=name,
            series_type="line",
            data=xy_pairs,
            extra_opts={
                "smooth": smooth,
                "lineStyle": {"width": width},
            },
        )

    # ---------------------------------------------------------
    # AREA SERIES
    # ---------------------------------------------------------
    def add_area_series(self, name, xy_pairs, opacity=0.25):
        self.add_series(
            name=name,
            series_type="line",
            data=xy_pairs,
            extra_opts={
                "areaStyle": {"opacity": opacity},
                "smooth": True,
                "lineStyle": {"width": 1},
            },
        )

    # ---------------------------------------------------------
    # BAR SERIES
    # ---------------------------------------------------------
    def add_bar_series(self, name, xy_pairs):
        self.add_series(
            name=name,
            series_type="bar",
            data=xy_pairs,
        )

    # ---------------------------------------------------------
    # STACKED BAR SERIES
    # ---------------------------------------------------------
    def add_stacked_bar_series(self, name, xy_pairs, stack="stack1"):
        self.add_series(
            name=name,
            series_type="bar",
            data=xy_pairs,
            extra_opts={"stack": stack},
        )

    # ---------------------------------------------------------
    # PIE SERIES
    # ---------------------------------------------------------
    def add_pie_series(self, name, pie_data, radius="50%"):
        """
        pie_data = [
            {"name": "A", "value": 10},
            {"name": "B", "value": 20},
        ]
        """
        self.option["series"].append({
            "name": name,
            "type": "pie",
            "radius": radius,
            "data": pie_data,
        })

    # ---------------------------------------------------------
    # SCATTER SERIES (for highlighted points)
    # ---------------------------------------------------------
    def add_scatter_series(self, name, xy_pairs, size=12, color=None, emphasis=True):
        extra_opts = {
            "symbolSize": size,
        }
        if color:
            extra_opts["itemStyle"] = {"color": color}
        if emphasis:
            extra_opts["emphasis"] = {"scale": True}
        else:
            extra_opts["emphasis"] = {"disabled": True}

        self.add_series(
            name=name,
            series_type="scatter",
            data=xy_pairs,
            extra_opts=extra_opts,
        )

    # Backwards-compatible alias name if you ever used it
    def add_scatter_points(self, name, xy_pairs, size=12, color=None):
        return self.add_scatter_series(name, xy_pairs, size=size, color=color)

    # ---------------------------------------------------------
    # REFERENCE LINES (vertical / horizontal)
    # ---------------------------------------------------------
    def add_reference_line(self, x_value=None, y_value=None,
                        color="#000", width=1, style="dashed"):
        """
        Adds a vertical (x_value) or horizontal (y_value) reference line
        using ECharts markLine on the last series.

        If no series exist yet, a dummy invisible line series is created.
        """

        if x_value is None and y_value is None:
            return

        if not self.option["series"]:
            # Create a dummy series so markLine has somewhere to live
            self.option["series"].append({
                "name": "_refline",
                "type": "line",
                "data": [],
                "showSymbol": False,
                "lineStyle": {"opacity": 0},
                "tooltip": {"show": False},
            })

        target = self.option["series"][-1]

        markline = target.setdefault(
            "markLine",
            {
                "symbol": "none",
                "data": [],
            },
        )

        entry = {
            "lineStyle": {
                "color": color,
                "width": width,
                "type": style,  # "solid" | "dashed" | "dotted"
            }
        }
        if x_value is not None:
            entry["xAxis"] = x_value
        if y_value is not None:
            entry["yAxis"] = y_value

        markline["data"].append(entry)

    # ---------------------------------------------------------
    # METHOD TO RETURN FINAL OPTION
    # ---------------------------------------------------------
    def build(self):
        return self.option
