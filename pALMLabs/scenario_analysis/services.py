# scenario_analysis/services.py

import pandas as pd
from io import TextIOWrapper
from .models import ScenarioValue


def parse_mapping_file(mapping_file):
    """
    Parse the mapping CSV file where scenario_name is the index.
    Returns a dict: scenario_name -> filename
    """
    df = pd.read_csv(
        TextIOWrapper(mapping_file, encoding="utf-8"), index_col="scenario_name"
    )

    if df.index.has_duplicates:
        raise ValueError("Mapping file contains duplicate scenario names.")

    mapping = df["filename"].to_dict()
    return mapping


def process_scenario_file(file_obj, dataset):
    """
    Reads the CSV, processes and stores ScenarioValue objects linked to the dataset.
    Assumes first column contains variable names, and remaining columns are time series.
    """

    file_obj.seek(0)  # Just in case it was read before
    df = pd.read_csv(file_obj, header=None)
    df = df.dropna(axis=1, how="all")  # Remove empty columns

    df.columns = ["variable"] + list(range(df.shape[1] - 1))
    df.set_index("variable", inplace=True)

    df = df.transpose()
    df.index.name = "timestep"
    df.reset_index(inplace=True)

    long_df = df.melt(id_vars=["timestep"], var_name="variable", value_name="value")
    long_df.dropna(subset=["value"], inplace=True)
    long_df["timestep"] = long_df["timestep"].astype(int)

    values = [
        ScenarioValue(
            dataset=dataset,
            timestep=row["timestep"],
            variable=row["variable"],
            value=row["value"],
        )
        for _, row in long_df.iterrows()
    ]
    ScenarioValue.objects.bulk_create(values)

    dataset.column_names = list(long_df["variable"].unique())
    dataset.status = "done"
    dataset.log(f"Processed {len(values)} values.")
    dataset.save(update_fields=["status", "column_names"])
