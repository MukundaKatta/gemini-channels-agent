#!/usr/bin/env bash
# Start the local demo: stub MCP via in-process StubToolset + Streamlit dashboard.
# No SLACK_BOT_TOKEN required. To run against a real Slack workspace, export
# SLACK_BOT_TOKEN (and optionally SLACK_TEAM_ID) before invoking this script
# and the agent will spawn @modelcontextprotocol/server-slack instead of the stub.
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -z "${SLACK_BOT_TOKEN:-}" ]]; then
  echo "[channels-agent] SLACK_BOT_TOKEN not set — using in-process stub workspace."
else
  echo "[channels-agent] SLACK_BOT_TOKEN detected — will spawn @modelcontextprotocol/server-slack."
fi

python -m pip install -e . >/dev/null

exec streamlit run app/streamlit_app.py --server.port "${PORT:-8501}"
