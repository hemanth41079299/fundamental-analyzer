from core.extractor import FundamentalExtractor
from core.parser_utils import parse_numeric_value


def test_parse_numeric_value_handles_percent_and_commas() -> None:
    assert parse_numeric_value("1,234.5%") == 1234.5
    assert parse_numeric_value("(45.2)") == -45.2
    assert parse_numeric_value("NA") is None


def test_extractor_returns_null_for_missing_metrics() -> None:
    text = """
    Company Name: Alpha Industries
    Market Cap: 12,345 Cr
    ROE: 18.5%
    Debt to Equity: 0.3
    """
    extractor = FundamentalExtractor()
    result = extractor.extract(text, source_file="alpha.pdf")

    assert result.company_name == "Alpha Industries"
    assert result.market_cap_cr == 12345.0
    assert result.roe == 18.5
    assert result.debt_to_equity == 0.3
    assert result.roce is None
