"""Request-scoped context (replaces flask.g)."""

from __future__ import annotations

import contextvars
import typing

_ctx: contextvars.ContextVar[dict[str, typing.Any]] = contextvars.ContextVar(
    "request_context", default={}
)


def get(key: str, default: typing.Any = None) -> typing.Any:
    return _ctx.get().get(key, default)


def set(key: str, value: typing.Any) -> None:
    _ctx.get()[key] = value


def has(key: str) -> bool:
    return key in _ctx.get()


def reset() -> None:
    _ctx.set({})
