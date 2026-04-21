from typing import Any


def _to_dict(data: Any) -> dict:
    if hasattr(data, "model_dump"):
        return data.model_dump(mode="json")
    return data


def _compute_totals(data_dicts: list[dict]) -> dict:
    totals: dict[str, float] = {}
    for d in data_dicts:
        for key, value in d.items():
            if isinstance(value, (int, float)):
                totals[key] = totals.get(key, 0.0) + value
    return totals


def format_response(
    results: dict[str, Any],
    compute_totals: bool = False,
) -> Any:
    if len(results) == 1:
        data = next(iter(results.values()))
        if isinstance(data, Exception):
            name = next(iter(results.keys()))
            return {"account": name, "error": str(data)}
        return _to_dict(data)

    entries = []
    data_dicts_for_totals = []

    for account_name, data in results.items():
        if isinstance(data, Exception):
            entries.append({"account": account_name, "error": str(data)})
        else:
            serialised = _to_dict(data)
            entries.append({"account": account_name, "data": serialised})
            if compute_totals:
                data_dicts_for_totals.append(serialised)

    if compute_totals and data_dicts_for_totals:
        entries.append({"account": "__totals__", "data": _compute_totals(data_dicts_for_totals)})

    return entries
