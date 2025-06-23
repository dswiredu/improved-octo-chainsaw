from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from urllib.parse import quote_plus
import pandas as pd
from filtering import build_filters


class MySQLDataSource:
    def __init__(
        self, dbname: str, host: str, user: str, password: str, port: int = 3306
    ):
        self.dbname = dbname
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self._engine = self._create_engine()

    def _create_engine(self) -> Engine:
        return create_engine(self.dsn, pool_pre_ping=True)

    @property
    def dsn(self) -> str:
        pw = quote_plus(self.password)
        return f"mysql+pymysql://{self.user}:{pw}@{self.host}:{self.port}/{self.dbname}"

    @property
    def engine(self) -> Engine:
        return self._engine

    def read_table(self, table_name: str, filters: dict = None) -> pd.DataFrame:
        if filters:
            clauses, params = build_filters(filters)
            where_clause = " AND ".join(clauses)
            query = text(f"SELECT * FROM {table_name} WHERE {where_clause}")
        else:
            query = text(f"SELECT * FROM {table_name}")
            params = {}
        return pd.read_sql(query, self.engine, params=params)

    def run_query(self, sql: str, params: dict = None) -> pd.DataFrame:
        return pd.read_sql(text(sql), self.engine, params=params)

    def list_tables(self) -> list[str]:
        inspector = inspect(self.engine)
        return inspector.get_table_names()

    def table_exists(self, table_name: str) -> bool:
        return table_name in self.list_tables()

    def get_columns(self, table_name: str) -> list[str]:
        inspector = inspect(self.engine)
        return [col["name"] for col in inspector.get_columns(table_name)]

    def write_table(
        self,
        df: pd.DataFrame,
        table_name: str,
        if_exists: str = "replace",
        dtype: dict = None,
        chunksize: int = 5000,
    ):
        
        df.to_sql(
            table_name,
            con=self.engine,
            if_exists=if_exists,
            index=False,
            dtype=dtype,
            chunksize=chunksize,
            method="multi",
        )

    def delete_from_table(self, table_name: str, filters: dict):
        if not filters:
            raise ValueError("Filters are required to avoid deleting all rows.")
        clauses, params = build_filters(filters)
        where_clause = " AND ".join(clauses)
        sql = text(f"DELETE FROM {table_name} WHERE {where_clause}")
        with self.engine.begin() as conn:
            conn.execute(sql, params)

    def drop_table(self, table_name: str):
        with self.engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))

    def truncate_table(self, table_name: str):
        with self.engine.begin() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table_name}"))

    def create_table_from_df(
        self, df: pd.DataFrame, table_name: str, dtype: dict = None
    ):
        self.write_table(df.iloc[0:0], table_name, if_exists="fail", dtype=dtype)

    def create_table_from_schema(self, table_name: str, schema: dict, primary_key: str = None, if_not_exists: bool = True):
        """
        Create a table explicitly from a schema dictionary.

        Parameters:
        - table_name (str): Name of the table to create
        - schema (dict): Dictionary of column definitions, e.g.,
            {
                "id": "INT",
                "timestamp": "DATETIME",
                "price": "DECIMAL(20,6)",
                "status": "VARCHAR(50)"
            }
        - primary_key (str, optional): Column to set as PRIMARY KEY
        - if_not_exists (bool): Whether to include IF NOT EXISTS

        This will run SQL like:
        CREATE TABLE IF NOT EXISTS `positions_validated` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `timestamp` DATETIME,
            `price` DECIMAL(20,6),
            `status` VARCHAR(50)
        )
        """
        cols = []
        for col, col_type in schema.items():
            line = f"`{col}` {col_type}"
            if primary_key and col == primary_key:
                line += " PRIMARY KEY"
            cols.append(line)

        clause = ",\n    ".join(cols)
        if_not_exists_sql = "IF NOT EXISTS " if if_not_exists else ""

        sql = f"""
        CREATE TABLE {if_not_exists_sql}`{table_name}` (
            {clause}
        )
        """

        with self.engine.begin() as conn:
            conn.execute(text(sql.strip()))

    def run_stored_procedure(self, procedure_name: str, args: list = None):
        args_str = ", ".join([f":arg{i}" for i in range(len(args))]) if args else ""
        sql = text(f"CALL {procedure_name}({args_str})")
        params = {f"arg{i}": arg for i, arg in enumerate(args)} if args else {}
        with self.engine.begin() as conn:
            conn.execute(sql, params)
