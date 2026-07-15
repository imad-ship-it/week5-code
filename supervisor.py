"""Supervisor (Day 2, Week 5): routes tasks to specialist workers.

The supervisor never searches the web or reads files itself — it only
delegates. This is the top of the agent graph; run this file directly.
"""
import os
import time
from dotenv import load_dotenv
from openai import OpenAI

from agent_core import run_loop
from worker_researcher import run_researcher
from worker_notes import run_notes_worker
from hooks import fire

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
MODEL = "deepseek-chat"

AGENT_NAME = "supervisor"

SYSTEM_PROMPT = (
    "You are a supervisor that coordinates two specialists: a researcher "
    "(web search + memory of facts) and a notes_worker (reads local files in "
    "docs/). You do not do the work yourself — break the user's request into "
    "sub-tasks and delegate each to the right specialist via call_researcher "
    "or call_notes_worker. For multi-part questions, call both, then combine "
    "their results into one final answer for the user."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "call_researcher",
            "description": "Delegate a fact-finding task to the researcher specialist (web search, remembering/recalling facts).",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "The specific research task to hand off."},
                },
                "required": ["task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "call_notes_worker",
            "description": "Delegate a task to the notes specialist to read/summarize a file from the docs/ folder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "The specific notes/file task to hand off."},
                },
                "required": ["task"],
            },
        },
    },
]


def _execute_tool(name: str, args: dict) -> str:
    fire("pre_tool", tool_name=name, arguments=args, agent=AGENT_NAME)
    start = time.perf_counter()
    result, error = None, None
    try:
        if name == "call_researcher":
            result = run_researcher(args["task"])
        elif name == "call_notes_worker":
            result = run_notes_worker(args["task"])
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


def run_supervisor(user_message: str) -> str:
    return run_loop(client, MODEL, SYSTEM_PROMPT, TOOLS, _execute_tool, user_message)


if __name__ == "__main__":
    print("Supervisor (researcher + notes_worker). Type 'quit' to exit.\n")
    while True:
        question = input("You: ").strip()
        if question.lower() in {"quit", "exit"}:
            break
        answer = run_supervisor(question)
        print(f"\nSupervisor: {answer}\n")
