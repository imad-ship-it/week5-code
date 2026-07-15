## Week 5, Day 1 — MCP server (tool + resource)
- Built mcp_server.py with FastMCP, exposing the existing web_search skill
  as a tool (search_web) and docs/notes.txt as a resource (docs://notes).
  Reused the Week 4 function directly instead of rewriting it — FastMCP
  auto-generates the tool schema from type hints, so no manual JSON schema
  was needed like the OpenAI-style WEB_SEARCH_TOOL dict.
- Correction: first put .mcp.json inside week5-code/, but Claude Code only
  auto-loads .mcp.json from the session's root working directory
  (d:\iccode), not a nested subfolder — moved/copied it to the root for
  this to be detected.
- New project-scoped MCP servers require explicit user approval
  (`claude mcp list` showed "Pending approval") — had to reload the
  editor window to get the approval prompt, then approve, then verify
  with a live search_web call.
- Verified end-to-end: Claude Code (client) -> stdio -> mcp_server.py
  (server) -> web_search() -> DDGS API, returning real results.

## Week 5, Day 2 — Supervisor + worker agents, cross-agent tracing
- Split the single Week 4 agent into three: worker_researcher.py (web
  search + memory only), worker_notes.py (read_file only), and
  supervisor.py, which has no tools of its own except call_researcher and
  call_notes_worker and must delegate rather than act directly.
- Extracted agent_core.py (shared run_loop) instead of copy-pasting the
  tool-calling while-loop three times across agent.py-style files.
- Extended hooks.py's log_pre_tool/log_post_tool with an `agent` field
  (default "agent" for backward compat with the original agent.py calls)
  so tool_calls.log now shows which agent — supervisor, researcher, or
  notes_worker — made each call, not just which tool.
- Correction: pypdf was never listed in requirements.txt (only installed
  ad-hoc in the original week4-agent venv), so importing worker_notes.py
  failed on a fresh install. Added pypdf and mcp[cli] to requirements.txt.
- Verified live with a multi-hop question ("read notes.txt to find which
  company, then search the web for its latest funding, summarize under
  100 words") — supervisor correctly called notes_worker first, then
  researcher, then combined both into one answer respecting the
  preference found in the notes. Confirmed the full hand-off chain in
  tool_calls.log via the agent field.

## Day 2 — Web search skill
- Provider: DeepSeek (deepseek-chat), OpenAI-compatible API.
- Tool: web_search(query) via DuckDuckGo (ddgs) — keyless, chosen
  because Brave now requires a credit card. Skills are swappable, so
  the model doesn't know which engine runs behind the function.
- Description design: states WHEN to use (recent/uncertain facts) and
  when NOT to (math, known facts). Without the negative clause, the
  model searched even for "2+2".
- System prompt tells the agent to search step-by-step for multi-part
  questions — this made multi-hop chaining reliable.
- Errors are returned as strings so the agent can see and recover.
- Note: DuckDuckGo can rate-limit under heavy testing; pause between runs.