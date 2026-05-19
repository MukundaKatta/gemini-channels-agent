"""Import-time smoke tests for the Slack channels agent.

These run without real Slack credentials, without Vertex AI credentials, and
without spawning the `npx @modelcontextprotocol/server-slack` subprocess. The
`slack_toolset()` factory falls back to the in-process `StubToolset` so
`_build_root_agent()` produces a fully wired `Agent` object.
"""

from __future__ import annotations

import sys


def _reset_agent_module() -> None:
    for mod in ("agent", "agent.agent", "agent.tools"):
        sys.modules.pop(mod, None)


def test_import_does_not_require_real_credentials(monkeypatch):
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    monkeypatch.delenv("SLACK_TEAM_ID", raising=False)
    _reset_agent_module()

    import agent  # noqa: F401

    assert "root_agent" not in vars(agent)


def test_stub_toolset_matches_documented_surface(monkeypatch):
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    _reset_agent_module()

    from agent.tools import StubToolset, slack_toolset

    toolset = slack_toolset()
    assert isinstance(toolset, StubToolset)
    names = {fn.__name__ for fn in toolset.tools}
    assert names == {
        "list_channels",
        "get_channel_history",
        "search_messages",
        "get_user",
        "get_thread_replies",
    }


def test_channel_history_window_and_thread_walk(monkeypatch):
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    _reset_agent_module()

    from agent.tools import (
        INCIDENT_THREAD,
        get_channel_history,
        get_thread_replies,
    )

    # The incident thread is within the last 24h.
    rows = get_channel_history(channel="incidents", hours=24)["messages"]
    assert len(rows) >= len(INCIDENT_THREAD)
    parent_ts = INCIDENT_THREAD[0]["ts"]

    thread = get_thread_replies(channel="incidents", thread_ts=parent_ts)["messages"]
    assert len(thread) == len(INCIDENT_THREAD)
    # Chronological order.
    ts_vals = [float(m["ts"]) for m in thread]
    assert ts_vals == sorted(ts_vals)


def test_search_messages_finds_quota_mention(monkeypatch):
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    _reset_agent_module()

    from agent.tools import search_messages

    hits = search_messages(query="quota")["matches"]
    assert hits, "expected at least one quota mention in the incident thread"
    assert any("quota" in m["text"].lower() for m in hits)


def test_root_agent_shape_with_stub(monkeypatch):
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    _reset_agent_module()

    import agent.agent as agent_mod
    from agent.tools import StubToolset
    from google.adk.agents import Agent

    root = agent_mod.root_agent
    assert isinstance(root, Agent)
    assert root.name == "slack_channels_agent"
    assert len(root.tools) == 1
    assert isinstance(root.tools[0], StubToolset)
    assert "Slack" in root.instruction
    assert "get_thread_replies" in root.instruction
