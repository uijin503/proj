from decimal import Decimal

from bot.utils.formatting import format_krw, format_native


def test_format_krw():
    assert format_krw(Decimal("10000000")) == "10,000,000원"
    assert format_krw(Decimal("0")) == "0원"


def test_format_native_krw():
    assert format_native(Decimal("71000"), "KRW") == "71,000원"


def test_format_native_usd():
    assert format_native(Decimal("123.456"), "USD") == "$123.46"
