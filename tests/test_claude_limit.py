"""Offline tests for skills/claude-limit/scripts/claude_limit.py. No real token, no real endpoint."""
import http.server
import io
import json
import sys
import tempfile
import threading
import unittest
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "claude-limit" / "scripts"))
import claude_limit as cl  # noqa: E402

NOW = 1_800_000_000.0
TOKEN = "sk-ant-oat-TEST-SECRET-9f3c"
ANSI = "\033["


def iso(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def creds(expires_in=3600, token=TOKEN):
    return {"claudeAiOauth": {"accessToken": token, "expiresAt": (NOW + expires_in) * 1000,
                              "subscriptionType": "pro"}}


def live_payload(five=42.0, seven=81.0):
    return {"five_hour": {"utilization": five, "resets_at": iso(NOW + 4320)},
            "seven_day": {"utilization": seven, "resets_at": iso(NOW + 2 * 86400 + 5 * 3600)}}


def ravenline(age=180, five=30, seven=50):
    return {"ts": NOW - age, "rate_limits": {
        "five_hour": {"used_percentage": five, "resets_at": NOW + 3600},
        "seven_day": {"used_percentage": seven, "resets_at": NOW + 86400}}}


class FakeResponse:
    def __init__(self, body, status=200):
        self.status, self._body = status, body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeOpener:
    def __init__(self, payload=None, error=None, raw=None):
        self.payload, self.error, self.raw, self.requests = payload, error, raw, []

    def open(self, request, timeout=None):
        self.requests.append(request)
        if self.error:
            raise self.error
        body = self.raw if self.raw is not None else json.dumps(self.payload).encode()
        return FakeResponse(body)


def http_error(code):
    return urllib.error.HTTPError(cl.USAGE_URL, code, "error", {}, None)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        (self.home / ".claude").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, data):
        text = data if isinstance(data, str) else json.dumps(data)
        (self.home / ".claude" / name).write_text(text, encoding="utf-8")

    def collect(self, opener):
        return cl.collect(home=self.home, now=NOW, opener=opener)

    def run_main(self, opener, *args):
        out = io.StringIO()
        code = cl.main(list(args), home=self.home, now=NOW, opener=opener, out=out)
        return code, out.getvalue()


class LiveTests(Base):
    def test_live_success(self):
        self.write(".credentials.json", creds())
        opener = FakeOpener(live_payload())
        result = self.collect(opener)
        self.assertEqual(result["source"], "live")
        self.assertEqual(result["plan"], "pro")
        self.assertEqual([w["used_percent"] for w in result["windows"]], [42.0, 81.0])
        self.assertEqual([w["resets_in"] for w in result["windows"]], ["1h 12m", "2d 5h"])
        request = opener.requests[0]
        self.assertEqual(request.get_header("Authorization"), f"Bearer {TOKEN}")
        self.assertEqual(request.get_header("Anthropic-beta"), "oauth-2025-04-20")

    def test_extra_window_is_shown(self):
        self.write(".credentials.json", creds())
        payload = live_payload()
        payload["seven_day_opus"] = {"utilization": 95.0, "resets_at": iso(NOW + 3600)}
        names = [w["name"] for w in self.collect(FakeOpener(payload))["windows"]]
        self.assertEqual(names, ["5-hour", "7-day", "seven day opus"])


class CredentialTests(Base):
    def test_missing_credentials_falls_back(self):
        self.write("ravenline-limits.json", ravenline())
        opener = FakeOpener(live_payload())
        result = self.collect(opener)
        self.assertEqual(result["source"], "ravenline")
        self.assertEqual(opener.requests, [])

    def test_corrupt_credentials_falls_back(self):
        self.write(".credentials.json", "{not json")
        self.write("ravenline-limits.json", ravenline())
        opener = FakeOpener(live_payload())
        self.assertEqual(self.collect(opener)["source"], "ravenline")
        self.assertEqual(opener.requests, [])

    def test_expired_token_skips_live(self):
        self.write(".credentials.json", creds(expires_in=-60))
        self.write("ravenline-limits.json", ravenline())
        opener = FakeOpener(live_payload())
        result = self.collect(opener)
        self.assertEqual(opener.requests, [])
        self.assertEqual(result["source"], "ravenline")
        self.assertTrue(any("expired" in w for w in result["warnings"]))


