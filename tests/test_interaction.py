"""
Tests for the interaction subsystem: voice commands, chat + interludes,
sandbox preview, and pluggable AI model providers (all offline).
"""

import os
import sys
import unittest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from assistant import AssistantEngine
from interaction import (
    ChatSession,
    CommandParser,
    DictSpeechEngine,
    InteractionController,
    InterludeManager,
    SnippetSandbox,
    VoiceCommandProcessor,
)
from interaction.providers import (
    ADAPTER_KINDS,
    HuggingFaceProvider,
    MockProvider,
    ProviderError,
    ProviderManager,
    ProviderRegistry,
    TogetherProvider,
)


def make_engine():
    return AssistantEngine.from_config({}, clock=lambda: 1.0)


class CommandParserTests(unittest.TestCase):
    def test_wake_word_stripped(self):
        p = CommandParser(wake_word="aicodex")
        cmd = p.parse("aicodex analyze the data")
        self.assertEqual(cmd.intent, "analyze")
        self.assertEqual(cmd.argument, "the data")

    def test_no_wake_word_ok(self):
        p = CommandParser(wake_word="aicodex")
        cmd = p.parse("analyze the data")
        self.assertEqual(cmd.intent, "analyze")

    def test_longest_keyword_wins(self):
        p = CommandParser()
        cmd = p.parse("insert snippet for loops")
        self.assertEqual(cmd.intent, "insert_snippet")
        self.assertEqual(cmd.argument, "for loops")

    def test_unknown_intent(self):
        p = CommandParser()
        cmd = p.parse("blorp the zazzle")
        self.assertEqual(cmd.intent, "unknown")

    def test_empty_is_unknown(self):
        p = CommandParser()
        self.assertEqual(p.parse("").intent, "unknown")
        self.assertEqual(p.parse(None).intent, "unknown")

    def test_preview_and_interlude(self):
        p = CommandParser()
        self.assertEqual(p.parse("preview print(1)").intent, "preview")
        self.assertEqual(p.parse("brainstorm api design").intent, "interlude")
        self.assertEqual(p.parse("resume").intent, "stop_interlude")


class VoiceCommandProcessorTests(unittest.TestCase):
    def test_dispatch_to_hook(self):
        proc = VoiceCommandProcessor(CommandParser(), DictSpeechEngine())
        proc.on("analyze", lambda arg: f"analyzed: {arg}")
        out = proc.handle_utterance("analyze the metrics")
        self.assertEqual(out, "analyzed: the metrics")

    def test_unknown_command_friendly(self):
        proc = VoiceCommandProcessor(CommandParser(), DictSpeechEngine())
        out = proc.handle_utterance("zqx wkv")
        self.assertIn("didn't understand", out)

    def test_unwired_intent_friendly(self):
        proc = VoiceCommandProcessor(CommandParser(), DictSpeechEngine())
        out = proc.handle_utterance("format the code")
        self.assertIn("not available", out)

    def test_listen_once_uses_speech_engine(self):
        speech = DictSpeechEngine(["analyze the data"])
        proc = VoiceCommandProcessor(CommandParser(), speech)
        proc.on("analyze", lambda arg: f"ok {arg}")
        self.assertEqual(proc.listen_once(), "ok the data")
        # speak() was called with the response
        self.assertIn("ok the data", speech.spoken)


class ChatSessionTests(unittest.TestCase):
    def test_send_user_appends_and_replies(self):
        session = ChatSession(make_engine(), clock=lambda: 1.0)
        reply = session.send_user("analyze the data and measure it")
        self.assertTrue(reply)
        roles = [m.role for m in session.messages]
        self.assertEqual(roles, ["user", "assistant"])

    def test_history_bounded(self):
        session = ChatSession(make_engine(), max_history=4, clock=lambda: 1.0)
        for i in range(5):
            session.send_user(f"question {i} about data analysis")
        self.assertLessEqual(len(session.messages), 4)

    def test_apply_adjustment_retunes_persona(self):
        engine = make_engine()
        session = ChatSession(engine, clock=lambda: 1.0)
        before = session.engine.persona.trait("creative")
        session.apply_adjustment(traits={"creative": 0.99}, tone="creative")
        self.assertEqual(session.engine.persona.trait("creative"), 0.99)
        self.assertEqual(session.engine.persona.tone, "creative")
        self.assertNotEqual(before, 0.99)


