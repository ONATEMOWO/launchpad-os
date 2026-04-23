# -*- coding: utf-8 -*-
"""Optional AI-assisted intake helpers."""
import json
from urllib import error, request

VALID_CATEGORIES = {"internship", "scholarship", "research", "fellowship"}
MAX_CHECKLIST_ITEMS = 6
MAX_TAGS = 5

SYSTEM_PROMPT = """
You are an intake assistant for a student application workspace.
Given rough opportunity text, return only valid JSON with these keys:
- title
- organization
- category
- deadline_text
- summary
- checklist_items
- tags

Rules:
- category must be one of: internship, scholarship, research
- deadline_text should be a short recognizable date string if present, otherwise ""
- summary should be 1-2 sentences
- checklist_items should be a short list of practical application tasks
- tags should be a short list of useful organization tags
- do not include markdown or extra commentary
""".strip()


def ai_intake_configured(app):
    """Return whether AI-assisted intake is configured."""
    return all(
        [
            app.config.get("AI_INTAKE_ENDPOINT"),
            app.config.get("AI_INTAKE_API_KEY"),
            app.config.get("AI_INTAKE_MODEL"),
        ]
    )


def _extract_message_text(payload):
    """Extract text from an OpenAI-compatible chat completions response."""
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return ""

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
        return "\n".join(part for part in text_parts if part)

    return ""


def _load_json_fragment(text):
    """Load a JSON object from a plain response or fenced code block."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            cleaned = "\n".join(lines[1:-1]).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object returned.")
    json_fragment = cleaned[start:]
    json_fragment = json_fragment[: end - start + 1]
    return json.loads(json_fragment)


def _normalize_checklist_items(items):
    """Return a cleaned, unique list of checklist suggestions."""
    if not isinstance(items, list):
        return []

    normalized_items = []
    seen = set()
    for item in items:
        if not isinstance(item, str):
            continue
        cleaned = item.strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized_items.append(cleaned)
        if len(normalized_items) >= MAX_CHECKLIST_ITEMS:
            break
    return normalized_items


def _normalize_tags(items):
    """Return a cleaned, unique list of short tag suggestions."""
    if not isinstance(items, list):
        return []

    normalized_tags = []
    seen = set()
    for item in items:
        if not isinstance(item, str):
            continue
        cleaned = item.strip().strip("#")
        if not cleaned:
            continue
        cleaned = cleaned[:50]
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized_tags.append(cleaned)
        if len(normalized_tags) >= MAX_TAGS:
            break
    return normalized_tags


def normalize_ai_suggestions(payload):
    """Normalize AI output into a predictable dict for the UI."""
    category = (payload.get("category") or "").strip().lower()
    if category not in VALID_CATEGORIES:
        category = ""

    return {
        "used_ai": True,
        "title": (payload.get("title") or "").strip(),
        "organization": (payload.get("organization") or "").strip(),
        "category": category,
        "deadline_text": (payload.get("deadline_text") or "").strip(),
        "summary": (payload.get("summary") or "").strip(),
        "checklist_items": _normalize_checklist_items(
            payload.get("checklist_items") or []
        ),
        "tags": _normalize_tags(payload.get("tags") or []),
        "reason": "AI suggestions are ready to review before you save.",
    }


def ai_unavailable_result(reason):
    """Return a normalized fallback payload."""
    return {
        "used_ai": False,
        "title": "",
        "organization": "",
        "category": "",
        "deadline_text": "",
        "summary": "",
        "checklist_items": [],
        "tags": [],
        "reason": reason,
    }


def request_ai_capture_suggestions(app, capture_text):
    """Request optional AI intake suggestions from a configured endpoint."""
    if not ai_intake_configured(app):
        return ai_unavailable_result(
            "AI suggestions are not configured in this environment yet, "
            "so LaunchPad OS used the standard Quick Capture prefill."
        )

    payload = {
        "model": app.config["AI_INTAKE_MODEL"],
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": capture_text},
        ],
        "temperature": 0.2,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {app.config['AI_INTAKE_API_KEY']}",
    }
    http_request = request.Request(
        app.config["AI_INTAKE_ENDPOINT"],
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with request.urlopen(
            http_request, timeout=app.config.get("AI_INTAKE_TIMEOUT", 20)
        ) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
        message_text = _extract_message_text(response_payload)
        normalized_payload = _load_json_fragment(message_text)
        return normalize_ai_suggestions(normalized_payload)
    except (
        error.URLError,
        error.HTTPError,
        TimeoutError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
    ):
        app.logger.exception("AI-assisted intake request failed")
        return ai_unavailable_result(
            "AI suggestions were unavailable for this capture, so LaunchPad OS used the standard Quick Capture prefill."
        )
