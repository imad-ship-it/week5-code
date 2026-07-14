"""Research agent: DeepSeek + web search skill (Day 2) + hooks (Day 4)."""

import os
import json
import time  # ── DAY 4: for timing tool execution
from dotenv import load_dotenv
from openai import OpenAI

from skills.web_search import web_search, WEB_SEARCH_TOOL
from skills.memory import SessionMemory
from hooks import fire  # ── DAY 4: hook system
import plugins.file_reader  # noqa: F401  — importing runs register_plugin()
from plugins import plugin_schemas, get_plugin

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",  # points the OpenAI SDK at DeepSeek
)

MODEL = "deepseek-chat"
MAX_ITERATIONS = 10  # safety guard against infinite loops

SYSTEM_PROMPT = (
    "You are a careful research assistant. Answer the user's question. "
    "If you need current or uncertain information, use the web_search tool. "
    "For multi-part questions, search step by step — one search per fact. "
    "Cite which search result supports your answer when relevant.\n"
    "You have session memory. When the user shares a durable fact (name, "
    "preference, decision) or you learn a key finding, call remember_fact. "
    "When the user refers to something from earlier, call recall_facts "
    "before answering. Never claim to remember something without checking."
    "\nYou can also read .txt and .pdf files from the docs/ folder with read_file. "
    "For complex questions, work step by step in the ReAct style: state a brief "
    "Thought about what you need next, then take one Action (tool call), observe "
    "the result, and repeat until you can give a final answer."
)

memory = SessionMemory()  # one instance per session, created once at startup

MEMORY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "remember_fact",
            "description": "Save an important fact from the conversation (user preferences, names, decisions, key research findings) so it can be recalled later in the session.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The fact, stated as one clear sentence.",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "1-3 keyword tags.",
                    },
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recall_facts",
            "description": "Search previously saved session facts. Use when the user references something from earlier or you need past context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to search for."},
                },
                "required": ["query"],
            },
        },
    },
]

TOOLS = [WEB_SEARCH_TOOL] + MEMORY_TOOLS + plugin_schemas()


def execute_tool(name: str, args: dict) -> str:
    fire("pre_tool", tool_name=name, arguments=args)  # ── DAY 4
    start = time.perf_counter()  # ── DAY 4
    result, error = None, None  # ── DAY 4
    try:  # ── DAY 4
        if name == "web_search":
            result = web_search(**args)
        elif name == "remember_fact":
            result = memory.remember(args["text"], args.get("tags"))
        elif name == "recall_facts":
            result = memory.recall(args["query"])
        else:
            plugin_fn = get_plugin(name)  # ── DAY 5
            if plugin_fn:  # ── DAY 5
                result = plugin_fn(**args)  # ── DAY 5
            else:
                result = f"Unknown tool: {name}"
                error = "unknown_tool"
    except Exception as e:  # ── DAY 4
        result = f"Tool error: {e}"  # ── DAY 4: agent sees error, keeps going
        error = repr(e)  # ── DAY 4
    fire(  # ── DAY 4
        "post_tool",
        tool_name=name,
        arguments=args,
        result=result,
        duration_s=time.perf_counter() - start,
        error=error,
    )
    return result


MAX_TURNS = 20  # keep system prompt + last N messages


def trimmed(messages):
    if len(messages) <= MAX_TURNS + 1:
        return messages
    return [messages[0]] + messages[-MAX_TURNS:]


def run_agent(user_message: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    for iteration in range(MAX_ITERATIONS):
        response = client.chat.completions.create(
            model=MODEL,
            messages=trimmed(messages),
            tools=TOOLS,
        )
        msg = response.choices[0].message

        # Case 1: final answer — done
        if not msg.tool_calls:
            return msg.content

        # Case 2: the model requested tool calls
        # Add the model's turn (with its tool_calls) to history
        messages.append(msg)

        # Execute each requested tool and send results back
        for call in msg.tool_calls:
            args = json.loads(
                call.function.arguments
            )  # arguments arrive as a JSON string
            print(f"[agent] calling tool: {call.function.name}({args})")

            output = execute_tool(call.function.name, args)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": output,
                }
            )

    return "Agent stopped: reached maximum iterations without a final answer."


if __name__ == "__main__":
    print("Research Agent (DeepSeek). Type 'quit' to exit.\n")
    while True:
        question = input("You: ").strip()
        if question.lower() in {"quit", "exit"}:
            break
        answer = run_agent(question)
        print(f"\nAgent: {answer}\n")