class InterludeManagerTests(unittest.TestCase):
    def test_start_brainstorm_end_applies_adjustments(self):
        session = ChatSession(make_engine(), clock=lambda: 1.0)
        mgr = InterludeManager(session)
        mgr.start("api design")
        self.assertTrue(mgr.active)
        mgr.brainstorm("what if we cache the results creatively")
        mgr.adjust_model(traits={"creative": 0.95}, tone="creative")
        result = mgr.end()
        self.assertIn("interlude ended", result)
        self.assertIn("adjustments applied", result)
        self.assertFalse(mgr.active)
        self.assertEqual(session.engine.persona.trait("creative"), 0.95)

    def test_end_without_active(self):
        mgr = InterludeManager(ChatSession(make_engine(), clock=lambda: 1.0))
        self.assertEqual(mgr.end(), "No interlude is currently active.")

    def test_end_without_adjustments(self):
        session = ChatSession(make_engine(), clock=lambda: 1.0)
        mgr = InterludeManager(session)
        mgr.start("quick think")
        mgr.brainstorm("just a thought")
        result = mgr.end()
        self.assertNotIn("adjustments applied", result)


class SnippetSandboxTests(unittest.TestCase):
    def setUp(self):
        self.sandbox = SnippetSandbox()

    def test_runs_and_captures_result(self):
        res = self.sandbox.run("result = 6 * 7\nprint(result)")
        self.assertTrue(res.ok)
        self.assertEqual(res.result, 42)
        self.assertIn("42", res.stdout)

    def test_error_captured(self):
        res = self.sandbox.run("1/0")
        self.assertFalse(res.ok)
        self.assertIn("ZeroDivisionError", res.error)

    def test_blocked_import(self):
        res = self.sandbox.run("import os")
        self.assertFalse(res.ok)
        self.assertIn("not allowed", res.error)

    def test_blocked_builtin(self):
        res = self.sandbox.run("open('/etc/passwd')")
        self.assertFalse(res.ok)

    def test_empty_snippet(self):
        res = self.sandbox.run("   ")
        self.assertFalse(res.ok)
        self.assertIn("Empty", res.error)

    def test_disabled(self):
        sb = SnippetSandbox(enabled=False)
        res = sb.run("print(1)")
        self.assertFalse(res.ok)
        self.assertIn("disabled", res.error)

    def test_timeout(self):
        sb = SnippetSandbox(timeout_seconds=1)
        res = sb.run("while True: pass")
        self.assertFalse(res.ok)
        self.assertTrue(res.timed_out)

    def test_output_truncation(self):
        sb = SnippetSandbox(max_output_chars=120)
        res = sb.run("print('x' * 5000)")
        self.assertTrue(res.truncated)
        self.assertLessEqual(len(res.stdout), 120)


class ProviderAdapterTests(unittest.TestCase):
    def test_all_kinds_registered(self):
        # Original 8 kinds must always be present (regression guard); newer
        # kinds (grok4, openrouter, gemini, ...) may be added over time.
        expected = {
            "huggingface", "northflank", "bentoml", "replicate",
            "modal", "lambdalabs", "together", "runpod",
        }
        self.assertTrue(expected.issubset(set(ADAPTER_KINDS.keys())))

    def test_together_builds_openai_style_request(self):
        captured = {}

        def transport(url, headers, payload, timeout):
            captured["url"] = url
            captured["headers"] = headers
            import json
            captured["payload"] = json.loads(payload.decode())
            return {"choices": [{"message": {"content": "hello"}}]}

        p = TogetherProvider(
            name="together",
            endpoint="https://api.together.xyz/v1",
            api_key_env="TOGETHER_API_KEY",
            transport=transport,
            environ={"TOGETHER_API_KEY": "test-key"},
        )
        resp = p.generate("llama-3", "Say hi")
        self.assertEqual(resp.text, "hello")
        self.assertEqual(captured["url"], "https://api.together.xyz/v1/chat/completions")
        self.assertEqual(captured["payload"]["model"], "llama-3")
        self.assertIn("Authorization", captured["headers"])

    def test_huggingface_request_shape(self):
        captured = {}

        def transport(url, headers, payload, timeout):
            captured["url"] = url
            return [{"generated_text": "hf says hi"}]

        p = HuggingFaceProvider(
            name="huggingface",
            endpoint="https://api-inference.huggingface.co/models",
            api_key_env="HUGGINGFACE_API_KEY",
            transport=transport,
            environ={},
        )
        resp = p.generate("gpt2", "hello")
        self.assertEqual(resp.text, "hf says hi")
        self.assertEqual(captured["url"], "https://api-inference.huggingface.co/models/gpt2")

    def test_disabled_provider_raises(self):
        p = TogetherProvider(name="t", endpoint="x", enabled=False)
        with self.assertRaises(ProviderError):
            p.generate("m", "p")

    def test_api_key_from_env_not_stored(self):
        p = TogetherProvider(
            name="t", endpoint="x", api_key_env="MY_KEY",
            environ={"MY_KEY": "sekret"},
        )
        self.assertEqual(p.api_key(), "sekret")
        # The key value must never be stored as an instance attribute.
        self.assertFalse(any("sekret" in str(v) for v in vars(p).values()))


