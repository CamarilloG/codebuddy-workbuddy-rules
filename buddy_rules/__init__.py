"""Offline request transformations. No credentials, network, or persistence."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from importlib.resources import files
import json
import re
from typing import Any, Mapping

__version__ = "0.1.0"


def ruleset() -> dict[str, Any]:
    """Return a fresh rules manifest; callers cannot mutate shared state."""
    return json.loads(files(__package__).joinpath("rules.json").read_text(encoding="utf-8"))


@dataclass(frozen=True)
class Change:
    rule_id: str
    path: str
    action: str


@dataclass
class Result:
    payload: dict[str, Any]
    headers: dict[str, str]
    changes: list[Change]
    ruleset_version: str = __version__


def _text(content: Any, role: str, selected: list[dict], path: str, changes: list[Change]) -> Any:
    def apply(value: str, location: str) -> str:
        for rule in selected:
            if role not in rule["roles"]:
                continue
            updated = re.sub(rule["pattern"], rule["replacement"], value)
            if updated != value:
                changes.append(Change(rule["id"], location, "replace"))
                value = updated
        return value

    if isinstance(content, str):
        return apply(content, path)
    if isinstance(content, list):
        for i, block in enumerate(content):
            if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str):
                block["text"] = apply(block["text"], f"{path}[{i}].text")
    return content


def transform(
    payload: Mapping[str, Any],
    headers: Mapping[str, str] | None = None,
    *,
    platform: str,
    region: str = "cn",
    identity_rules: tuple[str, ...] = (),
    allow_international_identity: bool = False,
    extra_forward_headers: tuple[str, ...] = (),
) -> Result:
    """Transform a copy; return metadata-only changes. Never send a request.

    Identity rules are explicit opt-ins. WorkBuddy international identity edits
    additionally require allow_international_identity=True (not a support claim).
    Caller authentication must be injected AFTER this function by the host.
    Unknown headers are dropped, including caller session and product headers.
    """
    if not isinstance(allow_international_identity, bool):
        raise ValueError("allow_international_identity must be a boolean")
    if headers is not None and not isinstance(headers, Mapping):
        raise ValueError("headers must be a mapping")
    if not isinstance(identity_rules, (tuple, list)) or any(not isinstance(x, str) for x in identity_rules):
        raise ValueError("identity_rules must be a sequence of rule IDs")
    if not isinstance(extra_forward_headers, (tuple, list)) or any(not isinstance(x, str) for x in extra_forward_headers):
        raise ValueError("extra_forward_headers must be a sequence of names")
    if platform not in {"codebuddy", "workbuddy"}:
        raise ValueError("platform must be codebuddy or workbuddy")
    if region not in {"cn", "intl"}:
        raise ValueError("region must be cn or intl")
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    manifest = ruleset()
    available = {r["id"]: r for r in manifest["text_rules"]}
    if set(identity_rules) - available.keys():
        raise ValueError("unknown identity rule ID")
    if platform == "workbuddy" and region == "intl" and identity_rules and not allow_international_identity:
        raise ValueError("international identity processing requires explicit opt-in")
    selected = [r for r in manifest["text_rules"] if r["id"] in identity_rules]
    changes: list[Change] = []
    body = deepcopy(dict(payload))
    messages = body.get("messages", [])
    if not isinstance(messages, list) or any(not isinstance(m, dict) for m in messages):
        raise ValueError("messages must be a list of objects")
    for i, msg in enumerate(messages):
        role = msg.get("role")
        if not isinstance(role, str):
            raise ValueError("each message must have a string role")
        if role == "developer":
            msg["role"] = "system"
            changes.append(Change("compat.developer-role", f"messages[{i}].role", "replace"))
        if role in {"system", "developer", "assistant"} and "content" in msg:
            msg["content"] = _text(msg["content"], role, selected, f"messages[{i}].content", changes)
        if platform == "workbuddy" and role == "assistant" and msg.get("tool_calls") == []:
            del msg["tool_calls"]
            changes.append(Change("compat.empty-tool-calls", f"messages[{i}].tool_calls", "remove"))
    if platform == "workbuddy":
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": "You are a helpful assistant."})
            changes.append(Change("compat.workbuddy-system", "messages[0]", "insert"))
        body["messages"] = messages
        if body.get("stream") is not True:
            changes.append(Change("compat.workbuddy-stream", "stream", "replace"))
        body["stream"] = True
        options = body.setdefault("stream_options", {})
        if not isinstance(options, dict):
            raise ValueError("stream_options must be an object")
        if options.get("include_usage") is not True:
            changes.append(Change("compat.workbuddy-usage", "stream_options.include_usage", "replace"))
        options["include_usage"] = True
    if platform == "codebuddy" and isinstance(body.get("tool_choice"), dict):
        choice = body["tool_choice"]
        function = choice.get("function")
        name = function.get("name") if isinstance(function, dict) else None
        if choice.get("type") != "function" or not isinstance(name, str) or not name:
            raise ValueError("unsupported tool_choice object")
        tools = body.get("tools", [])
        if not isinstance(tools, list):
            raise ValueError("tools must be a list")
        matching = [t for t in tools if isinstance(t, dict) and t.get("type") == "function"
                    and isinstance(t.get("function"), dict) and t["function"].get("name") == name]
        if not matching:
            raise ValueError("selected function is missing from tools")
        body["tools"], body["tool_choice"] = matching, "required"
        changes.append(Change("compat.codebuddy-tool-choice", "tools,tool_choice", "replace"))
    policy = manifest["header_policy"]
    forbidden = set(policy["never_forward"])
    allowed = set(policy["default_forward"])
    for name in extra_forward_headers:
        normalized = name.lower()
        if normalized in forbidden or normalized in policy["agent_identity_examples"]:
            raise ValueError("sensitive or client-identity header cannot be forwarded")
        if not re.fullmatch(r"[a-z0-9!#$%&'*+.^_`|~-]+", normalized):
            raise ValueError("invalid extra header name")
        allowed.add(normalized)
    output: dict[str, str] = {}
    # Connection-nominated fields must never be forwarded, even with an allowlist.
    nominated = set()
    for name, value in (headers or {}).items():
        if not isinstance(name, str) or not isinstance(value, str):
            raise ValueError("header names and values must be strings")
        if name.lower() == "connection":
            nominated.update(v.strip().lower() for v in value.split(","))
    for name, value in (headers or {}).items():
        key = name.lower()
        if key not in allowed or key in forbidden or key in nominated:
            # Do not echo arbitrary header names or values into the audit trail.
            changes.append(Change("headers.allowlist", "headers", "remove"))
            continue
        if any((ord(char) < 32 and char != "\t") or ord(char) == 127 for char in value):
            raise ValueError("invalid forwarded header value")
        if key in output:
            raise ValueError("duplicate forwarded header name")
        output[key] = value
    return Result(body, output, changes)
