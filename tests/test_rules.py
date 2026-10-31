from copy import deepcopy
from dataclasses import asdict
import json
import unittest

from buddy_rules import ruleset, transform


class RuleTests(unittest.TestCase):
    def run_rule(self, body, **kwargs):
        return transform(body, platform="codebuddy", **kwargs)

    def test_identity_is_off_by_default(self):
        p = {"messages": [{"role": "system", "content": "You are Claude Code, Anthropic's official CLI for Claude."}]}
        self.assertEqual(self.run_rule(p).payload, p)

    def test_roles_and_content_blocks_are_scoped(self):
        identity = "You are Claude Code, Anthropic's official CLI for Claude.\n"
        p = {"messages": [{"role": role, "content": identity + "Keep instructions."} for role in ("system", "assistant", "user", "tool")]}
        before = deepcopy(p)
        r = self.run_rule(p, identity_rules=("identity.claude-code",))
        self.assertEqual(r.payload["messages"][0]["content"], "Keep instructions.")
        self.assertEqual(r.payload["messages"][1]["content"], "Keep instructions.")
        self.assertEqual(r.payload["messages"][2:], p["messages"][2:])
        self.assertEqual(p, before)
        self.assertNotIn(identity, json.dumps([asdict(c) for c in r.changes]))
        self.assertEqual(self.run_rule(r.payload, identity_rules=("identity.claude-code",)).payload, r.payload)

    def test_nontext_blocks_and_calls_remain(self):
        p = {"messages": [{"role": "assistant", "content": [{"type": "text", "text": "You are Claude Code, Anthropic's official CLI for Claude."}, {"type": "image_url", "image_url": {"url": "https://example.invalid/image"}}], "tool_calls": [{"id": "synthetic-call"}]}]}
        r = self.run_rule(p, identity_rules=("identity.claude-code",))
        self.assertEqual(len(r.payload["messages"]), 1)
        self.assertEqual(r.payload["messages"][0]["content"][1], p["messages"][0]["content"][1])
        self.assertEqual(r.payload["messages"][0]["tool_calls"], p["messages"][0]["tool_calls"])

    def test_no_substring_brand_deletion(self):
        p = {"messages": [{"role": "system", "content": "Discuss Claude Code and Codex. You are Claude Code, Anthropic's official CLI for Claude."}]}
        self.assertEqual(self.run_rule(p, identity_rules=("identity.claude-code",)).payload, p)

    def test_codex_does_not_modify_assistant(self):
        text = "Codex CLI is an open source project led by OpenAI.\nKeep task."
        p = {"messages": [{"role": "developer", "content": text}, {"role": "assistant", "content": text}]}
        r = self.run_rule(p, identity_rules=("identity.codex",))
        self.assertEqual(r.payload["messages"][0], {"role": "system", "content": "Keep task."})
        self.assertEqual(r.payload["messages"][1]["content"], text)

    def test_workbuddy_profile_and_idempotence(self):
        p = {"messages": [{"role": "assistant", "tool_calls": [], "reasoning_content": "synthetic reasoning", "content": "ok"}], "stream_options": {"custom": True}}
        r = transform(p, platform="workbuddy")
        self.assertTrue(r.payload["stream"])
        self.assertTrue(r.payload["stream_options"]["custom"])
        self.assertTrue(r.payload["stream_options"]["include_usage"])
        self.assertNotIn("tool_calls", r.payload["messages"][1])
        self.assertEqual(r.payload["messages"][1]["reasoning_content"], "synthetic reasoning")
        self.assertEqual(transform(r.payload, platform="workbuddy").payload, r.payload)

    def test_international_identity_requires_second_optin(self):
        with self.assertRaises(ValueError):
            transform({}, platform="workbuddy", region="intl", identity_rules=("identity.codex",))
        transform({}, platform="workbuddy", region="intl")

    def test_named_tool_and_original_are_preserved(self):
        p = {"tools": [{"type": "function", "function": {"name": n}} for n in ("alpha", "beta")], "tool_choice": {"type": "function", "function": {"name": "beta"}}}
        before = deepcopy(p)
        r = self.run_rule(p)
        self.assertEqual(r.payload["tool_choice"], "required")
        self.assertEqual([t["function"]["name"] for t in r.payload["tools"]], ["beta"])
        self.assertEqual(p, before)
        p["tool_choice"]["function"]["name"] = "missing"
        with self.assertRaises(ValueError):
            self.run_rule(p)

    def test_header_allowlist(self):
        headers = {"Authorization": "synthetic caller credential", "Cookie": "synthetic cookie", "X-IDE-Name": "SyntheticClient", "User-Agent": "SyntheticClient/0", "X-Session-ID": "synthetic-session", "Content-Type": "application/json"}
        r = transform({}, headers, platform="codebuddy")
        self.assertEqual(r.headers, {"content-type": "application/json"})
        audit = json.dumps([asdict(c) for c in r.changes])
        self.assertNotIn("synthetic", audit)
        self.assertEqual(len(headers), 6)

    def test_header_override_cannot_forward_secrets(self):
        for name in ("Authorization", "Cookie", "Host", "User-Agent", "X-IDE-Name"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.run_rule({}, extra_forward_headers=(name,))
        r = transform({}, {"X-Trace": "synthetic", "Connection": "X-Trace"}, platform="codebuddy", extra_forward_headers=("x-trace",))
        self.assertEqual(r.headers, {})

    def test_bad_forwarded_headers(self):
        with self.assertRaises(ValueError):
            transform({}, {"Accept": "ok\r\nInjected: value"}, platform="codebuddy")
        with self.assertRaises(ValueError):
            transform({}, {"Accept": "a", "accept": "b"}, platform="codebuddy")

    def test_international_switch_is_strict_boolean(self):
        for value in ("false", "true", 1, 0, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                transform({}, platform="workbuddy", region="intl", identity_rules=("identity.codex",), allow_international_identity=value)
        transform({}, platform="workbuddy", region="intl", identity_rules=("identity.codex",), allow_international_identity=True)

    def test_feedback_requires_complete_line(self):
        base = "- To give feedback, users should report the issue at https://github.com/anthropics/claude-code/issues"
        for suffix in ("-private policy remains", " and keep this instruction"):
            p = {"messages": [{"role": "system", "content": base + suffix}]}
            self.assertEqual(self.run_rule(p, identity_rules=("identity.claude-feedback",)).payload, p)
        p = {"messages": [{"role": "system", "content": base + "\nKeep task."}]}
        self.assertEqual(self.run_rule(p, identity_rules=("identity.claude-feedback",)).payload["messages"][0]["content"], "Keep task.")

    def test_invalid_header_types_and_controls(self):
        for headers in ([], {"accept": "x\x00y"}, {"accept": 1}):
            with self.subTest(headers=headers), self.assertRaises(ValueError):
                transform({}, headers, platform="codebuddy")
        for args in ({"identity_rules": None}, {"extra_forward_headers": (1,)}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                self.run_rule({}, **args)

    def test_manifest_is_not_shared_mutable_state(self):
        first = ruleset()
        first["text_rules"].clear()
        self.assertTrue(ruleset()["text_rules"])

    def test_bad_inputs(self):
        for kwargs in ({"platform": "unknown"}, {"platform": "codebuddy", "region": "unknown"}, {"platform": "codebuddy", "identity_rules": ("unknown",)}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                transform({}, **kwargs)
        with self.assertRaises(ValueError):
            self.run_rule({"messages": "invalid"})


if __name__ == "__main__":
    unittest.main()
