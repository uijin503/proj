from decimal import Decimal

from bot.services.market import FxQuote, _resolve_kr_code


def test_resolve_numeric_code():
    assert _resolve_kr_code("005930") == "005930"


def test_resolve_korean_name():
    assert _resolve_kr_code("삼성전자") == "005930"
    assert _resolve_kr_code("네이버") == "035420"


def test_resolve_unknown_returns_none():
    assert _resolve_kr_code("존재하지않는종목") is None


def test_resolve_us_ticker_returns_none():
    assert _resolve_kr_code("AAPL") is None


def test_fx_quote_change():
    q = FxQuote(pair="USD/KRW", rate=Decimal("1400"), prev_close=Decimal("1350"))
    assert q.change == Decimal("50")
    assert q.change_pct == Decimal("50") / Decimal("1350") * 100


def test_fx_quote_change_zero_prev_close():
    q = FxQuote(pair="USD/KRW", rate=Decimal("1400"), prev_close=Decimal("0"))
    assert q.change_pct == Decimal("0")
