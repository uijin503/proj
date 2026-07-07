from bot.services.market import _resolve_kr_code


def test_resolve_numeric_code():
    assert _resolve_kr_code("005930") == "005930"


def test_resolve_korean_name():
    assert _resolve_kr_code("삼성전자") == "005930"
    assert _resolve_kr_code("네이버") == "035420"


def test_resolve_unknown_returns_none():
    assert _resolve_kr_code("존재하지않는종목") is None


def test_resolve_us_ticker_returns_none():
    assert _resolve_kr_code("AAPL") is None
