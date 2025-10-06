import sys
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.utils.balance_extractor import BalanceExtractor  # noqa: E402


def test_parse_balance_text_with_currency_code():
    extractor = BalanceExtractor(driver=None)
    value, currency = extractor._parse_balance_text("Current balance: USD 1,234.50")

    assert value == pytest.approx(1234.50)
    assert currency == "USD"


def test_parse_balance_text_with_symbol_and_extended_decimals():
    extractor = BalanceExtractor(driver=None)
    value, currency = extractor._parse_balance_text("账户余额：CN¥ 2,345.6789")

    assert value == pytest.approx(2345.6789)
    assert currency == "CNY"


def test_parse_balance_text_without_currency_defaults_to_usd():
    extractor = BalanceExtractor(driver=None)
    value, currency = extractor._parse_balance_text("Balance remaining: 75")

    assert value == pytest.approx(75)
    assert currency == "USD"


def test_regex_extraction_finds_value_in_keyword_section():
    class DummyDriver:
        def __init__(self, page_source: str):
            self.page_source = page_source

    html = """
    <div>
        <span>Current balance</span>
        <strong>US$ 1,500.25</strong>
    </div>
    """

    extractor = BalanceExtractor(driver=DummyDriver(html))
    result = extractor._extract_by_regex_patterns()

    assert result["success"] is True
    assert result["currency"] == "USD"
    assert float(result["balance"]) == pytest.approx(1500.25)
