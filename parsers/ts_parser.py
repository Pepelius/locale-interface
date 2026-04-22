from __future__ import annotations

import json
import re
from pathlib import Path

from .base import BaseParser, flatten, unflatten


# ---------------------------------------------------------------------------
# TypeScriptParser
# ---------------------------------------------------------------------------

class TypeScriptParser(BaseParser):
    """Parse TypeScript / JavaScript i18n object files.

    Handles common patterns:
      export default { key: "value" }
      export const NAME = { key: "value" }
      module.exports = { key: "value" }
      const NAME = { key: "value" }

    Single-quote and unquoted keys are supported on load.
    On save the wrapper is preserved and only the object body is replaced.
    """

    def load(self, path: Path) -> dict[str, str]:
        text = path.read_text(encoding="utf-8")
        raw = _parse_js_object(text)
        return flatten(raw)

    def save(self, path: Path, data: dict[str, str]) -> None:
        original = path.read_text(encoding="utf-8")
        nested = unflatten(data)
        obj_js = _dict_to_js(nested, indent=2, level=0)
        new_text = _splice_object(original, obj_js)
        path.write_text(new_text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINE_COMMENT = re.compile(r"//[^\n]*")

# Patterns that introduce the top-level object (ordered by specificity)
_WRAPPER_PATTERNS = [
    r"export\s+default\s*\{",
    r"export\s+const\s+\w[\w$]*\s*=\s*\{",
    r"module\.exports\s*=\s*\{",
    r"const\s+\w[\w$]*\s*=\s*\{",
    r"var\s+\w[\w$]*\s*=\s*\{",
    r"let\s+\w[\w$]*\s*=\s*\{",
]


def _strip_comments(text: str) -> str:
    text = _BLOCK_COMMENT.sub(" ", text)
    text = _LINE_COMMENT.sub("", text)
    return text


def _find_object_start(text: str) -> int:
    """Return the index of the opening '{' for the main export object."""
    for pat in _WRAPPER_PATTERNS:
        m = re.search(pat, text)
        if m:
            # The '{' is the last character of the match
            return m.end() - 1
    # Fallback: first '{' in the file
    idx = text.find("{")
    return idx if idx >= 0 else 0


def _extract_balanced(text: str, start: int) -> str:
    """Return the balanced {...} block beginning at *start*."""
    depth = 0
    in_str = False
    str_char = ""
    i = start
    while i < len(text):
        c = text[i]
        if in_str:
            if c == "\\" and i + 1 < len(text):
                i += 2
                continue
            if c == str_char:
                in_str = False
        else:
            if c in ('"', "'", "`"):
                in_str = True
                str_char = c
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        i += 1
    return text[start:]


def _js_to_json(js: str) -> str:
    """Best-effort conversion of a JS/TS object literal to valid JSON.

    Steps:
      1. Normalise strings: single-quoted → double-quoted, template literals → string.
      2. Quote bare identifier keys.
      3. Strip trailing commas.
    """
    # ── Pass 1: normalise strings ──────────────────────────────────────────
    out: list[str] = []
    i = 0
    n = len(js)

    while i < n:
        c = js[i]

        if c == '"':
            # Copy double-quoted string verbatim (handle escapes)
            out.append(c)
            i += 1
            while i < n:
                c2 = js[i]
                out.append(c2)
                if c2 == "\\":
                    i += 1
                    if i < n:
                        out.append(js[i])
                elif c2 == '"':
                    break
                i += 1
            i += 1

        elif c == "'":
            # Convert single-quoted → double-quoted
            out.append('"')
            i += 1
            while i < n:
                c2 = js[i]
                if c2 == "\\" and i + 1 < n:
                    nc = js[i + 1]
                    if nc == "'":
                        out.append("'")   # \' → ' (unescape)
                    elif nc == '"':
                        out.append('\\"') # " inside str must be escaped
                    else:
                        out.append("\\")
                        out.append(nc)
                    i += 2
                elif c2 == "'":
                    i += 1
                    break
                elif c2 == '"':
                    out.append('\\"')
                    i += 1
                else:
                    out.append(c2)
                    i += 1
            out.append('"')

        elif c == "`":
            # Template literal: strip ${...} expressions, keep plain text
            out.append('"')
            i += 1
            while i < n:
                c2 = js[i]
                if c2 == "`":
                    i += 1
                    break
                elif c2 == "$" and i + 1 < n and js[i + 1] == "{":
                    # Skip template expression
                    depth = 0
                    i += 2
                    while i < n:
                        if js[i] == "{":
                            depth += 1
                        elif js[i] == "}":
                            if depth == 0:
                                i += 1
                                break
                            depth -= 1
                        i += 1
                    out.append("{{dynamic}}")
                elif c2 == '"':
                    out.append('\\"')
                    i += 1
                elif c2 == "\\" and i + 1 < n:
                    out.append("\\")
                    out.append(js[i + 1])
                    i += 2
                else:
                    out.append(c2)
                    i += 1
            out.append('"')

        else:
            out.append(c)
            i += 1

    normalised = "".join(out)

    # ── Pass 2: quote bare identifier keys ────────────────────────────────
    # After normalisation all strings are double-quoted, so we can safely
    # skip over them and look for bare identifiers followed by ':'.
    out2: list[str] = []
    i = 0
    n = len(normalised)

    while i < n:
        c = normalised[i]

        if c == '"':
            # Copy string verbatim
            out2.append(c)
            i += 1
            while i < n:
                c2 = normalised[i]
                out2.append(c2)
                if c2 == "\\":
                    i += 1
                    if i < n:
                        out2.append(normalised[i])
                elif c2 == '"':
                    break
                i += 1
            i += 1

        elif re.match(r"[A-Za-z_$]", c):
            # Scan to end of identifier
            j = i
            while j < n and re.match(r"[\w$-]", normalised[j]):
                j += 1
            # Check for optional whitespace + ':'
            k = j
            while k < n and normalised[k] in " \t\n\r":
                k += 1
            if k < n and normalised[k] == ":":
                # Bare key — wrap in quotes
                out2.append('"')
                out2.append(normalised[i:j])
                out2.append('"')
                i = j
            else:
                # Might be a value keyword (true/false/null) — emit as-is
                out2.append(c)
                i += 1

        else:
            out2.append(c)
            i += 1

    result = "".join(out2)

    # ── Pass 3: strip trailing commas ─────────────────────────────────────
    result = re.sub(r",(\s*[}\]])", r"\1", result)
    return result


def _parse_js_object(text: str) -> dict:
    """Extract and JSON-parse the main object literal from a TS/JS source file."""
    clean = _strip_comments(text)
    start = _find_object_start(clean)
    js_obj = _extract_balanced(clean, start)
    json_str = _js_to_json(js_obj)
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {}


def _dict_to_js(d: dict, indent: int = 2, level: int = 0) -> str:
    """Serialise *d* back to a JS object literal with bare keys where possible."""
    if not d:
        return "{}"
    pad = " " * (indent * level)
    inner = " " * (indent * (level + 1))
    lines: list[str] = []
    for k, v in d.items():
        # Use bare key if it's a valid JS identifier; otherwise quote it
        key_str = k if re.match(r"^[A-Za-z_$][A-Za-z0-9_$]*$", k) else f'"{k}"'
        if isinstance(v, dict):
            val_str = _dict_to_js(v, indent, level + 1)
        else:
            escaped = (
                str(v)
                .replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t")
            )
            val_str = f'"{escaped}"'
        lines.append(f"{inner}{key_str}: {val_str}")
    return "{\n" + ",\n".join(lines) + "\n" + pad + "}"


def _splice_object(original: str, new_obj_js: str) -> str:
    """Replace the main object literal in *original* with *new_obj_js*."""
    clean = _strip_comments(original)
    start = _find_object_start(clean)
    old_obj = _extract_balanced(original, start)
    end = start + len(old_obj)
    return original[:start] + new_obj_js + original[end:]
