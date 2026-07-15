# Lesson 5 — the human checkpoint

Everything from v4 is here, plus one new tool that's different in kind, not
just in number: `draft_partnership_outreach`.

Every tool before this one only *observes* — it looks something up and
reports back, and nothing in the world changes as a result. This tool
*acts* — it proposes sending a real message to a real brand. That's the
observe-vs-act line from the layered approach document, built into actual
code for the first time.

## What's different about this tool

When Claude calls `draft_partnership_outreach`, the function does not send
anything. It stops, prints exactly what Claude wants to send, and waits for
you — a real human, typing into the terminal — to approve or decline it.

Whatever you decide gets reported back to Claude as a genuine tool result,
the same way any other tool's output would be. If you decline, Claude sees
`"status": "declined"` and has to continue reasoning from there — it can't
assume the message went out just because it asked to send it.

## The toggles

Near the top of `05_human_checkpoint.py`:

```python
SHOW_HTML_REPORT = True
SHOW_MESSAGE_INTERNALS = True
FILLED_MESSAGE_BACKGROUNDS = True
```

The same two extras introduced in lesson 8 (`08-html-report-and-internals`),
brought forward here.

One thing specific to this lesson: the terminal deliberately suppresses
the generic `[Tool call]`/`[Tool result]` lines for `draft_partnership_outreach`,
since that tool already prints its own human-checkpoint dialog and printing
both would just be noise. That suppression is terminal-only — the HTML
report below still captures that tool call and its result (approved or
declined) in full, so the report stays a complete, traceable record of
everything that happened even when the terminal deliberately shows less.
Whenever the generic lines do print, tool calls/results are numbered
(`[Tool call 1]`, `[Tool result 1]`, `[Tool call 2]`...), matching lesson 8
— the counter still increments for the suppressed tool too, so its number
in the report stays consistent with the others.

### `SHOW_HTML_REPORT`

Once the run finishes, writes a file to `reports/run_report_05.html` at
the root of the repository — a static, readable page rendering the system
prompt, the task, and every piece of reasoning, tool call, and tool result
as cards, including the human-checkpoint tool call the terminal hides. The
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

## Setup

This lesson only needs `ANTHROPIC_API_KEY`, read from the single `.env` file
at the root of this repository, shared by every lesson. Then:

```
py 05_human_checkpoint.py
```

When the checkpoint appears, read what's being proposed before answering.
Try approving it once, then run the script again and decline it, to see
how Claude's final verdict differs depending on your answer.

## What to watch for

- Does Claude only propose outreach when it's found something genuinely
  specific and actionable, or does it reach for the tool speculatively?
  The system prompt asks it not to — worth checking whether it actually
  holds to that.
- When you decline, does Claude's final verdict acknowledge that the
  message wasn't sent, or does it quietly write as if it had been?
- Notice that every other tool in this script runs without asking you
  anything. Only this one stops and waits. That asymmetry is deliberate —
  it's the whole point of the exercise.

## Try this

Edit the system prompt to remove the line about the human review process
entirely, and see whether Claude still treats the tool with the same
caution, or starts proposing outreach more readily. That tells you how
much of the tool's careful use was coming from the explicit instruction
versus Claude's own sense that a consequential action deserves care.
