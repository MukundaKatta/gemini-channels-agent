# gemini-channels-agent

A Gemini 2.0 Flash agent on Vertex AI that summarises **Slack** channel activity grounded via the official [Slack MCP server](https://github.com/modelcontextprotocol/servers/tree/main/src/slack). Ships with an in-process stub workspace (5 channels + a realistic incident thread) so the demo runs offline, and a Streamlit dashboard for one-page judging.

## What it does

Ask the agent things like:

- "Summarise unread messages in #incidents in the last 24h."
- "What's happening in #eng-platform this week?"
- "Did anyone mention Vertex AI quota?"
- "Summarise the active incident thread."

The agent picks among the Slack MCP tools (`list_channels`, `get_channel_history`, `search_messages`, `get_user`, `get_thread_replies`). The system prompt enforces a strict format: a one-line headline, then a bullet list of key turns each tagged with the speaker's handle. Resolved threads are reported as resolved — no false alarms.

With no `SLACK_BOT_TOKEN` set the agent reads from an in-process fixture: 5 channels (`#general`, `#incidents`, `#eng-platform`, `#dev`, `#random`), ~50 messages across the last 7 days, and one realistic incident thread in `#incidents` (Vertex AI quota exhaustion, acked + mitigated + resolved). With `SLACK_BOT_TOKEN` set it spawns `@modelcontextprotocol/server-slack` over stdio.

## Tool surface

| Tool | When it fires |
| --- | --- |
| `list_channels` | First call when the channel name is ambiguous |
| `get_channel_history` | "What's happening in #X?" with an optional time window |
| `search_messages` | "Did anyone mention X?" — full-text search, optional channel scope |
| `get_user` | Resolve a user id to a real name for the answer |
| `get_thread_replies` | Walk one thread cleanly (used for the incident-summary path) |

## Architecture

```
+--------------+         +---------------------+
|   Judge      |  chat   |  ADK web UI / SLT   |
|  (browser)   +-------->|  on Cloud Run       |
+--------------+         +----------+----------+
                                    |
                                    | function-calling loop
                                    v
                         +----------+----------+
                         |  Gemini 2.0 Flash   |
                         |  on Vertex AI       |
                         +----------+----------+
                                    |
                              MCP stdio (or in-process stub)
                                    |
                         +----------+----------+
                         |  Slack MCP server   |
                         |  (Apache-2.0)       |
                         +----------+----------+
                                    |
                              Slack Web API
                                    v
                         +----------+----------+
                         |  Slack workspace    |
                         +---------------------+
```

## Try it locally

Requires Python 3.11+ and (for the real-tenant path) Node 22+ and a Slack bot token with `channels:history`, `channels:read`, `users:read`, and `search:read` scopes.

```bash
pip install -e .

# Offline demo (no Slack token needed):
./scripts/run_local_demo.sh

# Real-tenant mode:
export SLACK_BOT_TOKEN='xoxb-xxxxxxxxxx'
export SLACK_TEAM_ID='T0XXXXXXX'           # optional
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT=<your-project>
export GOOGLE_CLOUD_LOCATION=us-central1
adk web .
```

The Streamlit dashboard at `app/streamlit_app.py` includes a channel inspector with a time-window slider and a stub-only answer path for the four example questions above (including the incident-thread summary).

## Deploy to Cloud Run

```bash
adk deploy cloud_run --project="$GOOGLE_CLOUD_PROJECT" \
  --region=us-central1 --service_name=channels-agent \
  --with_ui --allow_origins='*' .
```

Required env vars:

- `GOOGLE_GENAI_USE_VERTEXAI=TRUE`
- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION`
- `SLACK_BOT_TOKEN` (only for the real-tenant path)
- `SLACK_TEAM_ID` (optional)

## Tests

```bash
pip install -e ".[dev]"
pytest
```

The smoke tests in `tests/test_agent.py` cover the tool surface, the channel-history window, the thread walk, and the agent wiring — all without a real Slack token or Vertex AI credentials.

## Why this isn't an extension of pre-existing work

This project was newly created during the contest period. Every Python file in `agent/` and `app/` was written from scratch within the contest window, and the git history starts inside that window. The official `@modelcontextprotocol/server-slack` (Apache-2.0) is consumed strictly through the public MCP protocol — no fork, no vendored copy. The novel contribution is the agent: its system prompt, the channel + thread tool playbook, the offline-runnable stub workspace (including a realistic incident thread), and the Streamlit dashboard.

## License

Apache 2.0
