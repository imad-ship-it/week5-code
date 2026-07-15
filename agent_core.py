"""Shared agent loop (Day 2, Week 5) used by the supervisor and each worker.

Factored out of agent.py's run_agent so the supervisor and workers don't each
duplicate the same tool-calling loop.
"""
import json

MAX_ITERATIONS = 10
MAX_TURNS = 20


def trimmed(messages):
    if len(messages) <= MAX_TURNS + 1:
        return messages
    return [messages[0]] + messages[-MAX_TURNS:]


def run_loop(client, model, system_prompt, tools, execute_tool, user_message):
    """Run one tool-calling agent loop to completion and return its final answer.

    execute_tool(name: str, args: dict) -> str
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    for _ in range(MAX_ITERATIONS):
        response = client.chat.completions.create(
            model=model,
            messages=trimmed(messages),
            tools=tools,
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content

        messages.append(msg)
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            output = execute_tool(call.function.name, args)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": output,
                }
            )

    return "Agent stopped: reached maximum iterations without a final answer."
