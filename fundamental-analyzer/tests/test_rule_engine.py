from core.rule_engine import evaluate_rules
from models.company_data import CompanyData
from models.rule_model import Rule


def test_rule_engine_returns_pass_fail_and_na() -> None:
    company_data = CompanyData(
        current_price=400,
        book_value=100,
        stock_pe=20,
        industry_pe=25,
        roe=16,
        cfo_5y=None,
        cfo_last_year=None,
    )
    rules = [
        Rule(parameter="roe", operator=">", value=15, rationale="ROE check"),
        Rule(parameter="pe", operator="industry_compare", value=0, rationale="PE vs industry"),
        Rule(parameter="pb", operator="<", value=5, rationale="PB check"),
        Rule(parameter="cfo", operator=">", value=0, rationale="Cash flow check"),
    ]

    results = evaluate_rules(company_data, rules)

    assert results[0].status == "Pass"
    assert results[1].status == "Pass"
    assert results[2].status == "Pass"
    assert results[3].status == "NA"
