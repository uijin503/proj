from __future__ import annotations

import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    """가상 은행 계좌 역할을 겸하는 유저 레코드."""

    __tablename__ = "users"

    discord_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(100))
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    last_daily_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    holdings: Mapped[list["Holding"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Holding(Base):
    """유저가 보유 중인 종목 (평균 매수 원가는 원화 환산 기준으로 누적)."""

    __tablename__ = "holdings"
    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_holdings_user_symbol"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.discord_id"))
    symbol: Mapped[str] = mapped_column(String(20))
    market: Mapped[str] = mapped_column(String(4))  # "KR" or "US"
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=Decimal("0"))
    cost_basis_krw: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0"))

    user: Mapped["User"] = relationship(back_populates="holdings")


class Transaction(Base):
    """은행/증권 거래 내역 (입출금, 송금, 매수/매도, 출석 보너스 등)."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.discord_id"), index=True)
    type: Mapped[str] = mapped_column(String(20))
    symbol: Mapped[str | None] = mapped_column(String(20), nullable=True)
    market: Mapped[str | None] = mapped_column(String(4), nullable=True)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    price_native: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    fx_rate: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    amount_krw: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    balance_after: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    counterparty_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.discord_id"), nullable=True)
    memo: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
