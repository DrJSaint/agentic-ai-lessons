# Lesson 8 — seeing the innards

Same real tools and open-ended task as v7. The terminal log — the familiar
`[Claude says]` / `[Tool call]` / `[Tool result]` / `DONE` lines — is
completely unchanged no matter what you do with the two toggles below.
They only add extra ways of watching the same run, never change what the
loop actually does.

## The two toggles

Near the top of `08_html_report_and_internals.py`:

```python
SHOW_HTML_REPORT = True
SHOW_MESSAGE_INTERNALS = True
```

The terminal output is always the same regardless of either toggle: the
familiar `[Claude says]` / `[Tool call]` / `[Tool result]` / `DONE` lines
from every earlier version, plus two small additions — the system prompt
printed once at the very start, and each tool call/result numbered
(`[Tool call 1]`, `[Tool result 1]`, `[Tool call 2]`...) so a longer run
with many tool calls is easier to follow. Nothing else about the terminal
ever changes, no matter how the two toggles below are set.

### `SHOW_HTML_REPORT`

Once the run finishes, writes a file to `reports/run_report.html` — a
static, readable page rendering the system prompt, the task, and every
piece of reasoning, tool call, and tool result as cards, similar in spirit
to v2's live browser view. Unlike v2, nothing streams live here — there's
no `yield`, no Flask, no server. The run happens exactly as normal, a
plain list of what happened gets built up alongside it, and the whole file
gets written once, right at the end. Open it in any browser afterward. The
`reports` folder is created automatically if it doesn't already exist.
Reports aren't timestamped yet, so each run overwrites the last one.

### `SHOW_MESSAGE_INTERNALS`

Only has any effect if `SHOW_HTML_REPORT` is also `True` — on its own,
with the HTML report switched off, this toggle does nothing at all, since
there's nowhere for it to display anything.

When both are `True`, the HTML report gets an extra section for every
change to the `messages` list: the **entire** list, raw, exactly as it
stood at that point in the run, deliberately unformatted. This is
specifically kept out of the terminal — a growing, resent-in-full list is
genuinely hard to follow scrolling past in a terminal, but reads fine as a
static, scrollable section in a browser. Nothing is simplified; you see
precisely what Claude receives on every loop iteration, including the
full structure of tool_use blocks and tool_result blocks, not just the
tidied-up `[Tool call]` / `[Tool result]` summary lines.

Fair warning: with several businesses and two tools each, this section can
get genuinely long, since the list keeps growing and gets recorded again
in full each time, not just the newest addition. That's honest, not a
bug — it's exactly how much data really is being resent to Claude on every
single loop iteration.

## Setup

Same as lessons 6/7 — this lesson needs both `ANTHROPIC_API_KEY` and
`GOOGLE_PLACES_KEY`, read from the single `.env` file at the root of this
repository, shared by every lesson, plus `googlemaps` installed. Then:

```
py 08_html_report_and_internals.py
```

## What to look for

- In the HTML report's raw snapshot section (if `SHOW_MESSAGE_INTERNALS`
  is on), find the moment `"role": "assistant"` gets added — that's
  Claude's own reply, including its tool_use requests, being folded into
  the conversation exactly as described back when you first traced
  `messages.append(...)` in v1.
- Notice the messages list never shrinks — every snapshot after the first
  is strictly longer than the one before it. That's the "resend the whole
  conversation every time" behaviour, made fully visible rather than just
  described.
- In the main part of the HTML report, compare how the run reads as a
  sequence of cards versus how it read in the terminal. Same information,
  different shape — worth noticing which one makes the actual
  decision-making easier to follow.
