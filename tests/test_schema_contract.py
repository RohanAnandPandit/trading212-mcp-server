"""Check implementation coverage against the reviewed public schema snapshot."""

import json
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from trading212_mcp import models
from trading212_mcp.models.history import ReportDataIncludedResponse

SCHEMAS = json.loads(
    (Path(__file__).resolve().parents[1] / "docs/api.json").read_text()
)["components"]["schemas"]
OBJECTS = [
    (name, schema) for name, schema in SCHEMAS.items() if schema.get("properties")
]


@pytest.mark.parametrize("name,schema", OBJECTS, ids=[n for n, _ in OBJECTS])
def test_schema_fields_and_enums_are_represented(name, schema):
    # Preserve the public Python spelling while covering the upstream model.
    model = getattr(
        models, "TradeableInstrument" if name == "TradableInstrument" else name
    )
    candidates = [model]
    if name == "ReportDataIncluded":
        candidates.append(ReportDataIncludedResponse)
    for candidate in candidates:
        assert set(schema["properties"]) <= set(candidate.model_fields)
        for field, definition in schema["properties"].items():
            if "$ref" in definition:
                definition = SCHEMAS[definition["$ref"].rsplit("/", 1)[-1]]
            for value in definition.get("enum", []):
                parsed = TypeAdapter(
                    candidate.model_fields[field].annotation
                ).validate_python(value)
                assert parsed == value
