# Lesson 3 — a genuine branch

Same loop as v1, but with a THIRD tool — `check_review_authenticity` — that
Claude only needs to call sometimes, not always. This is the first version
where the *number* and *choice* of tool calls can genuinely vary, not just
their order.

## The toggles

Near the top of `03_branching_tool_choice.py`:

```python
SHOW_HTML_REPORT = True
SHOW_MESSAGE_INTERNALS = True
FILLED_MESSAGE_BACKGROUNDS = True
```

The same two extras introduced in lesson 8 (`08-html-report-and-internals`),
brought forward here. The terminal output described below never changes,
no matter how these are set — including the numbered `[Tool call 1]` /
`[Tool result 1]` lines, which always print regardless of any toggle,
matching lesson 8.

### `SHOW_HTML_REPORT`

Once the run finishes, writes a file to `reports/run_report_03.html` at
the root of the repository — a static, readable page rendering the system
prompt, the task, and every piece of reasoning, tool call, and tool result
as cards. The path is anchored to the script's own location, not to
whatever directory you happen to run it from, so it always lands in the
same `reports` folder at the repo root regardless of where you invoke it
from; that folder is created automatically if it doesn't already exist.
The filename is unique to this lesson so it won't collide with any other
lesson's report. Reports aren't timestamped, so running this lesson again
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
py 03_branching_tool_choice.py
```

## What's different from v1

`check_brand_data` and `check_competitor_data` now return different data
depending on which brand name is passed in. Two brands are wired up:

- **Lumière** — a high average score (4.7) but a suspiciously low review
  count (23). Worth double-checking.
- **Solenne** — a lower average score (4.3) but a large, healthy review
  count (1,560). Nothing to double-check.

The third tool, `check_review_authenticity`, is described to Claude as
*optional* — useful only if the review data looks thin or worth verifying,
not a required step. Whether Claude reaches for it depends on what the
first two tools return, not on anything hardcoded in the script.

## Try this

Run it as-is first. Watch whether Claude calls the third tool for Lumière
(thin review count) — it's reasoning about *when* to reach for it, based
on the actual numbers, not because the script forces it to.

Then edit the task at the bottom of the file to compare **Solenne vs
Lumière** (swap which one is "the brand" vs "the competitor") and run
again. If Claude skips the third tool this time — because it's now
checking a brand with solid review numbers — that's your proof the branch
is real: same script, same tools available, different path taken, because
the decision depends on the data, not on the code.

You can also try asking about two brands with *both* thin review counts,
or both healthy ones, to see whether Claude calls the third tool zero,
one, or two times in the same run.
