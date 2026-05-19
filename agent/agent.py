"""Gemini agent that summarises Slack channel activity grounded via MCP.

Architecture:
  - Gemini 2.0 Flash on Vertex AI is the planner / responder.
  - The Slack MCP tool surface is exposed by `agent.tools.slack_toolset()`.
    Without credentials it returns an in-process `StubToolset` over a fixture
    workspace (5 channels, ~50 messages incl. one realistic incident thread);
    with `SLACK_BOT_TOKEN` it spawns `@modelcontextprotocol/server-slack`.
  - The agent picks among `list_channels`, `get_channel_history`,
    `search_messages`, `get_user`, `get_thread_replies` to summarise activity
    in a channel or thread.

Run locally with `streamlit run app/streamlit_app.py` for the demo dashboard,
or `adk web .` for the ADK chat UI. Deploy with `adk deploy cloud_run --with_ui`.
"""

from __future__ import annotations

import os
from typing import Any

from google.adk.agents import Agent

from .tools import slack_toolset


SYSTEM_PROMPT = """\
You are a Slack activity summariser. Your only data source is the Slack MCP
tool surface; never invent message text, channel names, users, or timestamps.

Tool playbook:
1. Resolve the channel first. If the user gives a hash-name (`#incidents`),
   strip the hash and pass it as `channel`. If the channel is ambiguous, call
   `list_channels` and pick the closest name match.
2. For "summarise / what happened" questions: call `get_channel_history` with
   the requested time window (default 24 hours). Group messages by thread
   when one parent ts has multiple replies, and call `get_thread_replies`
   once per thread you summarise.
3. For "did anyone mention X?" questions: use `search_messages` with the
   user's phrase, scoped to the channel when one is given.
4. Use `get_user` only when you need to surface a real name and only have a
   user id.

Answer rules:
- Lead with a one-line headline ("Incident: Vertex AI quota exhaustion, resolved 02:30 UTC").
- Then a bullet list of the key turns, each tagged with the speaker's handle.
- Treat resolved threads as resolved; do not raise an alarm for them.
- If the channel has no messages in the window, say so plainly.
- Keep summaries under eight bullets unless the user asks for a long form.
"""


def _build_root_agent() -> Agent:
    toolset = slack_toolset()
    return Agent(
        model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-001"),
        name="slack_channels_agent",
        instruction=SYSTEM_PROMPT,
        tools=[toolset],
    )


def __getattr__(name: str) -> Any:
    """Lazy module attribute access.

    `root_agent` is built on first access, not at import time. That keeps imports
    cheap (and testable) without requiring a live Slack token. ADK's loader
    reads `agent.root_agent`, which triggers this hook the first time it's
    referenced.
    """
    if name == "root_agent":
        value = _build_root_agent()
        globals()["root_agent"] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
