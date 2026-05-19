# Cloud Run image: needs Python (for ADK) AND Node (so `npx @modelcontextprotocol/server-slack` works).
FROM python:3.12-slim

# Install Node 22 — needed when the agent spawns the Slack MCP server.
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Pre-cache the MCP server so we don't pay npx-fetch latency on first request.
RUN npm install -g @modelcontextprotocol/server-slack

WORKDIR /app
COPY pyproject.toml ./
COPY agent ./agent
COPY app ./app
RUN pip install --no-cache-dir .

ENV PORT=8080
EXPOSE 8080

CMD ["adk", "web", "--host=0.0.0.0", "--port=8080", "."]
