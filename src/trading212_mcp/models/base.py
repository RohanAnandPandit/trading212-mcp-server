from enum import StrEnum
from typing import Annotated, TypeVar

from pydantic import BaseModel, ConfigDict, Field

E = TypeVar("E", bound=StrEnum)

# Response enum fields: a known value parses to the enum member, while a value
# Trading 212 adds later is kept as a plain string instead of rejecting the
# whole response. Request models keep strict enums.
OpenEnum = Annotated[E | str, Field(union_mode="left_to_right")]


class ApiModel(BaseModel):
    # Trading 212's public API is still evolving. Ignoring unknown fields keeps
    # additive upstream changes from breaking the MCP server.
    model_config = ConfigDict(extra="ignore")


class Environment(StrEnum):
    DEMO = "demo"
    LIVE = "live"


class RequestModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", allow_inf_nan=False, hide_input_in_errors=True
    )
