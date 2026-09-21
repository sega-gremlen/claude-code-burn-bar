# AGENTS.md

Instructions for an AI coding agent asked to install, configure, or modify this
plugin. Written to be followed literally.

## What this is

Burn Bar is a Claude Code **plugin** providing a **status line**. It prints one
line showing the 5-hour rate limit, the 7-day rate limit, and the context
window usage, each as a colored bar with a percentage.

It reads the session state Claude Code writes to **stdin** as JSON. It makes no
network requests, needs no API key, and installs no dependencies.

## Installing it for a user

Do **not** clone this repo, copy files into `~/.claude/`, or hand-edit
`settings.json` to install it. Tell the user to run these two slash commands in
Claude Code, in this order:

```
/plugin marketplace add sega-gremlen/claude-code-burn-bar
/plugin install burn-bar@claude-code-burn-bar
```

The syntax is `<plugin-name>@<marketplace-name>`. Here both are fixed: the
plugin is `burn-bar` and the marketplace is `claude-code-burn-bar`.

These are **interactive slash commands typed by the user** in the Claude Code
REPL. You cannot run them with a Bash/shell tool. If you have a shell, the
non-interactive equivalent is:

```
claude plugin marketplace add sega-gremlen/claude-code-burn-bar
claude plugin install burn-bar@claude-code-burn-bar
```

### Prerequisite to check first

Python 3.10+ must be callable as `python`. Verify with `python --version`.

- If `python` is missing but `python3` works (typical on macOS/Linux), the
  plugin's own command will fail. Fix it by adding a user-level `statusLine`
  override, which takes precedence over the plugin's — see
  "Overriding the interpreter" below. Do not edit files inside the installed
  plugin directory; an update would overwrite them.
- The code uses `X | None` type syntax, so 3.10 is a hard floor.

## Configuring it

All configuration is optional and lives in **`~/.claude/burn-bar.json`**. Create
that file; do not modify files inside the plugin directory.

```json
{
  "warn_pct": 75,
  "stop_pct": 90,
  "context_warn_pct": 80,
  "context_stop_pct": 92,
  "bar_width": 5,
  "show_context": true,
  "show_reset": true
}
```

Every key is optional and merges over the defaults shown above. Types: the four
`*_pct` keys and `bar_width` are numbers; `show_context` and `show_reset` are
booleans. Unknown keys are ignored. A malformed file is ignored silently and
the defaults apply — so if a config change appears to do nothing, validate the
JSON first.

Meaning of the thresholds: a gauge is green below `warn_pct`, yellow at or
above it, red at or above `stop_pct`. The `context_*` pair does the same for
the `ctx` gauge.

### Overriding the interpreter

To use a specific Python, put a `statusLine` in the user's
`~/.claude/settings.json` (user settings win over the plugin's defaults):

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 \"$HOME/.claude/plugins/marketplaces/claude-code-burn-bar/plugins/burn-bar/bin/burn_bar.py\"",
    "padding": 0
  }
}
```

Confirm the real install path before writing this — it varies by Claude Code
version. `/plugin` in the REPL shows where a plugin lives.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Line shows only `…` | No `rate_limits` and no `context_window` in the stdin payload yet | Expected on a fresh session and for non-subscription accounts. Wait for the first request. |
| Only the `ctx` gauge appears | Claude Code sent no `rate_limits` | Expected without a subscription, or before the first request of a window. |
| Status line is blank | The command failed, or the folder is untrusted | Run the script manually (below). Status lines run shell commands, so the workspace trust prompt must be accepted first. |
| Boxes / garbled characters | Terminal font lacks block glyphs, or not UTF-8 | Use a UTF-8 terminal with a font covering `█ ▏▎▍▌▋▊▉ │`. |
| Config changes do nothing | Invalid JSON in `burn-bar.json` | Validate the file; parse errors fall back to defaults silently. |

Reproduce the output without Claude Code by feeding it a sample payload:

```bash
echo '{"rate_limits":{"five_hour":{"used_percentage":89,"resets_at":1790000000},"seven_day":{"used_percentage":58,"resets_at":1790500000}},"context_window":{"used_percentage":12}}' | python plugins/burn-bar/bin/burn_bar.py
```

`resets_at` is **unix epoch seconds**. Use future timestamps or the reset times
will read `0m`.

## Repository layout

```
.claude-plugin/marketplace.json          marketplace catalog; lists the plugin
plugins/burn-bar/.claude-plugin/plugin.json   plugin identity and version
plugins/burn-bar/settings.json           declares the statusLine command
plugins/burn-bar/bin/burn_bar.py         the whole implementation
```

This repo is both a marketplace and the plugin it ships.

## If you are modifying the code

- `burn_bar.py` is standalone: standard library only, no imports from
  elsewhere in the repo. Keep it that way — it runs as a bare script.
- It must **never** crash or hang. It runs on every status line redraw, and a
  failure shows the user a blank line. Missing and malformed fields are handled
  by returning `…`; preserve that behavior.
- It must not make network calls or read the transcript. Everything needed is
  on stdin. Earlier versions did call the API; that was removed deliberately.
- Bump `version` in **both** `plugin.json` and `marketplace.json` — they are
  separate files and both carry it.
- Keep output to a single line. A status line is one row; a newline breaks the
  display.