class ProviderRegistryManagerTests(unittest.TestCase):
    def test_from_config_builds_and_filters(self):
        cfg = [
            {"name": "hf", "kind": "huggingface", "endpoint": "e", "enabled": True},
            {"name": "rp", "kind": "runpod", "endpoint": "e", "enabled": False},
            {"name": "bogus", "kind": "not-a-thing", "endpoint": "e"},
        ]
        reg = ProviderRegistry.from_config(cfg, environ={})
        self.assertIn("hf", reg.names())
        self.assertIn("rp", reg.names())
        self.assertNotIn("bogus", reg.names())
        self.assertEqual([p.name for p in reg.enabled()], ["hf"])

    def test_choose_prefers_named_enabled(self):
        reg = ProviderRegistry.from_config(
            [
                {"name": "a", "kind": "together", "endpoint": "e", "enabled": True},
                {"name": "b", "kind": "modal", "endpoint": "e", "enabled": False},
            ],
            environ={},
        )
        mgr = ProviderManager(reg)
        self.assertEqual(mgr.choose("a").name, "a")
        # Named but disabled → first enabled.
        self.assertEqual(mgr.choose("b").name, "a")

    def test_falls_back_to_mock_when_none_enabled(self):
        reg = ProviderRegistry.from_config(
            [{"name": "b", "kind": "modal", "endpoint": "e", "enabled": False}],
            environ={},
        )
        mgr = ProviderManager(reg)
        resp = mgr.generate("m", "hello", provider_name="b")
        self.assertEqual(resp.provider, "mock")

    def test_generate_falls_back_on_provider_error(self):
        def boom(url, headers, payload, timeout):
            raise RuntimeError("network down")

        reg = ProviderRegistry.from_config(
            [{"name": "a", "kind": "together", "endpoint": "e", "enabled": True}],
            transport=boom,
            environ={},
        )
        mgr = ProviderManager(reg)
        resp = mgr.generate("m", "hi", provider_name="a")
        self.assertEqual(resp.provider, "mock")


class InteractionControllerTests(unittest.TestCase):
    def _controller(self):
        engine = make_engine()
        cfg = {
            "interaction": {
                "voice": {"enabled": True, "wake_word": "aicodex"},
                "chat": {"max_history": 50},
                "sandbox": {"enabled": True, "timeout_seconds": 3},
                "providers": [
                    {"name": "mockonly", "kind": "together", "endpoint": "e", "enabled": False}
                ],
            }
        }
        return InteractionController.from_config(engine, cfg, environ={}, clock=lambda: 1.0)

    def test_chat_roundtrip(self):
        ctl = self._controller()
        reply = ctl.chat("analyze the data and measure it")
        self.assertTrue(reply)

    def test_voice_end_to_end(self):
        ctl = self._controller()
        out = ctl.handle_voice("aicodex analyze the performance metrics")
        self.assertTrue(out)

    def test_interlude_flow(self):
        ctl = self._controller()
        self.assertIn("Interlude started", ctl.start_interlude("design"))
        ctl.brainstorm("creative idea")
        ctl.adjust_model(traits={"creative": 0.9})
        self.assertIn("adjustments applied", ctl.end_interlude())
        # The live persona reflects the interlude's modelling adjustment.
        self.assertEqual(ctl.persona.trait("creative"), 0.9)

    def test_preview_via_controller(self):
        ctl = self._controller()
        res = ctl.preview("result = 2 + 2")
        self.assertTrue(res.ok)
        self.assertEqual(res.result, 4)

    def test_generate_uses_mock_fallback(self):
        ctl = self._controller()
        resp = ctl.generate("model", "prompt", provider_name="mockonly")
        self.assertEqual(resp.provider, "mock")


if __name__ == "__main__":
    unittest.main()
