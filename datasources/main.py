from mysql_connector import MySQLDataSource
from dotenv import load_dotenv
import os

load_dotenv()

# ds.read_table("positions", {
#     "timestamp": ("date", "2024-12-31"),
#     "status": ("in", ["open", "pending"]),
#     "deleted_at": ("null", False)
# })

def main():
    ds = MySQLDataSource(
        dbname="26nriskdb",
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

    df = ds.read_table(
        "positions", 
        {"timestamp": ("date", "2025-06-20")}
    )

    # Check if staging table exists
    if not ds.table_exists("positions_validated"):
        ds.create_table_from_df(df, "positions_validated")

    # Write the data
    ds.write_table(df, "positions_validated", if_exists="append")

if __name__ == "__main__":
    main()