class FailureTests(Base):
    def test_http_errors_fall_back(self):
        self.write(".credentials.json", creds())
        self.write("ravenline-limits.json", ravenline())
        for code in (401, 429, 500):
            with self.subTest(code=code):
                result = self.collect(FakeOpener(error=http_error(code)))
                self.assertEqual(result["source"], "ravenline")
                self.assertTrue(any(str(code) in w for w in result["warnings"]))

    def test_network_error_falls_back(self):
        self.write(".credentials.json", creds())
        self.write("ravenline-limits.json", ravenline())
        result = self.collect(FakeOpener(error=urllib.error.URLError("down")))
        self.assertEqual(result["source"], "ravenline")
        self.assertTrue(any("network" in w for w in result["warnings"]))

    def test_changed_response_shape_is_unknown(self):
        self.write(".credentials.json", creds())
        for payload in ({"foo": 1}, {"five_hour": {"utilization": None}}, ["list"]):
            with self.subTest(payload=payload):
                code, text = self.run_main(FakeOpener(payload), "--color", "never")
                self.assertEqual(code, 1)
                self.assertIn("no data", text)
                self.assertIn("UNKNOWN", text)

    def test_invalid_json_is_unknown(self):
        self.write(".credentials.json", creds())
        result = self.collect(FakeOpener(raw=b"<html>"))
        self.assertEqual(result["windows"], [])
        self.assertTrue(any("valid JSON" in w for w in result["warnings"]))


class RavenlineTests(Base):
    def test_stale_snapshot_is_unknown(self):
        self.write("ravenline-limits.json", ravenline(age=46 * 60))
        result = self.collect(FakeOpener())
        self.assertEqual(result["windows"], [])
        self.assertTrue(any("stale" in w for w in result["warnings"]))

    def test_fresh_snapshot_within_limit_is_used(self):
        self.write("ravenline-limits.json", ravenline(age=44 * 60))
        result = self.collect(FakeOpener())
        self.assertEqual(result["source"], "ravenline")
        self.assertEqual(result["age_minutes"], 44)

    def test_future_snapshot_is_unknown(self):
        self.write("ravenline-limits.json", ravenline(age=-120))
        self.assertEqual(self.collect(FakeOpener())["windows"], [])

    def test_all_zero_snapshot_is_unreadable(self):
        self.write("ravenline-limits.json", ravenline(five=0, seven=0))
        result = self.collect(FakeOpener())
        self.assertEqual(result["windows"], [])
        self.assertTrue(any("all zero" in w for w in result["warnings"]))

    def test_reset_formats(self):
        for value in (NOW + 60, (NOW + 60) * 1000, iso(NOW + 60)):
            with self.subTest(value=value):
                self.assertAlmostEqual(cl.reset_ts(value), NOW + 60, places=3)
        self.assertIsNone(cl.reset_ts("2026-01-01T00:00:00"))  # no timezone


class RenderTests(Base):
    def test_expired_window_is_flagged_red(self):
        self.write(".credentials.json", creds())
        payload = live_payload()
        payload["five_hour"]["resets_at"] = iso(NOW - 600)
        result = self.collect(FakeOpener(payload))
        self.assertTrue(result["windows"][0]["expired"])
        text = cl.render(result, color=True)
        self.assertIn(cl.RED + " 42%", text)
        self.assertIn("WINDOW EXPIRED", text)

    def test_color_bands(self):
        for used, expected in ((69, cl.GREEN), (70, cl.YELLOW), (89, cl.YELLOW), (90, cl.RED)):
            with self.subTest(used=used):
                self.assertEqual(cl.band({"used_percent": used, "expired": False}), expected)

    def test_color_never_has_no_ansi(self):
        self.write(".credentials.json", creds())
        _, text = self.run_main(FakeOpener(live_payload()), "--color", "never")
        self.assertNotIn(ANSI, text)
        self.assertIn("[########............]", text)

    def test_color_always_has_ansi(self):
        self.write(".credentials.json", creds())
        _, text = self.run_main(FakeOpener(live_payload()), "--color", "always")
        self.assertIn(cl.GREEN, text)


class TokenLeakTests(Base):
    def test_token_never_in_output(self):
        self.write(".credentials.json", creds())
        self.write("ravenline-limits.json", ravenline())
        openers = [FakeOpener(live_payload()), FakeOpener(error=http_error(401)),
                   FakeOpener(error=http_error(500)), FakeOpener(error=urllib.error.URLError(TOKEN)),
                   FakeOpener(raw=TOKEN.encode())]
        for opener in openers:
            for args in (["--json"], ["--color", "always"]):
                with self.subTest(opener=opener.error or opener.raw, args=args):
                    _, text = self.run_main(opener, *args)
                    self.assertNotIn(TOKEN, text)


class RedirectTests(unittest.TestCase):
    """Real local servers: a redirect must not carry the token to another origin."""

    def serve(self, handler):
        server = http.server.HTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return f"http://127.0.0.1:{server.server_port}/"

    def test_redirect_is_not_followed(self):
        seen = []

        class Target(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                seen.append(self.headers.get("Authorization"))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(live_payload()).encode())

            def log_message(self, *args):
                pass

        target = self.serve(Target)

        class Redirect(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(302)
                self.send_header("Location", target)
                self.end_headers()

            def log_message(self, *args):
                pass

        source = self.serve(Redirect)
        payload, reason = cl.fetch_live(TOKEN, url=source)
        self.assertIsNone(payload)
        self.assertIn("redirect", reason)
        self.assertEqual(seen, [])


if __name__ == "__main__":
    unittest.main()
