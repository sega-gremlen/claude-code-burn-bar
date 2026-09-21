# AGENTS.md

Instructions for an AI agent asked to install, configure, or modify Burn Bar.
Written to be followed literally, and to stand alone if this file is all you
were given.

## What this is

Burn Bar is a Claude Code **status line**: one line under the prompt showing the
5-hour rate limit, the 7-day rate limit, and the context window, each as a
colored bar with a percentage.

It is a single Python file, standard library only. It reads the session state
Claude Code writes to **stdin** as JSON. No network calls, no API key, no
credentials, nothing to build.

**It is not a plugin.** Claude Code plugins cannot provide a main status line —
a plugin's `settings.json` only honors `agent` and `subagentStatusLine`, and a
`statusLine` key there is silently ignored. Do not try to install this with
`/plugin install`; it would copy files and change nothing.

## Installing it

Two steps: put the script on disk, then point `statusLine` at it.

### Step 1 — download the script

```bash
curl -fsSL -o ~/.claude/burn_bar.py \
  https://raw.githubusercontent.com/sega-gremlen/claude-code-burn-bar/main/burn_bar.py
```

On Windows PowerShell:

```powershell
curl.exe -fsSL -o "$env:USERPROFILE\.claude\burn_bar.py" `
  https://raw.githubusercontent.com/sega-gremlen/claude-code-burn-bar/main/burn_bar.py
```

`~/.claude/` is the suggested home; anywhere readable works, as long as the
path in step 2 matches.

### Step 2 — add the status line to the user's settings

Edit **`~/.claude/settings.json`** (create it as `{}` if absent) and add the
`statusLine` key, **preserving every other key already in the file**. Read the
file, add one key, write it back — never overwrite it wholesale:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python -X utf8 ~/.claude/burn_bar.py",
    "padding": 0
  }
}
```

It takes effect on save. No restart needed.

### Before you finish, check these

- **Python 3.10+** must exist. Verify with `python --version`. If the binary is
  `python3`, use `python3` in the command — the code uses `X | None` syntax, so
  3.10 is a hard floor.
- **The user may already have a `statusLine`.** If so, do not silently replace
  it: say what is there now and ask before overwriting.
- **Windows: forward slashes only.** Claude Code runs status line commands
  through Git Bash, which eats backslashes as escapes and then fails silently.
  Write `~/.claude/burn_bar.py` or `C:/Users/name/.claude/burn_bar.py`, never
  `C:\Users\...`. Do not use `${CLAUDE_PLUGIN_ROOT}` or other `${VAR}` syntax —
  it is not expanded here.
- **Verify it runs** before declaring success:

  ```bash
  echo '{"rate_limits":{"five_hour":{"used_percentage":50,"resets_at":9999999999}},"context_window":{"used_percentage":20}}' | python -X utf8 ~/.claude/burn_bar.py
  ```

  Expected: one line like `5h ██▌░░ 50% ... │ ctx █░░░░ 20%`. `resets_at` is
  unix epoch seconds; a past timestamp reads as `0m`.

## Configuring it

All optional, in **`~/.claude/burn-bar.json`** (not in `settings.json`):

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

Every key is optional and merges over those defaults. The four `*_pct` keys and
`bar_width` are numbers; `show_context` and `show_reset` are booleans. Unknown
keys are ignored. A malformed file is ignored silently and the defaults apply —
so if a config change seems to do nothing, validate the JSON first.

A gauge is green below `warn_pct`, yellow at or above it, red at or above
`stop_pct`. The `context_*` pair does the same for the `ctx` gauge.

The script also reads `config.json` sitting next to itself, as a fallback for a
checkout-based install.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Line shows only `…` | No `rate_limits` and no `context_window` in the payload yet | Expected on a fresh session and without a subscription. Wait for the first request. |
| Only the `ctx` gauge | Claude Code sent no `rate_limits` | Same cause; expected. |
| Line is blank | Command failed, bad path, or untrusted folder | Run the script by hand (above). Check forward slashes on Windows. Status lines need the workspace trust prompt accepted. |
| Boxes / garbled characters | Font lacks block glyphs, or terminal is not UTF-8 | Use a UTF-8 terminal with a font covering `█ ▏▎▍▌▋▊▉ ░ │`. |
| Config changes do nothing | Invalid JSON in `burn-bar.json` | Validate it; parse errors fall back to defaults silently. |

`claude --debug` logs the exit code and stderr of the first status line run.

## Uninstalling

Remove the `statusLine` block from `~/.claude/settings.json` and delete
`~/.claude/burn_bar.py` (and `~/.claude/burn-bar.json` if it was created).

## If you are modifying the code

- `burn_bar.py` is standalone: standard library only, no imports from
  elsewhere in the repo. Keep it that way — it runs as a bare script.
- It must **never** crash or hang. It runs on every status line redraw, and a
  failure shows the user a blank line. Missing and malformed fields are handled
  by returning `…`; preserve that.
- It must not make network calls or read the transcript. Everything it needs
  arrives on stdin. An earlier version did call the usage API; that was removed
  deliberately, so the script never touches credentials.
- Keep output to a single line. A status line is one row; a newline breaks the
  display.
