from sqlalchemy import Integer, String, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base, TimeStampMixin


class Position(TimeStampMixin, Base):
    __tablename__ = "positions_nlg"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    row_num: Mapped[int] = mapped_column(Integer, nullable=False)

    position_dt: Mapped[str] = mapped_column(String(10))
    portfolio_raw: Mapped[str] = mapped_column(String(40))
    isin_raw: Mapped[str] = mapped_column(String(20))
    units_raw: Mapped[str] = mapped_column(String(50))
    book_val_raw: Mapped[str] = mapped_column(String(50))

    extra_json: Mapped[dict] = mapped_column(JSON, default=dict)

    __table_args__ = (
        UniqueConstraint("source_file", "row_num", name="uq_nlg_file_row"),
    )
