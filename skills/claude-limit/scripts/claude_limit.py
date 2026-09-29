#!/usr/bin/env python3
"""Show Claude subscription usage windows (5-hour, 7-day) for the claude-limit skill.

Sources, in order:
  1. Live usage endpoint, authenticated with the OAuth token in ~/.claude/.credentials.json.
  2. The ravenline statusline snapshot (~/.claude/ravenline-limits.json), if fresh.
Anything else is reported as unknown -- never as an empty pool.

The token only ever leaves as the Authorization header of the usage endpoint.
It is never printed, logged, written to disk or forwarded across a redirect.

Usage: python claude_limit.py [--color auto|always|never] [--json]
"""
import argparse
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
MAX_AGE_MIN = 45
KNOWN = (("five_hour", "5-hour"), ("seven_day", "7-day"))

RESET, BOLD, DIM = "\033[0m", "\033[1m", "\033[2m"
CYAN, GREEN, YELLOW, RED = "\033[36m", "\033[32m", "\033[33m", "\033[31m"


def number(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
        return float(value)
    return None


def percent(value):
    value = number(value)
    return value if value is not None and 0 <= value <= 100 else None


def reset_ts(value):
    """ISO string or unix time (seconds or milliseconds) -> unix seconds, else None."""
    if isinstance(value, str) and value:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed.timestamp() if parsed.tzinfo else None
    value = number(value)
    if value is None or value <= 0:
        return None
    return value / 1000 if value > 1e12 else value


def fmt_delta(seconds):
    seconds = int(abs(seconds))
    days, rem = divmod(seconds, 86400)
    hours, minutes = rem // 3600, rem % 3600 // 60
    if days:
        return f"{days}d {hours}h" if hours else f"{days}d"
    if hours:
        return f"{hours}h {minutes}m" if minutes else f"{hours}h"
    return f"{minutes}m"


def read_credentials(home, now):
    """Return (token, plan, reason). The token is None when missing or expired."""
    try:
        data = json.loads((home / ".claude" / ".credentials.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, None, "credentials file missing or unreadable"
    oauth = data.get("claudeAiOauth") if isinstance(data, dict) else None
    if not isinstance(oauth, dict):
        return None, None, "no claudeAiOauth block in credentials"
    plan = oauth.get("subscriptionType") if isinstance(oauth.get("subscriptionType"), str) else None
    expires = number(oauth.get("expiresAt"))
    if expires is not None and expires / 1000 < now:
        return None, plan, "token expired: open Claude Code once to refresh it"
    token = oauth.get("accessToken")
    if not isinstance(token, str) or not token:
        return None, plan, "no access token in credentials"
    return token, plan, None


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never follow a redirect: it would carry the Authorization header elsewhere."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def fetch_live(token, url=USAGE_URL, opener=None):
    """Return (payload, reason). Reasons never contain the token."""
    opener = opener or urllib.request.build_opener(NoRedirect())
    request = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "anthropic-beta": "oauth-2025-04-20",
        "User-Agent": "claude-limit/1.0",
    })
    try:
        with opener.open(request, timeout=10) as response:
            if response.status != 200:
                return None, f"endpoint returned HTTP {response.status}"
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        exc.close()
        if exc.code in (401, 403):
            return None, f"token rejected (HTTP {exc.code})"
        if exc.code == 429:
            return None, "endpoint rate-limited (HTTP 429) -- not a quota reading"
        if 300 <= exc.code < 400:
            return None, f"endpoint redirected (HTTP {exc.code}); not followed"
        return None, f"endpoint returned HTTP {exc.code}"
    except (urllib.error.URLError, OSError) as exc:
        return None, f"network unreachable ({exc.__class__.__name__})"
    except (ValueError, UnicodeError):
        return None, "endpoint did not return valid JSON"
    if not isinstance(payload, dict):
        return None, "unexpected response shape"
    return payload, None


def read_ravenline(home, now):
    """Return (windows mapping in endpoint shape, age seconds, reason)."""
    try:
        data = json.loads((home / ".claude" / "ravenline-limits.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, None, "no ravenline snapshot"
    stamp = number(data.get("ts")) if isinstance(data, dict) else None
    limits = data.get("rate_limits") if isinstance(data, dict) else None
    if stamp is None or not isinstance(limits, dict):
        return None, None, "ravenline snapshot has no timestamp or rate_limits"
    age = now - stamp
    if age < 0 or age > MAX_AGE_MIN * 60:
        return None, age, f"ravenline snapshot stale ({fmt_delta(age)} old, limit {MAX_AGE_MIN}m)"
    mapping = {}
    for key, window in limits.items():
        if isinstance(window, dict):
            mapping[key] = {"utilization": window.get("used_percentage"), "resets_at": window.get("resets_at")}
    values = [percent(w["utilization"]) for w in mapping.values()]
    if not values or any(v is None for v in values):
        return None, age, "ravenline snapshot has unreadable percentages"
    # An upstream 429 can be recorded as 0%: all-zero means unreadable, not empty.
    if max(values) <= 0:
        return None, age, "ravenline snapshot is all zero -- unreadable, not an empty pool"
    return mapping, age, None


def build_windows(mapping, now, warnings):
    """Known windows first, then any extra window the source returns."""
    keys = [k for k, _ in KNOWN if k in mapping]
    keys += [k for k in mapping if k not in dict(KNOWN)]
    windows = []
    for key in keys:
        window = mapping[key]
        if not isinstance(window, dict) or window.get("utilization") is None:
            continue
        label = dict(KNOWN).get(key, key.replace("_", " "))
        used = percent(window["utilization"])
        resets = reset_ts(window.get("resets_at"))
        expired = resets is not None and resets < now
        if used is None:
            warnings.append(f"{label}: unreadable percentage")
        if expired:
            warnings.append(f"{label} window expired {fmt_delta(now - resets)} ago -- number is not current")
        windows.append({
            "name": label,
            "used_percent": used,
            "resets_in": fmt_delta(resets - now) if resets and not expired else None,
            "expired": expired,
        })
    return windows


def collect(home=None, now=None, url=USAGE_URL, opener=None):
    home = Path(home) if home else Path.home()
    now = time.time() if now is None else now
    result = {"source": None, "plan": None, "age_minutes": None, "windows": [], "warnings": []}
    token, plan, reason = read_credentials(home, now)
    result["plan"] = plan
    if token:
        payload, reason = fetch_live(token, url=url, opener=opener)
        if payload is not None:
            windows = build_windows(payload, now, result["warnings"])
            if windows:
                result.update(source="live", age_minutes=0, windows=windows)
                return result
            reason = "live response had no usage windows"
    result["warnings"].append(f"live: {reason}")
    mapping, age, rl_reason = read_ravenline(home, now)
    if mapping is not None:
        windows = build_windows(mapping, now, result["warnings"])
        if windows:
            result.update(source="ravenline", age_minutes=round(age / 60), windows=windows)
            return result
        rl_reason = "ravenline snapshot had no usage windows"
    result["warnings"].append(f"ravenline: {rl_reason}")
    result["warnings"].append("quota is UNKNOWN -- do not treat it as empty")
    return result


def band(window):
    used = window["used_percent"]
    if window["expired"] or used is None or used >= 90:
        return RED
    return YELLOW if used >= 70 else GREEN


def bar(used, width=20):
    if used is None:
        return "?" * width
    filled = int(round(min(max(used, 0), 100) / 100 * width))
    return "#" * filled + "." * (width - filled)


def render(result, color=False):
    paint = (lambda text, code: f"{code}{text}{RESET}") if color else (lambda text, code: text)
    head = "CLAUDE"
    if result["plan"]:
        head += f"  (plan: {result['plan']})"
    if result["source"] == "live":
        head += "  [live]"
    elif result["source"]:
        head += f"  [{result['source']}, data {result['age_minutes']}m old]"
    lines = [paint(head, BOLD + CYAN)]
    if not result["windows"]:
        lines.append(paint("  no data", RED))
    width = max((len(w["name"]) for w in result["windows"]), default=0)
    for window in result["windows"]:
        used = window["used_percent"]
        shown = f"{used:>3.0f}%" if used is not None else "   ?"
        value = paint(f"{shown}  [{bar(used)}]", band(window))
        if window["expired"]:
            tail = paint("WINDOW EXPIRED", RED)
        elif window["resets_in"]:
            tail = paint(f"resets in: {window['resets_in']}", DIM)
        else:
            tail = ""
        lines.append(f"  {window['name']:<{width}}  {value}  {tail}".rstrip())
    for warning in result["warnings"]:
        lines.append(paint(f"  ! {warning}", YELLOW))
    return "\n".join(lines)


def main(argv=None, home=None, now=None, url=USAGE_URL, opener=None, out=None):
    parser = argparse.ArgumentParser(description="Claude subscription usage windows")
    parser.add_argument("--color", choices=("auto", "always", "never"), default="auto")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)
    out = out or sys.stdout
    result = collect(home=home, now=now, url=url, opener=opener)
    if args.json:
        out.write(json.dumps(result, indent=2) + "\n")
    else:
        color = args.color == "always" or (
            args.color == "auto" and hasattr(out, "isatty") and out.isatty() and not os.environ.get("NO_COLOR"))
        out.write(render(result, color=color) + "\n")
    return 0 if result["windows"] else 1


if __name__ == "__main__":
    sys.exit(main())
