import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)

import pandas as pd
import numpy as np
from openpyxl.cell.cell import MergedCell

PAYLOAD_PAGINATION_SIZE = 5000
DEFAULT_DATE_FORMAT = "%Y-%m-%d"


def _get_summation_frame(frame: pd.DataFrame, total_prefix) -> pd.DataFrame:
    df = frame.copy()
    for col in df.select_dtypes(
        "object"
    ).columns:  # TODO: Change this to use the grouping_fields
        data = df[col].astype(str)
        total_idx = data.str.startswith(total_prefix)
        df = df[~total_idx]
    return df


def _get_total_row(
    df: pd.DataFrame,
    columns: str,
    labels: str,
    sum_columns: list,
    total_prefix=None,
) -> pd.DataFrame:
    row_dict = {col: [label] for col, label in zip(columns, labels)}

    if total_prefix:
        last_column, last_label = columns[-1], labels[-1]
        row_dict.pop(last_column)
        row_dict[last_column] = [f"{total_prefix} {last_label}"]

    row = pd.DataFrame(row_dict)
    row[sum_columns] = df[sum_columns].fillna(0).sum()
    if len(columns) == 1:
        row.loc[max(row.index) + 1, :] = pd.NA
    return row


def _get_grand_total(df: pd.DataFrame, sum_columns: list, total_prefix) -> pd.DataFrame:
    sum_frame = _get_summation_frame(df, total_prefix)
    columns = [df.columns[0]]
    labels = ["Grand Total"]
    total = _get_total_row(
        sum_frame, columns=columns, labels=labels, sum_columns=sum_columns
    )
    return total


def _shift_non_grouping_fields(df: pd.DataFrame, grouping_fields: list):
    shift_cols = [x for x in df.columns if x not in grouping_fields]
    df.loc[max(df.index) + 1, :] = pd.NA
    df[shift_cols] = df[shift_cols].shift(1)
    df[grouping_fields] = df[grouping_fields].fillna(method="ffill")


def _get_summation_group(df: pd.DataFrame, grouping_fields: list) -> pd.DataFrame:
    dx = df.reset_index().drop(columns=["index"])
    field_length = len(grouping_fields)
    if field_length > 1:
        _shift_non_grouping_fields(dx, grouping_fields)
        dx.loc[max(dx.index) + 1, :] = pd.NA  # insert empty row at last
        shift_cols = [x for x in dx.columns if x not in grouping_fields[:-1]]
        dx[shift_cols] = dx[shift_cols].shift(1)
        dx[grouping_fields[:-1]] = dx[grouping_fields[:-1]].fillna(method="ffill")
    return dx


def generate_group_totals(
    frame: pd.DataFrame,
    grouping_fields: list,
    sum_columns: list,
    total_prefix="Total -",
    grand_total_sum_columns: list = None,
    grand_total_prefix: str = None,
) -> pd.DataFrame:
    res = get_individual_group_totals(
        frame=frame,
        grouping_fields=grouping_fields,
        sum_columns=sum_columns,
        total_prefix=total_prefix,
        grand_total_sum_columns=grand_total_sum_columns,
        grand_total_prefix=grand_total_prefix,
    )

    for col in grouping_fields:
        res[col] = res[col].fillna("")
        res.loc[res[col] == res[col].shift(1), col] = ""
    return res.fillna("")


def get_individual_group_totals(
    frame: pd.DataFrame,
    grouping_fields: list,
    sum_columns: list,
    total_prefix="Total -",
    grand_total_sum_columns: list = None,
    grand_total_prefix: str = None,
) -> pd.DataFrame:
    """Function to get summation of datatable based on grouping_fields
    with totals at the bottom of each node."""
    if grouping_fields:
        container = []
        groups = frame.groupby(grouping_fields, sort=False)
        for labels, _df in groups:
            _df = _get_summation_group(_df, grouping_fields)
            sum_frame = _get_summation_frame(_df, total_prefix)
            total = _get_total_row(
                sum_frame,
                grouping_fields,
                labels,
                sum_columns,
                total_prefix=total_prefix,
            )
            label_result = pd.concat([_df, total])
            container.append(label_result)
        result = pd.concat(container, ignore_index=True)
        return get_individual_group_totals(
            result,
            grouping_fields[:-1],
            sum_columns,
            grand_total_prefix=grand_total_prefix,
            grand_total_sum_columns=grand_total_sum_columns,
        )
    else:
        _sum_cols = (
            sum_columns if not grand_total_sum_columns else grand_total_sum_columns
        )
        _prefix = total_prefix if not grand_total_prefix else grand_total_prefix
        grand_total = _get_grand_total(frame, _sum_cols, _prefix)
        nan_row = pd.DataFrame([[pd.NA] * len(frame.columns)], columns=frame.columns)
        res = pd.concat([nan_row, frame, grand_total], ignore_index=True)
        return res

