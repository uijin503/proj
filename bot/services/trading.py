from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Holding, Transaction, User
from bot.services import market
from bot.services.bank import UserNotFoundError


class InsufficientFundsError(Exception):
    pass


class InsufficientSharesError(Exception):
    pass


def _to_krw(amount_native: Decimal, currency: str, fx_rate: Decimal) -> Decimal:
    if currency == "KRW":
        return amount_native
    return amount_native * fx_rate


async def _get_fx_rate(currency: str) -> Decimal:
    if currency == "KRW":
        return Decimal("1")
    return await market.get_usdkrw_rate()


async def buy(session: AsyncSession, discord_id: int, symbol_input: str, quantity: Decimal) -> dict:
    if quantity <= 0:
        raise ValueError("수량은 0보다 커야 합니다.")

    user = await session.get(User, discord_id)
    if user is None:
        raise UserNotFoundError()

    quote = await market.get_quote(symbol_input)
    fx_rate = await _get_fx_rate(quote.currency)
    cost_krw = (_to_krw(quote.price, quote.currency, fx_rate) * quantity).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )

    if user.cash_balance < cost_krw:
        raise InsufficientFundsError()

    result = await session.execute(
        select(Holding).where(Holding.user_id == discord_id, Holding.symbol == quote.symbol)
    )
    holding = result.scalar_one_or_none()
    if holding is None:
        holding = Holding(
            user_id=discord_id,
            symbol=quote.symbol,
            market=quote.market,
            quantity=Decimal("0"),
            cost_basis_krw=Decimal("0"),
        )
        session.add(holding)

    holding.quantity += quantity
    holding.cost_basis_krw += cost_krw
    user.cash_balance -= cost_krw

    session.add(
        Transaction(
            user_id=discord_id,
            type="BUY",
            symbol=quote.symbol,
            market=quote.market,
            quantity=quantity,
            price_native=quote.price,
            fx_rate=fx_rate,
            amount_krw=-cost_krw,
            balance_after=user.cash_balance,
        )
    )

    return {"quote": quote, "cost_krw": cost_krw, "quantity": quantity, "balance": user.cash_balance}


async def sell(session: AsyncSession, discord_id: int, symbol_input: str, quantity: Decimal) -> dict:
    if quantity <= 0:
        raise ValueError("수량은 0보다 커야 합니다.")

    user = await session.get(User, discord_id)
    if user is None:
        raise UserNotFoundError()

    quote = await market.get_quote(symbol_input)

    result = await session.execute(
        select(Holding).where(Holding.user_id == discord_id, Holding.symbol == quote.symbol)
    )
    holding = result.scalar_one_or_none()
    if holding is None or holding.quantity < quantity:
        raise InsufficientSharesError()

    fx_rate = await _get_fx_rate(quote.currency)
    proceeds_krw = (_to_krw(quote.price, quote.currency, fx_rate) * quantity).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )

    avg_cost_per_share = holding.cost_basis_krw / holding.quantity
    cost_basis_sold = (avg_cost_per_share * quantity).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    realized_pnl = proceeds_krw - cost_basis_sold

    holding.quantity -= quantity
    holding.cost_basis_krw -= cost_basis_sold
    if holding.quantity == 0:
        holding.cost_basis_krw = Decimal("0")

    user.cash_balance += proceeds_krw

    session.add(
        Transaction(
            user_id=discord_id,
            type="SELL",
            symbol=quote.symbol,
            market=quote.market,
            quantity=quantity,
            price_native=quote.price,
            fx_rate=fx_rate,
            amount_krw=proceeds_krw,
            balance_after=user.cash_balance,
        )
    )

    return {
        "quote": quote,
        "proceeds_krw": proceeds_krw,
        "realized_pnl": realized_pnl,
        "quantity": quantity,
        "balance": user.cash_balance,
    }


async def get_holdings(session: AsyncSession, discord_id: int) -> list[Holding]:
    result = await session.execute(
        select(Holding).where(Holding.user_id == discord_id, Holding.quantity > 0)
    )
    return list(result.scalars())


async def get_portfolio_value(session: AsyncSession, discord_id: int) -> dict:
    user = await session.get(User, discord_id)
    if user is None:
        raise UserNotFoundError()

    holdings = await get_holdings(session, discord_id)

    positions = []
    total_value = Decimal("0")
    for h in holdings:
        quote = await market.get_quote(h.symbol)
        fx_rate = await _get_fx_rate(quote.currency)
        value_krw = _to_krw(quote.price, quote.currency, fx_rate) * h.quantity
        pnl = value_krw - h.cost_basis_krw
        pnl_pct = (pnl / h.cost_basis_krw * 100) if h.cost_basis_krw else Decimal("0")
        positions.append(
            {
                "symbol": h.symbol,
                "market": h.market,
                "quantity": h.quantity,
                "quote": quote,
                "value_krw": value_krw,
                "cost_basis_krw": h.cost_basis_krw,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
            }
        )
        total_value += value_krw

    return {
        "cash": user.cash_balance,
        "positions": positions,
        "stock_value": total_value,
        "total_assets": user.cash_balance + total_value,
    }
