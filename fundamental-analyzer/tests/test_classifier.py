from core.classifier import classify_market_cap


def test_market_cap_classification_boundaries() -> None:
    assert classify_market_cap(60000) == "large_cap"
    assert classify_market_cap(5000) == "mid_cap"
    assert classify_market_cap(4999) == "small_cap"
    assert classify_market_cap(100) == "micro_cap"
    assert classify_market_cap(None) == "unknown"
