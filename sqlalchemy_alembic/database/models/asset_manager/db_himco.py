from sqlalchemy import Integer, String, JSON, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base, TimeStampMixin


class Position(TimeStampMixin, Base):
    __tablename__ = "positions_himco"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    row_num: Mapped[int] = mapped_column(Integer, nullable=False)

    trade_dt: Mapped[str] = mapped_column(String(10))  # HIMCO column name differs
    acct_number: Mapped[str] = mapped_column(String(30))
    cusip_raw: Mapped[str] = mapped_column(String(12))
    par_amt_raw: Mapped[str] = mapped_column(String(50))
    mv_raw: Mapped[str] = mapped_column(String(50))

    extra_json: Mapped[dict] = mapped_column(JSON, default=dict)

    __table_args__ = (
        UniqueConstraint("source_file", "row_num", name="uq_himco_file_row"),
        Index("ix_himco_acct_trade_dt", "acct_number", "trade_dt"),
    )
