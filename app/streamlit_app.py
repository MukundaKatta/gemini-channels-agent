"""Streamlit dashboard for the Slack channels agent.

One-page demo: channel inspector, thread summariser, and a stub-only
"summarise #incidents in the last 24h" answer path. Real-tenant mode is
auto-detected via `SLACK_BOT_TOKEN`.
"""

from __future__ import annotations

import os

import streamlit as st

from agent.tools import (
    CHANNELS,
    INCIDENT_THREAD,
    MESSAGES,
    STUB_TOOLS,
    USERS,
    WORKSPACE,
    get_channel_history,
    get_thread_replies,
    get_user,
    search_messages,
)


st.set_page_config(page_title="Slack channels agent", page_icon="S", layout="wide")
st.title("Slack channels agent")
st.caption(
    "Gemini 2.0 Flash + Slack MCP. Ask for channel summaries, search, and thread digests."
)

mode = "real-tenant" if os.environ.get("SLACK_BOT_TOKEN") else "stub workspace"
st.sidebar.markdown(f"**Mode:** `{mode}`")
st.sidebar.markdown("**Tool surface:**")
for name in STUB_TOOLS:
    st.sidebar.markdown(f"- `{name}`")

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Workspace:** `{WORKSPACE['name']}`")
st.sidebar.markdown(f"- Channels: {len(CHANNELS)}")
st.sidebar.markdown(f"- Messages: {len(MESSAGES)}")
st.sidebar.markdown(f"- Users: {len(USERS)}")

col_q, col_c = st.columns([1, 1])

with col_q:
    st.subheader("Ask the workspace")
    examples = [
        "Summarise unread messages in #incidents in the last 24h.",
        "What's happening in #eng-platform this week?",
        "Did anyone mention Vertex AI quota?",
        "Summarise the active incident thread.",
    ]
    question = st.text_area("Question", value=examples[0], height=80)
    st.caption("Try one of these:")
    for ex in examples:
        if st.button(ex, key=f"ex_{ex}"):
            question = ex

with col_c:
    st.subheader("Channel inspector")
    ch = st.selectbox(
        "Channel",
        options=[c["id"] for c in CHANNELS],
        format_func=lambda i: "#" + next(c["name"] for c in CHANNELS if c["id"] == i),
        index=1,  # incidents
    )
    window = st.slider("Window (hours)", 1, 168, 24)
    hist = get_channel_history(channel=ch, hours=window)["messages"]
    st.write(f"**{len(hist)} messages in the last {window}h**")
    for m in hist[-12:]:
        u = get_user(m["user"]).get("name", m["user"])
        st.markdown(f"- `@{u}`: {m['text']}")

st.markdown("---")
st.subheader("Agent (stub)")
st.info(
    "Streamlit is exercising the MCP tool surface against the stub workspace. "
    "For a live Gemini-driven session, run `adk web .` with "
    "`GOOGLE_GENAI_USE_VERTEXAI=TRUE` and your Google Cloud project / location set."
)

if question.strip():
    q = question.lower()
    if "incident" in q and ("summar" in q or "24" in q or "thread" in q):
        # Use thread replies for the parent incident ts so the summary stays tight.
        parent_ts = INCIDENT_THREAD[0]["ts"]
        replies = get_thread_replies(channel="C_INC", thread_ts=parent_ts)["messages"]
        st.success(
            "Incident: Vertex AI quota exhaustion on gemini-2.0-flash, resolved."
        )
        for m in replies:
            u = get_user(m["user"]).get("name", m["user"])
            st.markdown(f"- `@{u}`: {m['text']}")
    elif "eng-platform" in q or "platform" in q:
        rows = get_channel_history(channel="eng-platform", hours=168)["messages"]
        st.success(f"{len(rows)} messages in #eng-platform this week:")
        for m in rows[-10:]:
            u = get_user(m["user"]).get("name", m["user"])
            st.markdown(f"- `@{u}`: {m['text']}")
    elif "vertex" in q or "quota" in q:
        hits = search_messages(query="vertex")["matches"] + search_messages(
            query="quota"
        )["matches"]
        seen = set()
        dedup = []
        for m in hits:
            if m["ts"] in seen:
                continue
            seen.add(m["ts"])
            dedup.append(m)
        st.success(f"{len(dedup)} messages mention Vertex AI quota:")
        for m in dedup:
            u = get_user(m["user"]).get("name", m["user"])
            ch_name = next(c["name"] for c in CHANNELS if c["id"] == m["channel"])
            st.markdown(f"- `#{ch_name}` `@{u}`: {m['text']}")
    else:
        hits = search_messages(query=question)["matches"]
        if not hits:
            st.warning("No matches. Try one of the example questions.")
        else:
            st.success(f"{len(hits)} hits:")
            for m in hits[:10]:
                u = get_user(m["user"]).get("name", m["user"])
                ch_name = next(c["name"] for c in CHANNELS if c["id"] == m["channel"])
                st.markdown(f"- `#{ch_name}` `@{u}`: {m['text']}")
