from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import yfinance as yf

_KR_STOCKS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "kr_stocks.json"
_kr_name_to_code: dict[str, str] = json.loads(_KR_STOCKS_PATH.read_text(encoding="utf-8"))

_FX_CACHE_TTL_SECONDS = 60
_fx_cache: dict[str, tuple[Decimal, float]] = {}


class SymbolNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class Quote:
    symbol: str
    market: str  # "KR" or "US"
    currency: str  # "KRW" or "USD"
    name: str
    price: Decimal
    prev_close: Decimal

    @property
    def change(self) -> Decimal:
        return self.price - self.prev_close

    @property
    def change_pct(self) -> Decimal:
        if self.prev_close == 0:
            return Decimal("0")
        return (self.change / self.prev_close) * 100


def _resolve_kr_code(user_input: str) -> str | None:
    if user_input.isdigit() and len(user_input) == 6:
        return user_input
    return _kr_name_to_code.get(user_input)


def _fetch_yf_quote_sync(yf_symbol: str) -> tuple[Decimal, Decimal, str, str]:
    ticker = yf.Ticker(yf_symbol)
    hist = ticker.history(period="5d", interval="1d")
    if hist.empty:
        raise SymbolNotFoundError(yf_symbol)

    price = Decimal(str(hist["Close"].iloc[-1]))
    prev_close = Decimal(str(hist["Close"].iloc[-2])) if len(hist) > 1 else price

    currency = "KRW" if yf_symbol.endswith((".KS", ".KQ")) else "USD"
    name = yf_symbol
    try:
        info = ticker.get_info()
        currency = info.get("currency") or currency
        name = info.get("shortName") or info.get("longName") or yf_symbol
    except Exception:
        pass

    return price, prev_close, currency, name


async def get_quote(user_input: str) -> Quote:
    user_input = user_input.strip()
    if not user_input:
        raise SymbolNotFoundError("종목을 입력해주세요.")

    kr_code = _resolve_kr_code(user_input)
    if kr_code:
        for suffix in (".KS", ".KQ"):
            yf_symbol = kr_code + suffix
            try:
                price, prev_close, currency, name = await asyncio.to_thread(_fetch_yf_quote_sync, yf_symbol)
                return Quote(kr_code, "KR", currency, name, price, prev_close)
            except SymbolNotFoundError:
                continue
        raise SymbolNotFoundError(f"'{user_input}' 종목을 찾을 수 없습니다.")

    yf_symbol = user_input.upper()
    try:
        price, prev_close, currency, name = await asyncio.to_thread(_fetch_yf_quote_sync, yf_symbol)
    except SymbolNotFoundError:
        raise SymbolNotFoundError(f"'{user_input}' 종목을 찾을 수 없습니다.")
    return Quote(yf_symbol, "US", currency, name, price, prev_close)


def _fetch_fx_sync(pair: str) -> Decimal:
    ticker = yf.Ticker(pair)
    hist = ticker.history(period="5d", interval="1d")
    if hist.empty:
        raise SymbolNotFoundError(pair)
    return Decimal(str(hist["Close"].iloc[-1]))


async def get_usdkrw_rate() -> Decimal:
    now = time.monotonic()
    cached = _fx_cache.get("USDKRW")
    if cached and now - cached[1] < _FX_CACHE_TTL_SECONDS:
        return cached[0]

    rate = await asyncio.to_thread(_fetch_fx_sync, "KRW=X")
    _fx_cache["USDKRW"] = (rate, now)
    return rate
