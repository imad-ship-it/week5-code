"""Notes worker (Day 2, Week 5): a narrow agent scoped to reading local files.

Called by the supervisor via call_notes_worker(task). Only knows how to read
from docs/ — no web access, no memory of its own.
"""
import os
import time
from dotenv import load_dotenv
from openai import OpenAI

from agent_core import run_loop
from plugins.file_reader import read_file, FILE_READER_TOOL
from hooks import fire

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
MODEL = "deepseek-chat"

AGENT_NAME = "notes_worker"

SYSTEM_PROMPT = (
    "You are a notes specialist. You only read and summarize files from the "
    "docs/ folder using read_file. You do not search the web — that is "
    "another specialist's job. Answer the task you are given directly and "
    "concisely; you are reporting back to a supervisor agent, not the end user."
)

TOOLS = [FILE_READER_TOOL]


def _execute_tool(name: str, args: dict) -> str:
    fire("pre_tool", tool_name=name, arguments=args, agent=AGENT_NAME)
    start = time.perf_counter()
    result, error = None, None
    try:
        if name == "read_file":
            result = read_file(**args)
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


def run_notes_worker(task: str) -> str:
    return run_loop(client, MODEL, SYSTEM_PROMPT, TOOLS, _execute_tool, task)


if __name__ == "__main__":
    print("Notes worker (standalone test). Type 'quit' to exit.\n")
    while True:
        task = input("Task: ").strip()
        if task.lower() in {"quit", "exit"}:
            break
        print(f"\nResult: {run_notes_worker(task)}\n")
