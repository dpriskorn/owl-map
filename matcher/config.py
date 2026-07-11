"""Application configuration."""

from __future__ import annotations

import importlib
import typing


class Config:
    """Configuration loaded from a Python module."""

    def __init__(self) -> None:
        self._data: dict[str, typing.Any] = {}

    def from_object(self, module_path: str) -> None:
        """Load config from a Python module path (e.g. 'config.default')."""
        module = importlib.import_module(module_path)
        self._data = {
            key: value
            for key, value in vars(module).items()
            if key.isupper()
        }

    def from_dict(self, data: dict[str, typing.Any]) -> None:
        """Load config from a dict."""
        self._data.update(data)

    def get(self, key: str, default: typing.Any = None) -> typing.Any:
        return self._data.get(key, default)

    def __getitem__(self, key: str) -> typing.Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data


config = Config()
