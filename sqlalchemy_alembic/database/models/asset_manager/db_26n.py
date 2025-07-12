from decimal import Decimal
from sqlalchemy import Integer, String, JSON, Date, Numeric, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base, TimeStampMixin  # relative import up to database.base


class Position(TimeStampMixin, Base):
    """
    One row per record as received from the 26 North FTP drop.
    Nothing is ‘clean’ yet – everything is text except a few obvious fields.
    """

    __tablename__ = "positions_26n"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_file: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # e.g. 26N_20250715.csv
    row_num: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # line-number in the file

    pos_date: Mapped[str] = mapped_column(String(10))  # "YYYY-MM-DD" as text
    portfolio_code: Mapped[str] = mapped_column(String(30))
    instrument_code_raw: Mapped[str] = mapped_column(String(40))
    quantity_raw: Mapped[str] = mapped_column(String(50))
    market_value_raw: Mapped[str] = mapped_column(String(50))
    amort_cost_raw: Mapped[str] = mapped_column(String(50))

    extra_json: Mapped[dict] = mapped_column(JSON, default=dict)  # full original row

    __table_args__ = (
        # guarantee we don’t double-load a file
        UniqueConstraint("source_file", "row_num", name="uq_26n_file_row"),
        Index("ix_26n_portfolio_date", "portfolio_code", "pos_date"),
    )
