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