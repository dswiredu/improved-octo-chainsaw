"""
Dataframe representation of ChartTable standardized response.

Inspired by
https://github.com/d1g1tinc/python-services/blob/e165e8a9ff84d8a76ad7691da5bc9b54bbe5f560/src/d1g1t/main/util/excel/exporter.py
"""

from dataclasses import dataclass

from dateutil import parser
import numpy
import pandas as pd


@dataclass
class DfColumn:
    """Dataclass for converting chart table categories to DataFrame columns."""

    index: int
    category_id: str
    category_name: str


class ChartTableFormatter:
    """class to handle converting response object to DataFrame."""

    NESTED_CATEGORY_ID = "name"

    def __init__(self, response, request_data=None, fill_blanks=False):
        """
        Create a DataFrame representation of standardized response data.

        :param response: api json response (e.g. from cph-table, trend-aum)
        :param request_data: data from request payload.
        :param fill_blanks: used to fill out missing nodes in parsed response.
        fyi: Doesn't work for contribution tables
        """
        self.response = response
        self.categories = response["categories"]
        self.items = response["items"]
        self.request_data = request_data or {}
        self.columns = self._get_columns()
        self.df_rows = []
        self.fill_blanks = fill_blanks

    @staticmethod
    def format_period_label(start_date, end_date) -> str:
        """Convert dates in a response object to YYYY-MM-DD format."""
        return "from_{}_to_{}".format(
            start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )

    @staticmethod
    def str2date(str_date, default=None):
        """Convert str to a specific date format."""
        if not str_date:
            return default

        return parser.parse(str_date.strip()).date()

    @staticmethod
    def timestamp_to_datetime(ts: int):
        """Convert integer date to datetime."""
        return pd.to_datetime(ts, unit="ms")

    @property
    def display_data(self):
        """Display data from request body."""
        return self.request_data.get("display_data", {})

    @staticmethod
    def is_hidden_category(category):
        """Retrieve hidden categories."""
        return category.get("options", {}).get("hidden", False)

    @property
    def numeric_nodes_index(self) -> list:
        """Return all numeric nodes indexes."""
        # PS-10203
        indexes = []
        for i, category in enumerate(self.categories):
            if category.get("value_type") in ("decimal", "integer"):
                indexes.append(i)
        return indexes

    def is_item_empty(self, item_data) -> bool:
        """
        Check if all numeric item fields are empty.

        - If all of them are empty, return True
        - If at least one has a value, return False
        - If there is no numeric fields, return False
        """
        is_empty = bool(self.numeric_nodes_index)
        for index in self.numeric_nodes_index:
            if item_data[index].get("value"):
                # If at least one has a value, we don't need to keep checking it.
                is_empty = False
                break
        return is_empty

    def is_ignored_item(self, item) -> bool:
        """
        Indicate if an item is ignored.

        This logic for show_current_data_only and hide_empty_nodes should match what UI is currently doing. That is:
        - If "Show Current Holdings Only" and "Hide empty Nodes" are both checked, we should check for is_node_alive
        - If "Show Current Holdings Only" is checked, we should check for is_alive
        - If "Hide empty rows" is checked, validate if all numeric fields are empty
        """
        ignore_inactive_item, ignore_is_node_alive = False, False

        item_data = item.get("data")
        # PS-10203
        ignore_empty_item = self.display_data.get(
            "hide_empty_rows", False
        ) and self.is_item_empty(item_data)

        return (
            ignore_inactive_item or ignore_is_node_alive or ignore_empty_item
        )

    def _get_label_from_metric(self, metric: dict) -> str:
        """Retreives the metric label from self.response."""
        label = metric.get("slug")

        if label.endswith("custom-period"):
            date_range = metric.get("date_range") or {}
            start, end = date_range.get("start_date"), date_range.get(
                "end_date"
            )
            if start and end:
                label += "|" + self.format_period_label(
                    start_date=self.str2date(start),
                    end_date=self.str2date(end),
                )

        return label

    def _get_data_depth(self, items):
        """Return a number of nested `items` levels."""
        if not items:
            return 0

        max_depth = max(
            self._get_data_depth(items=item.get("items")) for item in items
        )
        return 1 + max_depth

    def _dfs_category(self, category, columns):
        """Deep first search a category and its sub-categories."""
        if self.is_hidden_category(category):
            return

        category_id, category_name, _ = (
            category["id"],
            category["name"],
            category["value_type"],
        )
        current_index = len(columns) + 1

        if category_id == self.NESTED_CATEGORY_ID:
            data_depth = self._get_data_depth(self.items)
            category_columns = [
                DfColumn(current_index + index, category_id, category_name)
                for index in range(data_depth)
            ]
        else:
            category_columns = [
                DfColumn(current_index, category_id, category_name)
            ]

        columns.extend(category_columns)

        # extract the nested categories
        for sub_category in category.get("categories", []):
            self._dfs_category(category=sub_category, columns=columns)

    def _get_columns(self):
        """
        Return a list of columns that has to be created in the Excel sheet.

        Respects a hierarchy so that each nested item data will be placed in separate column.
        Re-ordering may be applied based on actual metric order.
        :return: list of DfColumn
        """
        columns = []
        categories = self.categories

        # re-order categories
        metrics = self.request_data.get("metrics", {}).get("selected")
        if metrics:
            metric_categories, non_metric_categories = [], []
            metric_label_order = {
                self._get_label_from_metric(metric=metric): metric.get(
                    "order", 0
                )
                for metric in metrics
            }

            for c in categories:
                if c.get("id") in metric_label_order:
                    metric_categories.append(c)
                else:
                    non_metric_categories.append(c)

            new_metric_categories = sorted(
                metric_categories, key=lambda x: metric_label_order[x["id"]]
            )
            categories = non_metric_categories + new_metric_categories

        for category in categories:
            self._dfs_category(category=category, columns=columns)

        return columns

    def _get_column_for(self, data, item_depth):
        """
        Find a column among existing ones suitable for the `data`.

        :param data: a standardized `data` dict which we need to find a column for
        :param item_depth: how deep the `item` which holding the `data` is in a whole dataset.
        :rtype: DfColumn
        """
        category_id = data["category_id"]
        for column in self.columns:
            if column.category_id != category_id:
                continue

            if category_id != self.NESTED_CATEGORY_ID:
                return column

            if column.index == item_depth:
                return column
        return None

    @staticmethod
    def _include_fields(df, **kwargs) -> None:
        """
        Add additional 'static' fields to a dataframe based on key-value pairs.

        :param df:
        :param kwargs:
        :return:
        """
        if kwargs:
            for k, v in kwargs.items():
                df[k] = v

    def _get_value(self, data, column):
        value = data.get("value")
        if str(column.category_id).lower() == "date" and isinstance(
            value, int
        ):
            # we adjust a value as a corner case for TrendAnalysisChart or any ChartTable with 'date' category
            value = self.timestamp_to_datetime(value)

        if isinstance(value, numpy.float64):
            value = float(value)
        return value

    def parse_data(self, **kwargs):
        """Parse response object. Matches _export_data."""
        hdrs = [column.category_name for column in self.columns]

        for item in self.items:
            self._get_row(item=item)

        res = pd.DataFrame(self.df_rows, columns=hdrs)
        if any(res.columns.duplicated()):
            self._rename_name_cols(res)
        if self.fill_blanks:
            self.fill_parsed_response_nans(res)
        self._include_fields(res, **kwargs)
        return res

    def _get_row(self, item, current_depth=1):  # matches _export_row
        row_values = {}

        for data in item.get("data"):
            column = self._get_column_for(data, current_depth)
            if not column:
                continue

            value = self._get_value(data, column)
            row_values[column.index] = value

        row = [row_values.get(i) for i, _ in enumerate(self.columns, 1)]
        self.df_rows.append(row)

        for nested_item in item.get("items", []):
            self._get_row(item=nested_item, current_depth=current_depth + 1)
        for nested_item in item.get("benchmarks", []):
            self._get_row(item=nested_item, current_depth=current_depth)

    @staticmethod
    def _rename_name_cols(df):
        """Rename all 'Name' columns in dataframe if there are multiple."""
        cols = []
        count = 1
        for column in df.columns:
            if column == "Name":
                cols.append(f"Name{count}")
                count += 1
                continue
            cols.append(column)
        df.columns = cols

    @staticmethod
    def fill_parsed_response_nans(df):
        """Fill out all the blanks in a parsed response. Use for cph and summary tables."""
        fill_headers = [x for x in df.columns if "Name" in x]
        header_count, depth = len(fill_headers), 1
        if fill_headers:
            for col in df.columns:
                if col in fill_headers:
                    ccol = df[col]
                    if depth <= 2:
                        ccol.fillna(method="ffill", inplace=True)
                    elif 3 <= depth <= header_count - 1:
                        pcol = df.iloc[:, depth - 2]
                        prev_diff_idx = pcol != pcol.shift(1)
                        prev_na_idx = pcol == ""
                        ccol.fillna(method="ffill", inplace=True)
                        ccol.loc[(prev_diff_idx | prev_na_idx)] = ""
                else:
                    break
                depth += 1
