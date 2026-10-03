"""
Robust JSON extraction, repair, and parsing utilities for LLM outputs.
Handles markdown blocks, trailing commas, single quotes, and truncated JSON.
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def clean_markdown_fences(text: str) -> str:
    """Strip markdown code block syntax if present."""
    text = text.strip()
    if text.startswith("```"):
        # Remove opening fence like ```json or ```
        lines = text.splitlines()
        if len(lines) > 1 and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def repair_truncated_json(text: str) -> str:
    """Attempt to repair incomplete/truncated JSON string by closing open quotes and brackets."""
    # Count open/close braces and brackets while respecting escaped quotes
    in_string = False
    escape = False
    stack = []

    for char in text:
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if not in_string:
            if char in "{[":
                stack.append(char)
            elif char == "}":
                if stack and stack[-1] == "{":
                    stack.pop()
            elif char == "]":
                if stack and stack[-1] == "[":
                    stack.pop()

    # If truncated inside a string, close the string
    if in_string:
        text += '"'

    # Remove any trailing comma or dangling colon before closing
    text = re.sub(r",\s*$", "", text.strip())
    text = re.sub(r":\s*$", ': ""', text.strip())

    # Close remaining open brackets/braces in reverse order
    while stack:
        opener = stack.pop()
        if opener == "{":
            text += "}"
        elif opener == "[":
            text += "]"

    return text


def extract_and_parse_json(text: str, default: Any = None) -> Any:
    """Extract and parse JSON from arbitrary LLM response text.

    Args:
        text: Raw LLM output string.
        default: Default value to return if all parsing attempts fail.

    Returns:
        Parsed dict, list, or default value.
    """
    if not text or not text.strip():
        return default

    cleaned = clean_markdown_fences(text)

    # 1. Direct standard parse
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # 2. Extract substring between first { or [ and last } or ]
    match_dict = re.search(r"(\{[\s\S]*\})", cleaned)
    match_list = re.search(r"(\[[\s\S]*\])", cleaned)

    candidate = None
    if match_dict and match_list:
        # Pick the one that starts earlier
        if match_dict.start() < match_list.start():
            candidate = match_dict.group(1)
        else:
            candidate = match_list.group(1)
    elif match_dict:
        candidate = match_dict.group(1)
    elif match_list:
        candidate = match_list.group(1)
    else:
        # If no complete match, find first { or [ to the end
        first_brace = cleaned.find("{")
        first_bracket = cleaned.find("[")
        if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
            candidate = cleaned[first_brace:]
        elif first_bracket != -1:
            candidate = cleaned[first_bracket:]

    if candidate:
        # Remove trailing commas before closing braces/brackets
        candidate_clean = re.sub(r",\s*([\}\]])", r"\1", candidate)
        try:
            return json.loads(candidate_clean)
        except Exception:
            pass

        # Try replacing Python literals True, False, None if standard JSON failed
        replaced_literals = re.sub(r"\bTrue\b", "true", candidate_clean)
        replaced_literals = re.sub(r"\bFalse\b", "false", replaced_literals)
        replaced_literals = re.sub(r"\bNone\b", "null", replaced_literals)
        try:
            return json.loads(replaced_literals)
        except Exception:
            pass

        # Try repairing truncated JSON
        repaired = repair_truncated_json(candidate_clean)
        repaired = re.sub(r",\s*([\}\]])", r"\1", repaired)
        try:
            return json.loads(repaired)
        except Exception as exc:
            logger.debug("Repaired JSON parse failed: %s", exc)

        # Try repairing with replaced literals
        repaired_lit = repair_truncated_json(replaced_literals)
        repaired_lit = re.sub(r",\s*([\}\]])", r"\1", repaired_lit)
        try:
            return json.loads(repaired_lit)
        except Exception:
            pass

    return default
