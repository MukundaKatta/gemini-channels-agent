"""Public package surface for the Slack channels agent.

`root_agent` is lazy: it is constructed on first access via `agent.agent.__getattr__`.
Importing this package alone does not require Slack credentials, so the offline
stub demo and smoke tests both import safely with no real-tenant credentials.
"""

from __future__ import annotations

from typing import Any

__all__ = ["root_agent"]


def __getattr__(name: str) -> Any:
    if name == "root_agent":
        from . import agent as _agent

        value = _agent.root_agent
        globals()["root_agent"] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
