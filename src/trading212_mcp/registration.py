"""Consistent MCP annotations and safe errors for API-backed handlers."""

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from mcp.server.mcpserver.exceptions import ResourceError
from mcp.types import ToolAnnotations
from pydantic import ValidationError

from .errors import Trading212Error

P = ParamSpec("P")
R = TypeVar("R")


def annotations(*, write: bool) -> ToolAnnotations:
    return ToolAnnotations(
        read_only_hint=not write,
        destructive_hint=write,
        idempotent_hint=not write,
        open_world_hint=True,
    )


def safe_handler(fn: Callable[P, R]) -> Callable[P, R]:
    @wraps(fn)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return fn(*args, **kwargs)
        except Trading212Error as exc:
            raise ResourceError(str(exc)) from None
        except ValidationError:
            raise ResourceError(
                "Invalid request parameters or unexpected Trading 212 response format."
            ) from None

    return wrapped
