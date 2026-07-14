# skills/memory.py
import time


class SessionMemory:
    def __init__(self):
        self.facts = []  # each: {"text": str, "tags": list[str], "ts": float}

    def remember(self, text: str, tags: list[str] | None = None) -> str:
        self.facts.append(
            {
                "text": text.strip(),
                "tags": [t.lower() for t in (tags or [])],
                "ts": time.time(),
            }
        )
        return f"Saved fact #{len(self.facts)}: {text.strip()}"

    def recall(self, query: str, top_k: int = 3) -> str:
        if not self.facts:
            return "No facts stored yet."
        q_words = set(query.lower().split())
        scored = []
        for f in self.facts:
            f_words = set(f["text"].lower().split()) | set(f["tags"])
            score = len(q_words & f_words)
            scored.append((score, f))
        scored.sort(key=lambda x: (-x[0], -x[1]["ts"]))
        hits = [f for s, f in scored[:top_k] if s > 0]
        if not hits:
            # fall back to most recent facts so the model isn't left empty-handed
            hits = [f for _, f in scored[:top_k]]
        return "\n".join(f"- {f['text']}" for f in hits)

    def dump(self) -> str:
        return (
            "\n".join(f"{i + 1}. {f['text']}" for i, f in enumerate(self.facts))
            or "(empty)"
        )
