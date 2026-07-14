"""File-read plugin: lets the agent read .txt and .pdf files from docs/."""

from pathlib import Path
from pypdf import PdfReader
from plugins import register_plugin

DOCS_DIR = Path("docs")  # sandbox: agent may only read inside this folder
MAX_CHARS = 8000  # keep context manageable


def read_file(path: str) -> str:
    """Read a .txt or .pdf file and return its text content."""
    target = (DOCS_DIR / path).resolve()

    # Security: block path traversal (e.g. "../../.env")
    if not target.is_relative_to(DOCS_DIR.resolve()):
        return "Error: access denied — only files inside docs/ can be read."
    if not target.exists():
        available = [p.name for p in DOCS_DIR.glob("*") if p.is_file()]
        return f"Error: '{path}' not found. Available files: {available}"

    suffix = target.suffix.lower()
    if suffix == ".txt":
        text = target.read_text(encoding="utf-8", errors="replace")
    elif suffix == ".pdf":
        reader = PdfReader(target)
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n\n".join(pages)
    else:
        return f"Error: unsupported file type '{suffix}'. Only .txt and .pdf."

    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + f"\n\n[Truncated at {MAX_CHARS} chars]"
    return text or "The file appears to be empty (or the PDF has no extractable text)."


FILE_READER_TOOL = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read the text content of a .txt or .pdf file from the docs/ folder. Pass just the filename, e.g. 'notes.txt'.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Filename inside docs/, e.g. 'notes.txt' or 'report.pdf'.",
                },
            },
            "required": ["path"],
        },
    },
}

register_plugin(FILE_READER_TOOL, read_file)
