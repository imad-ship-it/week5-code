"""MCP server exposing the research agent's web-search tool and docs/ resource.

Day 1 (Week 5): wraps the Week 4 web_search skill as an MCP tool, and the
docs/ folder as an MCP resource, so any MCP client (Claude Code, Cursor,
a custom client) can use them without knowing about the agent's internals.
"""
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from skills.web_search import web_search

mcp = FastMCP("week5-research-server")

DOCS_DIR = Path(__file__).parent / "docs"


@mcp.tool()
def search_web(query: str, num_results: int = 5) -> str:
    """Search the web for current, factual information and return titles,
    snippets, and source URLs."""
    return web_search(query, num_results)


@mcp.resource("docs://notes")
def get_notes() -> str:
    """Contents of docs/notes.txt."""
    return (DOCS_DIR / "notes.txt").read_text(encoding="utf-8")


if __name__ == "__main__":
    mcp.run()
