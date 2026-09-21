"""
Burn Bar — a Claude Code status line showing how much budget is left.

Claude Code passes the session state as JSON on stdin, so there is no network
call and no transcript parsing here: the host has already sent both the rate
limit percentages and how full the context window is.

Output looks like:

    5h ████▍ 89% 1h 57m │ week ██▉░░ 58% 1d 23h │ ctx ▌░░░░ 12%
"""

import json
import sys
import time
from pathlib import Path

# Thresholds can be overridden per user — see README. Values are "percent
# used", so a higher number means a later warning.
DEFAULT_CONFIG = {
    "warn_pct": 75,
    "stop_pct": 90,
    "context_warn_pct": 80,
    "context_stop_pct": 92,
    "bar_width": 5,
    "show_context": True,
    "show_reset": True,
}

# Looked up in order; the first file that exists wins. The second covers a
# checkout kept anywhere, where a config next to the script is the natural
# place for it.
CONFIG_PATHS = (
    Path.home() / ".claude" / "burn-bar.json",
    Path(__file__).resolve().parent / "config.json",
)

DIM = "\033[2m"
RESET = "\033[0m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"

# An eighth-block bar: the fill is visible down to 1/8 of a cell.
BAR_BLOCKS = " ▏▎▍▌▋▊▉█"

# The empty part is drawn, not spaced: with plain spaces a mostly-empty bar
# reads as a stray tick floating in a gap, and proportional-ish terminal fonts
# make the gap width wander.
BAR_EMPTY = "░"


def load_config() -> dict:
    """Reads thresholds from the first config file found, filling in defaults."""
    config = dict(DEFAULT_CONFIG)
    for path in CONFIG_PATHS:
        try:
            if not path.exists():
                continue
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(loaded, dict):
            config.update(loaded)
        break
    return config


def color_for(percent: float, warn_pct: float, stop_pct: float) -> str:
    """Color for a value, by threshold."""
    if percent >= stop_pct:
        return RED
    if percent >= warn_pct:
        return YELLOW
    return GREEN


def bar(percent: float, width: int) -> tuple[str, str]:
    """Splits a fill bar into its (filled, empty) halves, for separate colors."""
    filled = max(0.0, min(100.0, percent)) / 100 * width
    full = int(filled)
    remainder = int((filled - full) * 8)
    cells = "█" * full
    empty = ""
    if full < width:
        # A partial cell belongs to the filled half; otherwise the whole
        # remaining run is empty.
        if remainder:
            cells += BAR_BLOCKS[remainder]
            empty = BAR_EMPTY * (width - full - 1)
        else:
            empty = BAR_EMPTY * (width - full)
    return cells, empty


def gauge(
    label: str, percent: float, warn_pct: float, stop_pct: float, width: int
) -> str:
    """Assembles "label + bar + percent" in color."""
    color = color_for(percent, warn_pct, stop_pct)
    filled, empty = bar(percent, width)
    return (
        f"{DIM}{label}{RESET} {color}{filled}{RESET}{DIM}{empty}{RESET}"
        f" {color}{percent:.0f}%{RESET}"
    )


def minutes_until(epoch_seconds: float | None) -> int | None:
    """Minutes left until a moment given as unix time."""
    if not epoch_seconds:
        return None
    try:
        left = float(epoch_seconds) - time.time()
    except (TypeError, ValueError):
        return None
    return max(0, int(left // 60))


def format_reset(minutes: int | None) -> str:
    """Compact "time left", e.g. 1d 23h / 1h 57m / 12m."""
    if minutes is None:
        return "—"
    days, rest = divmod(minutes, 24 * 60)
    hours, mins = divmod(rest, 60)
    if days:
        # Over a horizon of several days the minutes no longer matter.
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def format_statusline(session: dict, config: dict) -> str:
    """Builds the whole line from the session state Claude Code sent."""
    warn_pct = config["warn_pct"]
    stop_pct = config["stop_pct"]
    width = config["bar_width"]
    sections: list[str] = []

    limits = session.get("rate_limits") or {}

    # Both limits form one section: value, bar and time to reset side by side.
    for key, label in (("five_hour", "5h"), ("seven_day", "week")):
        window = limits.get(key) or {}
        percent = window.get("used_percentage")
        if percent is None:
            continue
        block = gauge(label, percent, warn_pct, stop_pct, width)
        if config["show_reset"]:
            minutes = minutes_until(window.get("resets_at"))
            if minutes is not None:
                block += f" {DIM}{format_reset(minutes)}{RESET}"
        sections.append(block)

    if config["show_context"]:
        context = session.get("context_window") or {}
        percent = context.get("used_percentage")
        if percent is not None:
            sections.append(
                gauge(
                    "ctx",
                    percent,
                    config["context_warn_pct"],
                    config["context_stop_pct"],
                    width,
                )
            )

    # Rate limits only reach subscribers, and only after the first request —
    # until then the line must not look broken.
    if not sections:
        return f"{DIM}…{RESET}"

    return f" {DIM}│{RESET} ".join(sections)


def main() -> None:
    """Entry point: read the session JSON on stdin, print one line."""
    # The Windows console is not UTF-8 by default, which would mangle the bar
    # and box-drawing characters.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    try:
        session = json.load(sys.stdin) or {}
    except (json.JSONDecodeError, ValueError, OSError):
        session = {}

    if not isinstance(session, dict):
        session = {}

    print(format_statusline(session, load_config()))


if __name__ == "__main__":
    main()
