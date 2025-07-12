"""
connectors package
------------------
Import each concrete *DataSource* implementation here and expose it
in ``__all__`` so other code can just do:

    from connectors import MySQLDataSource          # or PostgresDataSource
"""

from connectors.mysql_connector import MySQLDataSource

__all__ = [
    "MySQLDataSource",
    # "PostGresDataSource" later
]
