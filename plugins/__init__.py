"""Plugin registry: plugins self-register a (schema, function) pair."""

_REGISTRY = {}  # name -> {"schema": ..., "fn": ...}


def register_plugin(schema: dict, fn) -> None:
    name = schema["function"]["name"]
    _REGISTRY[name] = {"schema": schema, "fn": fn}


def plugin_schemas() -> list:
    return [p["schema"] for p in _REGISTRY.values()]


def get_plugin(name: str):
    entry = _REGISTRY.get(name)
    return entry["fn"] if entry else None
