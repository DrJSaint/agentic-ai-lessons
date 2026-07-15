# Lesson 8 — seeing the innards

Same real tools and open-ended task as v7. The terminal log — the familiar
`[Claude says]` / `[Tool call]` / `[Tool result]` / `DONE` lines — is
completely unchanged no matter what you do with the toggles below. They
only add extra ways of watching the same run, never change what the loop
actually does.

## The toggles

Near the top of `08_html_report_and_internals.py`:

```python
SHOW_HTML_REPORT = True
SHOW_MESSAGE_INTERNALS = True
FILLED_MESSAGE_BACKGROUNDS = True
```

The terminal output is always the same regardless of any toggle: the
familiar `[Claude says]` / `[Tool call]` / `[Tool result]` / `DONE` lines
from every earlier version, plus one small addition — each tool call/result
is numbered (`[Tool call 1]`, `[Tool result 1]`, `[Tool call 2]`...) so a
longer run with many tool calls is easier to follow. The system prompt is
not printed to the terminal at all; it only appears in the HTML report,
described below. Nothing else about the terminal
ever changes, no matter how the toggles below are set.

### `SHOW_HTML_REPORT`

Once the run finishes, writes a file to `reports/run_report_08.html` at
the root of the repository — a static, readable page rendering the system
prompt, the task, and every piece of reasoning, tool call, and tool result
as cards, similar in spirit to v2's live browser view. Unlike v2, nothing
streams live here — there's no `yield`, no Flask, no server. The run
happens exactly as normal, a plain list of what happened gets built up
alongside it, and the whole file gets written once, right at the end.
Open it in any browser afterward. The path is anchored to the script's own
location, not to whatever directory you happen to run it from, so it
always lands in the same `reports` folder at the repo root regardless of
where you invoke it from; that folder is created automatically if it
doesn't already exist. The filename is unique per lesson (`run_report_08.html`
here) so different lessons' reports don't overwrite each other — running
this lesson again does overwrite its own previous report, though; reports
aren't timestamped yet.

### `SHOW_MESSAGE_INTERNALS`

Only has any effect if `SHOW_HTML_REPORT` is also `True` — on its own,
with the HTML report switched off, this toggle does nothing at all, since
there's nowhere for it to display anything.

When both are `True`, the HTML report gets an extra section for every
change to the `messages` list: the **entire** list, raw, exactly as it
stood at that point in the run. This is specifically kept out of the
terminal — a growing, resent-in-full list is genuinely hard to follow
scrolling past in a terminal, but reads fine as a static, scrollable
section in a browser. Nothing is simplified; you see precisely what
Claude receives on every loop iteration, including the full structure of
tool_use blocks and tool_result blocks, not just the tidied-up
`[Tool call]` / `[Tool result]` summary lines.

Each message in the list is rendered as its own block, alternating white
and light-blue backgrounds by its position in the list — not by which
snapshot it appears in. That means a given message keeps the same colour
every time it shows up again in a later, longer snapshot, so the message
(or messages) newly appended since the previous snapshot are immediately
obvious: they're the block(s) that continue the alternating pattern past
wherever the last snapshot's colours left off.

Fair warning: with several businesses and two tools each, this section can
get genuinely long, since the list keeps growing and gets recorded again
in full each time, not just the newest addition. That's honest, not a
bug — it's exactly how much data really is being resent to Claude on every
single loop iteration.

### `FILLED_MESSAGE_BACKGROUNDS`

Only has any visible effect if `SHOW_MESSAGE_INTERNALS` is also `True` —
it controls how the white/light-blue alternation from the section above
is actually rendered, nothing more.

- `True` (the default): each message block is filled with a white or
  light-blue background, with dark text — high-contrast zebra striping
  that's easy to scan at a glance.
- `False`: the block keeps the same dark background as the rest of the
  report, and the white/light-blue colour is applied to the text instead —
  fitting in with the report's overall dark theme rather than standing out
  from it.

Either way, the alternation itself is identical: same messages, same
colours, same positions — just filled blocks versus coloured text.

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
