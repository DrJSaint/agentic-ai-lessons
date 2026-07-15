# Lesson 1 — the smallest agentic loop

## What this is
Claude is asked to decide whether a fictional brand ("Lumière") would be
shortlisted by an AI shopping agent over a competitor ("Aurelio"). It has
two tools available — fake data lookups — and decides for itself whether
and in what order to use them, then gives a verdict based on what comes
back. Every step prints to the screen so you can watch it happen.

## The toggles

Near the top of `01_first_agentic_loop.py`:

```python
SHOW_HTML_REPORT = True
SHOW_MESSAGE_INTERNALS = True
FILLED_MESSAGE_BACKGROUNDS = True
```

These are the same two extras introduced in lesson 8 (`08-html-report-and-internals`),
brought forward here so they're available from the very first lesson
instead of only the last one. The terminal output described below never
changes, no matter how these are set — including the numbered
`[Tool call 1]` / `[Tool result 1]` lines, which always print regardless
of any toggle, matching lesson 8.

### `SHOW_HTML_REPORT`

Once the run finishes, writes a file to `reports/run_report_01.html` at
the root of the repository — a static, readable page rendering the task
and every piece of reasoning, tool call, and tool result as cards. The
path is anchored to the script's own location, not to whatever directory
you happen to run it from, so it always lands in the same `reports`
folder at the repo root regardless of where you invoke it from; that
folder is created automatically if it doesn't already exist. The filename
is unique to this lesson so it won't collide with any other lesson's
report. Reports aren't timestamped, so running this lesson again
overwrites its own previous report.

### `SHOW_MESSAGE_INTERNALS`

Only has any effect if `SHOW_HTML_REPORT` is also `True`. When both are
`True`, the HTML report gets an extra section for every change to the
`messages` list: the **entire** list, raw, exactly as it stood at that
point in the run. Each message in the list is rendered as its own block,
alternating white and light-blue backgrounds by its position in the list —
not by which snapshot it appears in. That means a given message keeps the
same colour every time it shows up again in a later, longer snapshot, so
whatever's newly appended since the previous snapshot is immediately
obvious: it's the block(s) that continue the alternating pattern past
wherever the last snapshot's colours left off.

### `FILLED_MESSAGE_BACKGROUNDS`

Only has any visible effect if `SHOW_MESSAGE_INTERNALS` is also `True` —
it controls how the white/light-blue alternation above is rendered.

- `True` (the default): each message block is filled with a white or
  light-blue background, with dark text.
- `False`: the block keeps the same dark background as the rest of the
  report, and the white/light-blue colour is applied to the text instead.

## Setup (run this on your own machine, not in any chat)

1. Make sure you have Python 3.10+ installed.
2. In this folder, install the dependencies:
   ```
   pip install anthropic python-dotenv
   ```
3. This lesson only needs `ANTHROPIC_API_KEY`. It's read from a single `.env`
   file at the root of this repository, shared by every lesson — open it in
   a text editor and replace `paste-your-key-here` with your real Anthropic
   API key. Nobody but your own machine ever sees this file — it's excluded
   from git via .gitignore.
4. Run it:
   ```
   py 01_first_agentic_loop.py
   ```

## What to watch for
- The `[Claude says]` lines — this is Claude reasoning, before and between
  tool calls.
- The `[Tool call N]` lines — the moment Claude decides to use a tool, and
  what input it chose to send.
- The `[Tool result N]` lines — the fake data coming back.
- The final verdict — notice it's built from the actual data returned, not
  hardcoded anywhere in the script.

## Try this
Open `01_first_agentic_loop.py` and change the numbers in `check_brand_data` or
`check_competitor_data` — e.g. give Lumière a higher review score than
Aurelio — then run it again. If the verdict flips accordingly, that's
proof the decision is genuinely happening at runtime, not scripted.
