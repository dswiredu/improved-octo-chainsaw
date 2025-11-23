import uuid
from typing import List
from datetime import date

from sqlalchemy import (
    Column,
    Integer,
    Date,
    String,
    Enum,
    ForeignKey,
    UniqueConstraint,
    PrimaryKeyConstraint,
    Index,
    SmallInteger,
    Numeric,
)
from sqlalchemy.dialects.mysql import CHAR, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base, TimeStampMixin

from decimal import Decimal

# ---------------------------------------------------------------------------
# Lookup Tables
# ---------------------------------------------------------------------------


class Country(TimeStampMixin, Base):
    __tablename__ = "country"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    long_name: Mapped[str] = mapped_column(String(90), unique=True, nullable=False)


class AssetClass(TimeStampMixin, Base):
    __tablename__ = "asset_class"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(60), nullable=False)


class Industry(TimeStampMixin, Base):
    __tablename__ = "industry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)


class Rating(TimeStampMixin, Base):
    __tablename__ = "rating"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    grade: Mapped[str] = mapped_column(
        String(10), unique=True, nullable=False
    )  # Might need to set it up as ENUM


class AssetManager(TimeStampMixin, Base):
    """
    *Manager ID* is the short code (26N, HIMCO …) stable, never changes.
    """

    __tablename__ = "asset_manager"

    id: Mapped[str] = mapped_column(String(12), primary_key=True)  # e.g. "26N"
    name: Mapped[str] = mapped_column(String(80), nullable=False)


# ---------------------------------------------------------------------------
# portfolio & instrument hierarchy
# ---------------------------------------------------------------------------


class Portfolio(TimeStampMixin, Base):
    __tablename__ = "portfolio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    manager_id: Mapped[str] = mapped_column(
        String(12),
        ForeignKey("asset_manager.id", ondelete="CASCADE"),
        nullable=False,
    )

    manager = relationship("AssetManager", backref="portfolios")


class Instrument(TimeStampMixin, Base):
    __tablename__ = "instrument"

    id: Mapped[str] = mapped_column(
        String(30), primary_key=True
    )  # whatever your CUSIP / internal ID is
    name: Mapped[str] = mapped_column(String(120))

    # ← CHANGED: keep as numeric so you can do maths later
    quantity = Column(Integer)
    unit_of_measure: Mapped[SmallInteger] = mapped_column(SmallInteger)
    rating_id: Mapped[int] = mapped_column(ForeignKey("rating.id"))
    industry_id: Mapped[int] = mapped_column(ForeignKey("industry.id"))
    asset_class_id: Mapped[int] = mapped_column(ForeignKey("asset_class.id"))
    country_id: Mapped[int] = mapped_column(ForeignKey("country.id"))

    rating = relationship("Rating")
    industry = relationship("Industry")
    asset_cls = relationship("AssetClass")
    country = relationship("Country")


class PositionSilver(TimeStampMixin, Base):
    """
    Raw position rows exactly as the file comes in.
    """

    __tablename__ = "positions_silver"

    pos_date: Mapped[date] = mapped_column(Date, nullable=False)  # ← YYYY-MM-DD
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolio.id", ondelete="CASCADE"), nullable=False
    )
    instrument_id: Mapped[str] = mapped_column(
        ForeignKey("instrument.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=Decimal(0))
    mv: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=Decimal(0))

    portfolio = relationship("Portfolio")
    instrument = relationship("Instrument")

    __table_args__ = (
        PrimaryKeyConstraint(
            "portfolio_id", "instrument_id", "pos_date", name="pk_bronze"
        ),
        Index("ix_bronze_portfolio_date", "portfolio_id", "pos_date"),
    )


class PositionBronze(TimeStampMixin, Base):
    """
    Raw position rows exactly as the file comes in.
    """

    __tablename__ = "positions_bronze"

    pos_date: Mapped[date] = mapped_column(Date, nullable=False)  # ← YYYY-MM-DD
    portfolio_id: Mapped[str] = mapped_column(String(30))
    instrument_id: Mapped[str] = mapped_column(String(30))
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=Decimal(0))
    mv: Mapped[Integer] = mapped_column(SmallInteger, default=Decimal(0))
    book_v

    __table_args__ = (
        PrimaryKeyConstraint(
            "portfolio_id", "instrument_id", "pos_date", name="pk_bronze"
        ),
        Index("ix_bronze_portfolio_date", "portfolio_id", "pos_date"),
    )
