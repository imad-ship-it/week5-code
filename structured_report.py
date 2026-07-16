"""Structured outputs (Day 3, Week 5): schema guards + retry as agent guardrails.

Wraps the supervisor's free-text answer into a validated JSON report. The
schema is the contract; Pydantic validation is the guard; on failure the
model sees its own error and retries; after MAX_RETRIES we fall back safely
instead of crashing.
"""
import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

from supervisor import run_supervisor

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
MODEL = "deepseek-chat"
MAX_RETRIES = 2


class FinalReport(BaseModel):
    """The contract: every supervisor answer must fit this shape."""

    answer: str = Field(description="The final answer for the user, under 120 words.")
    workers_used: list[str] = Field(
        description="Which specialists contributed: 'researcher', 'notes_worker', or both."
    )
    key_facts: list[str] = Field(
        min_length=1, description="1-5 short facts the answer is based on."
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="How confident the answer is, 0.0 to 1.0."
    )


FORMAT_PROMPT = (
    "Convert the following agent answer into JSON matching this schema exactly. "
    "Return ONLY the JSON object, no markdown fences, no commentary.\n"
    f"Schema: {FinalReport.model_json_schema()}\n"
)


def structure_answer(question: str, raw_answer: str) -> FinalReport:
    """Guard + retry loop: validate model JSON against FinalReport."""
    messages = [
        {"role": "system", "content": FORMAT_PROMPT},
        {"role": "user", "content": f"Question: {question}\n\nAgent answer:\n{raw_answer}"},
    ]

    for attempt in range(1 + MAX_RETRIES):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            response_format={"type": "json_object"},  # DeepSeek JSON mode
        )
        raw_json = response.choices[0].message.content
        try:
            return FinalReport.model_validate_json(raw_json)  # the guard
        except ValidationError as e:
            print(f"[guard] attempt {attempt + 1} failed validation: {e.error_count()} error(s)")
            # feed the model its own mistake and retry
            messages.append({"role": "assistant", "content": raw_json})
            messages.append(
                {
                    "role": "user",
                    "content": f"That JSON failed validation:\n{e}\nFix it and return only valid JSON.",
                }
            )

    # fallback: never crash downstream code
    return FinalReport(
        answer=raw_answer[:500],
        workers_used=["unknown"],
        key_facts=["Structured formatting failed; raw answer preserved."],
        confidence=0.0,
    )


def run_structured(question: str) -> FinalReport:
    raw = run_supervisor(question)
    return structure_answer(question, raw)


if __name__ == "__main__":
    q = input("Question: ").strip()
    report = run_structured(q)
    print("\n=== VALIDATED REPORT ===")
    print(report.model_dump_json(indent=2))