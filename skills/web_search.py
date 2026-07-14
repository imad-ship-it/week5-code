"""Web search skill using DuckDuckGo (keyless, via the ddgs library)."""
from ddgs import DDGS


def web_search(query: str, num_results: int = 5) -> str:
    """Run a web search and return results as formatted text."""
    try:
        results = list(DDGS().text(query, max_results=num_results))
    except Exception as e:
        return f"ERROR: search request failed: {e}"

    if not results:
        return "No results found."

    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "No title")
        snippet = r.get("body", "")
        url = r.get("href", "")
        lines.append(f"{i}. {title}\n   {snippet}\n   Source: {url}")
    return "\n\n".join(lines)


# Tool definition the model sees (OpenAI/DeepSeek format)
WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for current, factual information. Use this when the "
            "question involves recent events, specific facts you are not fully "
            "certain about, or anything that may have changed over time (people's "
            "roles, prices, dates, statistics). Returns the top results as titles, "
            "snippets, and source URLs. Do not use it for math, reasoning, or "
            "questions you can already answer reliably."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "A short, specific search query, e.g. "
                        "'current CEO of OpenAI' or 'population of Buenos Aires 2025'."
                    ),
                }
            },
            "required": ["query"],
        },
    },
}