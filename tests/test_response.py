import pytest
from utils.response import format_response


def test_single_account_returns_data_directly():
    data = {"free": 100.0, "invested": 500.0}
    result = format_response({"sumeet": data})
    assert result == data


def test_multi_account_returns_labelled_list():
    result = format_response({
        "sumeet": {"free": 100.0},
        "wife": {"free": 200.0},
    })
    assert result == [
        {"account": "sumeet", "data": {"free": 100.0}},
        {"account": "wife",   "data": {"free": 200.0}},
    ]


def test_multi_account_with_totals():
    result = format_response(
        {
            "sumeet": {"free": 100.0, "invested": 500.0, "total": 600.0},
            "wife":   {"free": 200.0, "invested": 300.0, "total": 500.0},
        },
        compute_totals=True,
    )
    assert {"account": "sumeet", "data": {"free": 100.0, "invested": 500.0, "total": 600.0}} in result
    assert {"account": "wife",   "data": {"free": 200.0, "invested": 300.0, "total": 500.0}} in result
    totals_entry = next(e for e in result if e["account"] == "__totals__")
    assert totals_entry["data"]["free"] == pytest.approx(300.0)
    assert totals_entry["data"]["invested"] == pytest.approx(800.0)
    assert totals_entry["data"]["total"] == pytest.approx(1100.0)


def test_partial_failure_included_as_error_entry():
    result = format_response({
        "sumeet": {"free": 100.0},
        "wife":   Exception("API rate limit"),
    })
    sumeet_entry = next(e for e in result if e["account"] == "sumeet")
    assert sumeet_entry["data"] == {"free": 100.0}

    wife_entry = next(e for e in result if e["account"] == "wife")
    assert "error" in wife_entry
    assert "API rate limit" in wife_entry["error"]


def test_single_account_pydantic_model_serialised():
    from pydantic import BaseModel

    class Cash(BaseModel):
        free: float
        invested: float

    result = format_response({"sumeet": Cash(free=50.0, invested=200.0)})
    assert result == {"free": 50.0, "invested": 200.0}


def test_single_account_totals_flag_ignored():
    data = {"free": 100.0, "invested": 500.0}
    result = format_response({"sumeet": data}, compute_totals=True)
    assert result == data


def test_list_of_pydantic_models_serialised():
    from pydantic import BaseModel

    class Position(BaseModel):
        ticker: str
        quantity: float

    result = format_response({
        "sumeet": [Position(ticker="AAPL", quantity=10.0), Position(ticker="MSFT", quantity=5.0)],
        "wife": [Position(ticker="GOOG", quantity=2.0)],
    })

    sumeet = next(e for e in result if e["account"] == "sumeet")
    assert sumeet["data"] == [
        {"ticker": "AAPL", "quantity": 10.0},
        {"ticker": "MSFT", "quantity": 5.0},
    ]
    wife = next(e for e in result if e["account"] == "wife")
    assert wife["data"] == [{"ticker": "GOOG", "quantity": 2.0}]


def test_totals_skips_boolean_fields():
    result = format_response(
        {
            "sumeet": {"free": 100.0, "active": True},
            "wife":   {"free": 200.0, "active": False},
        },
        compute_totals=True,
    )
    totals_entry = next(e for e in result if e["account"] == "__totals__")
    assert totals_entry["data"] == {"free": 300.0}
    assert "active" not in totals_entry["data"]


def test_single_account_exception_returns_error_entry():
    result = format_response({"sumeet": Exception("API down")})
    assert result == {"account": "sumeet", "error": "API down"}


def test_totals_skipped_when_data_is_list():
    result = format_response(
        {
            "sumeet": [{"ticker": "AAPL", "quantity": 10.0}],
            "wife":   [{"ticker": "GOOG", "quantity": 2.0}],
        },
        compute_totals=True,
    )
    # no __totals__ entry because list-shaped data can't be summed field-wise
    assert not any(e["account"] == "__totals__" for e in result)
