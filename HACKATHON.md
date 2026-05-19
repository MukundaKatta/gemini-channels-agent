# gemini-channels-agent — Hackathon submission

## Elevator pitch (<200 chars)

A Gemini 2.0 Flash agent that summarises Slack channels and incident threads via the official Slack MCP server. Offline stub workspace + Streamlit demo ship in the repo.

## Description (~400 words)

`gemini-channels-agent` is a Gemini-on-Vertex-AI agent that turns a Slack workspace into a question-answering surface tuned for the on-call use case. It is built on Google's Agent Development Kit (ADK) and the Model Context Protocol (MCP), and is wired to the official [Slack MCP server](https://github.com/modelcontextprotocol/servers/tree/main/src/slack) published under Apache-2.0.

The user asks free-form questions — "summarise unread messages in #incidents in the last 24h", "did anyone mention Vertex AI quota?", "summarise the active incident thread" — and Gemini picks among five Slack MCP tools: `list_channels`, `get_channel_history`, `search_messages`, `get_user`, `get_thread_replies`. The system prompt enforces a strict format: a one-line headline, then a bullet list of key turns, each tagged with the speaker's handle. Resolved threads are reported as resolved.

To make the demo runnable end-to-end without a Slack workspace, the repo ships with an in-process `StubToolset` that exposes the exact same five tool names against a fixture workspace: 5 channels (`#general`, `#incidents`, `#eng-platform`, `#dev`, `#random`), ~50 messages across the last 7 days, and one realistic incident thread in `#incidents` (Vertex AI quota exhaustion, acked + mitigated + resolved). The `slack_toolset()` factory inspects `SLACK_BOT_TOKEN`: if set, it spawns `@modelcontextprotocol/server-slack` over stdio; if not, it returns the stub.

The Streamlit dashboard in `app/streamlit_app.py` gives a one-page demo: a channel inspector with a time-window slider, a thread summariser keyed to the fixture incident, and a stub-only answer path for each example question. The ADK web UI is also available via `adk web .` for the live Gemini-driven session.

Deployment is one command: `adk deploy cloud_run --with_ui`. The Dockerfile pre-installs Node 22 and the Slack MCP server so cold starts stay tight.

The novel contribution is the agent itself: the system prompt tuned for on-call summarisation, the channel + thread tool playbook, the offline-runnable stub workspace with the realistic incident thread, the Streamlit dashboard, and the Cloud Run packaging. The MCP server is consumed strictly over its public protocol — no fork, no vendored copy.

## Built with

- google-cloud-aiplatform
- vertex-ai
- gemini-2.0-flash
- google-adk
- model-context-protocol
- slack-mcp-server
- streamlit
- python-3.12
- cloud-run
- docker

## Try it out

- Repo: https://github.com/MukundaKatta/gemini-channels-agent
- Hosted demo: https://channels-agent-PROJECT-uc.a.run.app  *(placeholder — fill after Cloud Run deploy)*
- 3-min demo video: https://www.youtube.com/watch?v=PLACEHOLDER  *(placeholder — fill when recorded)*

## Rule compliance

| Rule | Compliance |
| --- | --- |
| Newly created during contest period | Yes. Git history starts inside the contest window; no forked or vendored code. |
| Uses Google Cloud | Vertex AI (Gemini 2.0 Flash) + Cloud Run (`adk deploy cloud_run`) |
| Uses MCP integration | Official Slack MCP server (Apache-2.0) via stdio; agent has zero hard-coded Slack logic |
| Open source license | Apache 2.0 |
| Includes working demo | `./scripts/run_local_demo.sh` runs offline; ADK web for live Gemini session |
| Smoke tests | `pytest` covers tool surface, channel-history window, thread walk, agent wiring |
