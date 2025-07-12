import datetime as _dt
from sqlalchemy import MetaData, DateTime, func
from sqlalchemy.orm import declarative_base, declared_attr, Mapped, mapped_column

_naming = MetaData(
    naming_convention={
        "pk": "pk_%(table_name)s",
        "ix": "ix_%(table_name)s_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_label)s",
        "fk": "fk_%(table_name)s_%(column_0_label)s_%(referred_table_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
    }
)

Base = declarative_base(metadata=_naming)


class TimeStampMixin:
    """Adds created_at / updated_at columns to every table that inherits it."""

    created_at: Mapped[_dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[_dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # repr for debugging
    def __repr__(self) -> str:  # pragma: no cover
        cname = self.__class__.__name__
        pk = getattr(self, "id", None)
        return f"<{cname} id={pk}>"
