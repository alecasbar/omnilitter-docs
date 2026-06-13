#!/usr/bin/env python
"""Small dependency-free MCP server for humanizing draft text."""

from __future__ import annotations

import json
import re
import sys
from typing import Any


try:
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


SPANISH_REPLACEMENTS = (
    ("En conclusion,", "En conjunto,"),
    ("En conclusión,", "En conjunto,"),
    ("Por consiguiente,", "Por eso,"),
    ("Asimismo,", "Además,"),
    ("Adicionalmente,", "Además,"),
    ("Cabe destacar que", "Conviene destacar que"),
    ("Es importante mencionar que", "Hay que tener en cuenta que"),
    ("Resulta fundamental", "Es fundamental"),
    ("se puede observar que", "se observa que"),
    ("se pretende llevar a cabo", "se busca realizar"),
    ("con el objetivo de", "para"),
    ("a fin de", "para"),
    ("debido a que", "porque"),
    ("no obstante,", "aun así,"),
    ("por lo tanto,", "por tanto,"),
)

ENGLISH_REPLACEMENTS = (
    ("In conclusion,", "Overall,"),
    ("Furthermore,", "Also,"),
    ("Additionally,", "Also,"),
    ("It is important to note that", "It is worth noting that"),
    ("It should be noted that", "Notably,"),
    ("in order to", "to"),
    ("due to the fact that", "because"),
    ("utilize", "use"),
    ("prior to", "before"),
    ("subsequent to", "after"),
    ("therefore,", "so,"),
    ("however,", "still,"),
)

LATEX_PATTERNS = (
    re.compile(r"\$[^$\n]*\$"),
    re.compile(r"\\[A-Za-z]+(?:\[[^\]\n]*\])?(?:\{[^{}\n]*\})?"),
)


def _protect_latex(text: str) -> tuple[str, dict[str, str]]:
    placeholders: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        token = f"@@LATEX_{len(placeholders)}@@"
        placeholders[token] = match.group(0)
        return token

    protected = text
    for pattern in LATEX_PATTERNS:
        protected = pattern.sub(replace, protected)
    return protected, placeholders


def _restore_latex(text: str, placeholders: dict[str, str]) -> str:
    for token, value in placeholders.items():
        text = text.replace(token, value)
    return text


def _detect_language(text: str, requested: str) -> str:
    if requested in {"es", "en"}:
        return requested
    spanish_markers = (" el ", " la ", " de ", " que ", " para ", " con ", " requisitos ")
    score = sum(1 for marker in spanish_markers if marker in f" {text.lower()} ")
    return "es" if score >= 2 else "en"


def _apply_replacements(text: str, language: str) -> str:
    replacements = SPANISH_REPLACEMENTS if language == "es" else ENGLISH_REPLACEMENTS
    for old, new in replacements:
        text = re.sub(re.escape(old), new, text, flags=re.IGNORECASE)
    return text


def _soften_pacing(text: str, intensity: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    text = re.sub(r"([.!?])\s+", r"\1 ", text)
    if intensity in {"medium", "strong"}:
        text = re.sub(r";\s+", ". ", text)
        text = re.sub(r",\s+(por tanto|so),\s+", r". \1, ", text, flags=re.IGNORECASE)
    if intensity == "strong":
        text = re.sub(r"\b(claramente|obviamente|clearly|obviously)\b,?\s*", "", text, flags=re.IGNORECASE)
    return text.strip()


def humanize_text(
    text: str,
    language: str = "auto",
    intensity: str = "medium",
    preserve_latex: bool = True,
) -> str:
    if not text or not text.strip():
        return ""

    placeholders: dict[str, str] = {}
    working = text
    if preserve_latex:
        working, placeholders = _protect_latex(working)

    detected_language = _detect_language(working, language)
    working = _apply_replacements(working, detected_language)
    working = _soften_pacing(working, intensity)

    if preserve_latex:
        working = _restore_latex(working, placeholders)
    return working


def _ok(message_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def _error(message_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}


def handle(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    message_id = message.get("id")
    params = message.get("params") or {}

    if message_id is None:
        return None

    if method == "initialize":
        return _ok(
            message_id,
            {
                "protocolVersion": params.get("protocolVersion", "2025-06-18"),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "humanizer", "version": "0.1.0"},
            },
        )

    if method == "ping":
        return _ok(message_id, {})

    if method in {"resources/list", "prompts/list"}:
        key = "resources" if method.startswith("resources") else "prompts"
        return _ok(message_id, {key: []})

    if method == "tools/list":
        return _ok(
            message_id,
            {
                "tools": [
                    {
                        "name": "humanize_text",
                        "description": "Rewrite draft text so it sounds more natural while preserving meaning and optional LaTeX fragments.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string", "description": "Text to humanize."},
                                "language": {
                                    "type": "string",
                                    "enum": ["auto", "es", "en"],
                                    "default": "auto",
                                },
                                "intensity": {
                                    "type": "string",
                                    "enum": ["light", "medium", "strong"],
                                    "default": "medium",
                                },
                                "preserve_latex": {"type": "boolean", "default": True},
                            },
                            "required": ["text"],
                        },
                    }
                ]
            },
        )

    if method == "tools/call":
        if params.get("name") != "humanize_text":
            return _error(message_id, -32601, "Unknown tool")
        arguments = params.get("arguments") or {}
        try:
            result = humanize_text(
                text=str(arguments.get("text", "")),
                language=str(arguments.get("language", "auto")),
                intensity=str(arguments.get("intensity", "medium")),
                preserve_latex=bool(arguments.get("preserve_latex", True)),
            )
        except Exception as exc:  # pragma: no cover - defensive for MCP clients
            return _ok(message_id, {"content": [{"type": "text", "text": str(exc)}], "isError": True})
        return _ok(message_id, {"content": [{"type": "text", "text": result}], "isError": False})

    return _error(message_id, -32601, f"Unsupported method: {method}")


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
            response = handle(message)
        except json.JSONDecodeError as exc:
            response = _error(None, -32700, f"Parse error: {exc}")
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
