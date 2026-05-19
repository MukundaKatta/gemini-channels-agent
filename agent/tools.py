"""Slack MCP tool surface — stub server for offline demos + real-tenant adapter.

The stub mirrors the public tool names exposed by the official Slack MCP server
(https://github.com/modelcontextprotocol/servers/tree/main/src/slack and
equivalents): `list_channels`, `get_channel_history`, `search_messages`,
`get_user`, `get_thread_replies`. Each stub tool reads from an in-memory
workspace fixture so the demo runs deterministically without Slack tokens.

When `SLACK_BOT_TOKEN` is set, `slack_toolset()` returns a real `McpToolset`
wired to the Slack MCP server over stdio. Otherwise it returns a local
`StubToolset` that the ADK agent can call exactly the same way.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable


_NOW = datetime(2026, 5, 19, 9, 0, tzinfo=timezone.utc)


def _ts(hours_ago: float) -> str:
    """Slack-style epoch timestamp: '1715942400.123456'."""
    dt = _NOW - timedelta(hours=hours_ago)
    return f"{dt.timestamp():.6f}"


# ---------------------------------------------------------------------------
# Fixture: 1 workspace, 5 channels, 50 sample messages across the last 7 days,
# with one realistic incident thread in #incidents.
# ---------------------------------------------------------------------------

WORKSPACE = {"id": "T_DEMO", "name": "Demo Workspace"}

USERS = {
    "U_MUK": {"id": "U_MUK", "name": "mukunda", "real_name": "Mukunda Katta"},
    "U_ALI": {"id": "U_ALI", "name": "ali", "real_name": "Ali R"},
    "U_JAY": {"id": "U_JAY", "name": "jay", "real_name": "Jay K"},
    "U_PRI": {"id": "U_PRI", "name": "priya", "real_name": "Priya S"},
    "U_OPS": {"id": "U_OPS", "name": "ops-bot", "real_name": "Ops Bot"},
}

CHANNELS = [
    {"id": "C_GEN", "name": "general", "purpose": "Company-wide chatter"},
    {"id": "C_INC", "name": "incidents", "purpose": "Active incidents only"},
    {"id": "C_PLAT", "name": "eng-platform", "purpose": "Platform engineering"},
    {"id": "C_DEV", "name": "dev", "purpose": "Day-to-day dev chat"},
    {"id": "C_RAN", "name": "random", "purpose": "Off-topic"},
]


def _msg(
    channel: str, user: str, text: str, hours_ago: float,
    *, thread_ts: str | None = None,
) -> dict[str, Any]:
    ts = _ts(hours_ago)
    return {
        "channel": channel,
        "user": user,
        "ts": ts,
        "text": text,
        "thread_ts": thread_ts or ts,
    }


# Incident thread in #incidents (within the last 24h) — used for the
# "summarise unread messages in #incidents" demo question.
_INC_PARENT_TS = _ts(8.0)
INCIDENT_THREAD = [
    {
        "channel": "C_INC", "user": "U_OPS", "ts": _INC_PARENT_TS,
        "thread_ts": _INC_PARENT_TS,
        "text": "PagerDuty: notes-agent Cloud Run service 5xx rate at 8% (threshold 1%).",
    },
    {
        "channel": "C_INC", "user": "U_MUK", "ts": _ts(7.8),
        "thread_ts": _INC_PARENT_TS,
        "text": "Acking. Pulling logs now. First 5xx at 01:12 UTC.",
    },
    {
        "channel": "C_INC", "user": "U_MUK", "ts": _ts(7.6),
        "thread_ts": _INC_PARENT_TS,
        "text": "Looks like Vertex AI quota exhaustion on gemini-2.0-flash in us-central1.",
    },
    {
        "channel": "C_INC", "user": "U_ALI", "ts": _ts(7.4),
        "thread_ts": _INC_PARENT_TS,
        "text": "Requesting quota bump from console. ETA 20 min.",
    },
    {
        "channel": "C_INC", "user": "U_MUK", "ts": _ts(7.0),
        "thread_ts": _INC_PARENT_TS,
        "text": "Quota raised to 600 QPM. 5xx rate dropping. Will leave alert hot for 30 min.",
    },
    {
        "channel": "C_INC", "user": "U_OPS", "ts": _ts(6.5),
        "thread_ts": _INC_PARENT_TS,
        "text": "Incident resolved. 5xx rate back under 1%. Postmortem doc to follow.",
    },
]

MESSAGES: list[dict[str, Any]] = [
    # ---------------- general ----------------
    _msg("C_GEN", "U_MUK", "Morning! Shipping the channels agent today.", 2.0),
    _msg("C_GEN", "U_JAY", "Nice. Demo video due Friday?", 1.5),
    _msg("C_GEN", "U_MUK", "Yep. All three agents in one cut.", 1.4),
    _msg("C_GEN", "U_PRI", "Anyone going to the Devpost office hours?", 30),
    _msg("C_GEN", "U_JAY", "I'll be there.", 29.5),
    _msg("C_GEN", "U_MUK", "Pushed the Notion agent stub. Streamlit page works.", 50),
    _msg("C_GEN", "U_ALI", "LGTM, opening a PR for the dashboard polish.", 49.5),
    _msg("C_GEN", "U_MUK", "Reminder: standup moved to 9:30.", 72),
    _msg("C_GEN", "U_PRI", "ack", 71.5),
    _msg("C_GEN", "U_JAY", "Lunch?", 100),

    # ---------------- incidents (incl. thread above) ----------------
    *INCIDENT_THREAD,
    _msg("C_INC", "U_OPS", "Heartbeat OK.", 26),
    _msg("C_INC", "U_OPS", "Heartbeat OK.", 50),

    # ---------------- eng-platform ----------------
    _msg("C_PLAT", "U_ALI", "I'm seeing slow cold-starts on tickets-agent. Adding pre-warm.", 4),
    _msg("C_PLAT", "U_MUK", "Same. Bumping min-instances to 1.", 3.5),
    _msg("C_PLAT", "U_JAY", "Trace export to Cloud Logging is wired up.", 12),
    _msg("C_PLAT", "U_MUK", "MCP stdio reconnect loop on disconnect — known issue, will patch.", 20),
    _msg("C_PLAT", "U_ALI", "Linear MCP server v0.4 has the relations endpoint we need.", 28),
    _msg("C_PLAT", "U_PRI", "I'll review the agent-safety guardrail PR today.", 36),
    _msg("C_PLAT", "U_MUK", "Cloud Run image down to 240MB. Better.", 55),
    _msg("C_PLAT", "U_JAY", "Notion stub fixture committed.", 60),
    _msg("C_PLAT", "U_MUK", "Slack stub fixture next.", 6),
    _msg("C_PLAT", "U_ALI", "After we land that, can we hook up the eval harness?", 5),

    # ---------------- dev ----------------
    _msg("C_DEV", "U_PRI", "Bumped google-adk to 0.4.1.", 2),
    _msg("C_DEV", "U_MUK", "Streamlit page renders fine in dark mode now.", 22),
    _msg("C_DEV", "U_JAY", "ADK web UI sometimes loses tool list on reload — repro?", 24),
    _msg("C_DEV", "U_MUK", "Repro'd. Filing PLAT-31.", 23.5),
    _msg("C_DEV", "U_PRI", "PR open: dashboard polish.", 40),
    _msg("C_DEV", "U_ALI", "Reviewing.", 39),
    _msg("C_DEV", "U_MUK", "Merged.", 38),
    _msg("C_DEV", "U_JAY", "thanks!", 37.8),
    _msg("C_DEV", "U_PRI", "Tests are flaky on the cycle-filter case — looking.", 65),
    _msg("C_DEV", "U_MUK", "Fixed by pinning the fixture clock to a constant.", 62),

    # ---------------- random ----------------
    _msg("C_RAN", "U_JAY", "New espresso machine in the kitchen.", 18),
    _msg("C_RAN", "U_PRI", "PSA: lunch truck on the south lot.", 70),
    _msg("C_RAN", "U_MUK", "Watched the Apollo doc last night, recommend.", 90),
    _msg("C_RAN", "U_ALI", "Anyone reading 'Designing Data-Intensive Applications' rev 2?", 110),
    _msg("C_RAN", "U_JAY", "I am — slow but worth it.", 109),
    _msg("C_RAN", "U_MUK", "team lunch friday?", 130),
    _msg("C_RAN", "U_PRI", "yes pls", 129),
]


# ---------------------------------------------------------------------------
# Stub tools — names mirror the official Slack MCP server.
# ---------------------------------------------------------------------------


def list_channels() -> dict[str, Any]:
    """All channels in the workspace."""
    return {"channels": CHANNELS}


def get_channel_history(
    channel: str,
    hours: float = 24,
    limit: int = 100,
) -> dict[str, Any]:
    """Messages in `channel` posted within the last `hours` hours.

    `channel` accepts either the channel id (`C_INC`) or a human name (`incidents`).
    """
    cid = _resolve_channel(channel)
    cutoff = (_NOW - timedelta(hours=hours)).timestamp()
    rows = [m for m in MESSAGES if m["channel"] == cid and float(m["ts"]) >= cutoff]
    rows.sort(key=lambda m: float(m["ts"]))
    return {"messages": rows[-limit:], "has_more": len(rows) > limit}


def search_messages(query: str, channel: str | None = None, limit: int = 25) -> dict[str, Any]:
    """Full-text search across all (or one) channel."""
    q = query.lower()
    rows = MESSAGES
    if channel:
        rows = [m for m in rows if m["channel"] == _resolve_channel(channel)]
    hits = [m for m in rows if q in m["text"].lower()]
    return {"matches": hits[:limit]}


def get_user(user_id: str) -> dict[str, Any]:
    """Look up a user by id."""
    return USERS.get(user_id, {})


def get_thread_replies(channel: str, thread_ts: str) -> dict[str, Any]:
    """All messages in a thread, in chronological order."""
    cid = _resolve_channel(channel)
    rows = [m for m in MESSAGES if m["channel"] == cid and m.get("thread_ts") == thread_ts]
    rows.sort(key=lambda m: float(m["ts"]))
    return {"messages": rows}


def _resolve_channel(name_or_id: str) -> str:
    """Allow callers to pass either `C_INC` or `incidents` or `#incidents`."""
    s = name_or_id.lstrip("#")
    for c in CHANNELS:
        if c["id"] == s or c["name"] == s:
            return c["id"]
    return s


STUB_TOOLS: dict[str, Callable[..., dict[str, Any]]] = {
    "list_channels": list_channels,
    "get_channel_history": get_channel_history,
    "search_messages": search_messages,
    "get_user": get_user,
    "get_thread_replies": get_thread_replies,
}


@dataclass
class StubToolset:
    """A minimal stand-in for `google.adk.tools.mcp_tool.McpToolset`."""

    tools: list[Callable[..., Any]] = field(
        default_factory=lambda: list(STUB_TOOLS.values())
    )

    def call(self, name: str, **kwargs: Any) -> Any:
        if name not in STUB_TOOLS:
            raise KeyError(f"unknown Slack MCP tool: {name}")
        return STUB_TOOLS[name](**kwargs)


def slack_toolset() -> Any:
    """Return the right toolset for the current environment.

    - If `SLACK_BOT_TOKEN` is set, spawn the official Slack MCP server over stdio.
    - Otherwise return the in-process `StubToolset` so the demo works offline.
    """
    if os.environ.get("SLACK_BOT_TOKEN"):
        from google.adk.tools.mcp_tool import McpToolset
        from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
        from mcp import StdioServerParameters

        env = {
            "SLACK_BOT_TOKEN": os.environ["SLACK_BOT_TOKEN"],
        }
        if os.environ.get("SLACK_TEAM_ID"):
            env["SLACK_TEAM_ID"] = os.environ["SLACK_TEAM_ID"]
        return McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="npx",
                    args=["-y", "@modelcontextprotocol/server-slack"],
                    env=env,
                ),
                timeout=30,
            ),
        )
    return StubToolset()