def get_group_with_no_totals(
    frame: pd.DataFrame,
    grouping_fields: list,
    currency_code_to_name: dict,
) -> pd.DataFrame:
    f"""Function to get summation of datatable based on {grouping_fields}
        with totals at the bottom of each node. The order of grouping_fields is very important"""
    first_group_name = grouping_fields[0]
    first_group_list = np.unique(frame[first_group_name])
    res = pd.DataFrame(columns=frame.columns)
    for first_group_item in first_group_list:
        first_group_first_row_df = pd.DataFrame(columns=frame.columns)
        first_group_first_row_df["Group"] = [currency_code_to_name[first_group_item]]
        tmp_df = frame[frame[first_group_name].isin([first_group_item])].copy()
        res = pd.concat([res, first_group_first_row_df,tmp_df])
    return res


def get_group_totals_with_currency(
    frame: pd.DataFrame,
    grouping_fields: list,
    sum_columns: list,
    currency_code_to_name: dict,
) -> pd.DataFrame:
    f"""Function to get summation of datatable based on {grouping_fields}
        with totals at the bottom of each node. The order of grouping_fields is very important"""
    first_group_name = grouping_fields[0]
    second_group_name = grouping_fields[1]
    third_group_name = grouping_fields[2]
    first_group_list = np.unique(frame[first_group_name])
    res = pd.DataFrame(columns=frame.columns)
    all_total = pd.DataFrame(columns=frame.columns)
    all_total[first_group_name] = ["NET INCOME"]
    all_total[sum_columns[-3:]] = [frame[sum_columns[-3:]].sum()]
    for first_group_item in first_group_list:
        first_group_first_row_df = pd.DataFrame(columns=frame.columns)
        first_group_first_row_df[first_group_name] = [first_group_item]
        tmp_df = frame[frame[first_group_name].isin([first_group_item])].copy()
        first_group_total = pd.DataFrame(columns=frame.columns)
        first_group_total[sum_columns[-3:]] = [tmp_df[sum_columns[-3:]].sum()]
        first_group_total[first_group_name] = ["Total - " + first_group_item]
        res = pd.concat([res, first_group_first_row_df])
        second_group_list = np.unique(tmp_df[second_group_name])
        for second_group_item in second_group_list:
            second_group_first_row_df = pd.DataFrame(columns=frame.columns)
            second_group_first_row_df[second_group_name] = [
                currency_code_to_name[second_group_item]
            ]
            tmp_df_2 = tmp_df[
                tmp_df[second_group_name].isin([second_group_item])
            ].copy()
            second_group_total = pd.DataFrame(columns=frame.columns)
            second_group_total[sum_columns] = [tmp_df_2[sum_columns].sum()]
            second_group_total[second_group_name] = [
                "Total - " + currency_code_to_name[second_group_item]
            ]
            res = pd.concat([res, second_group_first_row_df])
            third_group_list = np.unique(tmp_df_2[third_group_name])
            for third_group_item in third_group_list:
                third_group_first_row_df = pd.DataFrame(columns=frame.columns)
                third_group_first_row_df[third_group_name] = [
                    third_group_item# + " (" + second_group_item + ")"
                ]
                tmp_df_3 = tmp_df_2[
                    tmp_df_2[third_group_name].isin([third_group_item])
                ].copy()
                tmp_df_3[grouping_fields] = ""
                third_group_total = pd.DataFrame(columns=frame.columns)
                third_group_total[sum_columns] = [tmp_df_3[sum_columns].sum()]
                third_group_total[third_group_name] = [
                    "Total - " + third_group_item# + " (" + second_group_item + ")"
                ]
                res = pd.concat(
                    [res, third_group_first_row_df, tmp_df_3, third_group_total]
                )
            res = pd.concat([res, second_group_total])
        res = pd.concat([res, first_group_total])
    res = pd.concat([res, all_total])
    return res


def remove_unheld_positions(df: pd.DataFrame, position_col: str) -> pd.DataFrame:
    position_idx = df[position_col].notnull()
    no_qty_idx = df.quantity.isnull()
    return df[~(position_idx & no_qty_idx)]


def get_client_required_date_format(dates: pd.Series) -> pd.Series:
    return dates.dt.strftime(DEFAULT_DATE_FORMAT)


def set_pagination_size(payload: dict) -> None:
    if "pagination" in payload:
        payload["pagination"]["size"] = PAYLOAD_PAGINATION_SIZE


def update_cell_range_values(cell_range: tuple, values: list) -> None:
    cells = [c for c in cell_range if type(c) != MergedCell]
    for cell, header in zip(cells, values):
        cell.value = header


def set_trx_payload_custom_date_range(
    payload: dict, start: str, end: str, months: int = 3
) -> None:
    """Updates the transaction payload to a custom 2-year period."""

    payload["options"]["date_range"]["value"] = "custom"
    payload["options"]["date_range"]["Label"] = "Custom"

    start_date = pd.to_datetime(start) - pd.DateOffset(months=months)
    end_date = pd.to_datetime(end) + pd.DateOffset(months=months)

    payload["options"]["date_range"]["start_date"] = start_date.strftime("%Y-%m-%d")
    payload["options"]["date_range"]["end_date"] = end_date.strftime("%Y-%m-%d")
    payload["settings"]["date"]["date"] = end_date.strftime("%Y-%m-%d")
