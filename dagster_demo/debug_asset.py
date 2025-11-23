from dagster import build_asset_context
from dagster_etl.defs.bronze_factory import bronze_assets


def run_test(client: str, dte: str) -> None:
    """Run one bronze partition (+ its upstream raws) inside a Python shell."""
    # pick the bronze asset for the requested client
    bronze_asset = next(a for a in bronze_assets if a.key.path[-1] == client)

    # only the date dimension remains
    ctx = build_asset_context(
        partition_key=dte,  # e.g. "2025-07-08"
        resources={"noop_io": object()},  # satisfy the io-manager requirement
    )

    bronze_df = bronze_asset(ctx)  # triggers raw → bronze inside Python
    print(bronze_df.head())


if __name__ == "__main__":
    run_test(client="test_client", dte="2025-07-08")
