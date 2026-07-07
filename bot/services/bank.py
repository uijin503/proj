from __future__ import annotations

import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Transaction, User

DAILY_COOLDOWN_HOURS = 20


class UserNotFoundError(Exception):
    pass


class InsufficientFundsError(Exception):
    pass


class CooldownError(Exception):
    def __init__(self, remaining: datetime.timedelta):
        self.remaining = remaining
        super().__init__(str(remaining))


async def get_or_create_user(
    session: AsyncSession, discord_id: int, username: str, initial_balance: Decimal
) -> User:
    user = await session.get(User, discord_id)
    if user is None:
        user = User(discord_id=discord_id, username=username, cash_balance=initial_balance)
        session.add(user)
        await session.flush()
    elif user.username != username:
        user.username = username
    return user


async def get_balance(session: AsyncSession, discord_id: int) -> Decimal:
    user = await session.get(User, discord_id)
    if user is None:
        raise UserNotFoundError(discord_id)
    return user.cash_balance


async def transfer(
    session: AsyncSession, from_id: int, to_id: int, amount: Decimal, memo: str | None = None
) -> None:
    if amount <= 0:
        raise ValueError("송금 금액은 0보다 커야 합니다.")
    if from_id == to_id:
        raise ValueError("자기 자신에게는 송금할 수 없습니다.")

    sender = await session.get(User, from_id)
    receiver = await session.get(User, to_id)
    if sender is None or receiver is None:
        raise UserNotFoundError()
    if sender.cash_balance < amount:
        raise InsufficientFundsError()

    sender.cash_balance -= amount
    receiver.cash_balance += amount

    session.add(
        Transaction(
            user_id=sender.discord_id,
            type="TRANSFER_OUT",
            amount_krw=-amount,
            balance_after=sender.cash_balance,
            counterparty_id=receiver.discord_id,
            memo=memo,
        )
    )
    session.add(
        Transaction(
            user_id=receiver.discord_id,
            type="TRANSFER_IN",
            amount_krw=amount,
            balance_after=receiver.cash_balance,
            counterparty_id=sender.discord_id,
            memo=memo,
        )
    )


async def claim_daily(
    session: AsyncSession, discord_id: int, bonus: Decimal, cooldown_hours: int = DAILY_COOLDOWN_HOURS
) -> Decimal:
    user = await session.get(User, discord_id)
    if user is None:
        raise UserNotFoundError()

    now = datetime.datetime.now(datetime.timezone.utc)
    if user.last_daily_at is not None:
        elapsed = now - user.last_daily_at
        cooldown = datetime.timedelta(hours=cooldown_hours)
        if elapsed < cooldown:
            raise CooldownError(cooldown - elapsed)

    user.cash_balance += bonus
    user.last_daily_at = now
    session.add(
        Transaction(
            user_id=user.discord_id,
            type="DAILY_BONUS",
            amount_krw=bonus,
            balance_after=user.cash_balance,
        )
    )
    return user.cash_balance


async def get_recent_transactions(
    session: AsyncSession, discord_id: int, limit: int = 10
) -> list[Transaction]:
    result = await session.execute(
        select(Transaction)
        .where(Transaction.user_id == discord_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars())
