# Burn Bar

A Claude Code status line that shows how much of your budget is left before you
stop being able to work.

![Burn Bar](docs/burn-bar.png)

And where it lives — one line under the prompt:

![Burn Bar in Claude Code](docs/in-terminal.png)

Three gauges, left to right:

| Gauge  | What it is                                          |
| ------ | --------------------------------------------------- |
| `5h`   | the 5-hour rate limit, and when it resets            |
| `week` | the 7-day rate limit, and when it resets             |
| `ctx`  | how full the current session's context window is     |

Each gauge is a bar, a percentage, and (for the rate limits) the time left
until that window resets. The bar fills in eighths of a cell, so small changes
are still visible at five characters wide.

Colors follow thresholds: **green** below the warning level, **yellow** past
it, **red** past the stop level. Defaults are 75% / 90% for the rate limits and
80% / 92% for the context window — the context is allowed to run hotter because
filling it is harmless, autocompact just kicks in.

It is one Python file with no dependencies. It makes no network calls and reads
no credentials — Claude Code hands it the session state on stdin, and that is
all it needs.

## Install

Two ways. Both end with the same two things: the script somewhere on disk, and
a `statusLine` entry pointing at it.

### Let Claude install it

Paste this to Claude Code:

```
Install the Burn Bar status line by following
https://raw.githubusercontent.com/sega-gremlen/claude-code-burn-bar/main/AGENTS.md
```

It will fetch the file, download the script, and edit your settings.

### Do it yourself

Download the script:

```bash
curl -fsSL -o ~/.claude/burn_bar.py \
  https://raw.githubusercontent.com/sega-gremlen/claude-code-burn-bar/main/burn_bar.py
```

<details>
<summary>Windows PowerShell</summary>

```powershell
curl.exe -fsSL -o "$env:USERPROFILE\.claude\burn_bar.py" `
  https://raw.githubusercontent.com/sega-gremlen/claude-code-burn-bar/main/burn_bar.py
```
</details>

Then add this to `~/.claude/settings.json`, keeping whatever else is already in
the file:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python -X utf8 ~/.claude/burn_bar.py",
    "padding": 0
  }
}
```

The line appears as soon as you save — no restart needed.

Requires **Python 3.10+**. If yours is called `python3` rather than `python`,
use that in the command.

### Windows note

Write the path with **forward slashes**. Claude Code runs the status line
through Git Bash, which treats backslashes as escape characters, and the
command fails silently. `~` works and expands to your home directory.

### Why not a plugin?

Claude Code plugins cannot ship a main status line — a plugin's `settings.json`
only supports `agent` and `subagentStatusLine`, and a `statusLine` key there is
silently ignored. So the status line has to be configured in your own settings,
whatever installs the script.

## Configuration

Everything is optional. Create `~/.claude/burn-bar.json`:

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

| Key                 | Default | Meaning                                             |
| ------------------- | ------- | --------------------------------------------------- |
| `warn_pct`          | `75`    | rate-limit percentage that turns the gauge yellow    |
| `stop_pct`          | `90`    | rate-limit percentage that turns the gauge red       |
| `context_warn_pct`  | `80`    | context percentage that turns `ctx` yellow           |
| `context_stop_pct`  | `92`    | context percentage that turns `ctx` red              |
| `bar_width`         | `5`     | bar width in characters                              |
| `show_context`      | `true`  | show the `ctx` gauge at all                          |
| `show_reset`        | `true`  | show the time until each rate limit resets           |

Only the keys you set are overridden; the rest keep their defaults.

## Notes

**The rate limit gauges need a subscription and appear after the first
request.** Claude Code only sends `rate_limits` once it has them, so on a fresh
session the line may briefly show just `ctx`, or a single `…` before any data
arrives. That is expected, not a failure.

**To turn it off**, remove the `statusLine` block from your settings.

**Terminal requirements:** a UTF-8 capable terminal with a font that has block
characters (`█ ▏▎▍▌▋▊▉ ░`) and the box-drawing `│`. Any modern terminal
qualifies. On Windows the script forces UTF-8 output itself.

### If the line does not appear

Run the script by hand with a sample payload — it should print one line:

```bash
echo '{"rate_limits":{"five_hour":{"used_percentage":50,"resets_at":9999999999}},"context_window":{"used_percentage":20}}' | python -X utf8 ~/.claude/burn_bar.py
```

If that works but the status line stays blank, start Claude Code with
`claude --debug`, which logs the exit code and stderr of the first status line
run. Also check that you accepted the workspace trust prompt — status lines
execute a command, so they stay off in an untrusted folder.

## License

MIT
