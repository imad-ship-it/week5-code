"""Researcher worker (Day 2, Week 5): a narrow agent scoped to web search + memory.

Called by the supervisor via call_researcher(task). Has no knowledge of the
notes worker or the supervisor itself — it only sees its own task string.
"""
import os
import time
from dotenv import load_dotenv
from openai import OpenAI

from agent_core import run_loop
from skills.web_search import web_search, WEB_SEARCH_TOOL
from skills.memory import SessionMemory
from hooks import fire

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
MODEL = "deepseek-chat"

AGENT_NAME = "researcher"

SYSTEM_PROMPT = (
    "You are a research specialist. You only handle fact-finding: searching "
    "the web and recalling/remembering facts. You do not read local files — "
    "that is another specialist's job. Answer the task you are given directly "
    "and concisely; you are not talking to the end user, you are reporting "
    "back to a supervisor agent."
)

memory = SessionMemory()

MEMORY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "remember_fact",
            "description": "Save an important fact learned during research so it can be recalled later.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The fact, as one clear sentence."},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "1-3 keyword tags."},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recall_facts",
            "description": "Search previously saved research facts.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "What to search for."}},
                "required": ["query"],
            },
        },
    },
]

TOOLS = [WEB_SEARCH_TOOL] + MEMORY_TOOLS


def _execute_tool(name: str, args: dict) -> str:
    fire("pre_tool", tool_name=name, arguments=args, agent=AGENT_NAME)
    start = time.perf_counter()
    result, error = None, None
    try:
        if name == "web_search":
            result = web_search(**args)
        elif name == "remember_fact":
            result = memory.remember(args["text"], args.get("tags"))
        elif name == "recall_facts":
            result = memory.recall(args["query"])
        else:
            result = f"Unknown tool: {name}"
            error = "unknown_tool"
    except Exception as e:
        result = f"Tool error: {e}"
        error = repr(e)
    fire(
        "post_tool",
        tool_name=name,
        arguments=args,
        result=result,
        duration_s=time.perf_counter() - start,
        error=error,
        agent=AGENT_NAME,
    )
    return result


def run_researcher(task: str) -> str:
    return run_loop(client, MODEL, SYSTEM_PROMPT, TOOLS, _execute_tool, task)


if __name__ == "__main__":
    print("Researcher worker (standalone test). Type 'quit' to exit.\n")
    while True:
        task = input("Task: ").strip()
        if task.lower() in {"quit", "exit"}:
            break
        print(f"\nResult: {run_researcher(task)}\n")
