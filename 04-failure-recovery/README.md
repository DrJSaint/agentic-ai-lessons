# Lesson 4 — real looping and failure recovery

Everything from v3 is here — three tools, the system prompt weighting review
trust against availability — plus one new tool: `check_live_stock_feed`.

This one is genuinely unreliable in a scripted, predictable way: the
**first** time it's called for a given brand, it returns an error instead
of data, exactly like a real flaky external service timing out. Only on a
**second** call does it succeed. The mechanism is deterministic (a counter,
not randomness), but Claude is only ever told "this can fail" — the same
way a real tool's documentation would tell a developer, without revealing
the internal logic behind when or why.

Nothing in the code tells Claude what to do about that. There's no retry
logic, no `try/except` that automatically calls it again. The only guidance
is one line in the system prompt: tools representing live services can fail
transiently, and Claude should use its own judgement about whether to retry
or proceed without the data.

## The toggles

Near the top of `04_failure_recovery.py`:

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

Once the run finishes, writes a file to `reports/run_report_04.html` at
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
wherever the last snapshot's colours left off. This is a particularly
useful lens on this lesson specifically: the retry (if Claude does one)
shows up as a second `check_live_stock_feed` tool call/result pair, and
the messages snapshots make it unambiguous exactly what error text Claude
saw before deciding whether to retry.

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
py 04_failure_recovery.py
```

## What to watch for

This is the first version where the number of loop iterations can genuinely
vary based on something going wrong, not just based on which tools are
relevant. Watch for:

- Does Claude retry the failed call, or does it give up after the first
  timeout and reason without the stock data?
- If it retries, does it say why? Does it treat the error as "transient and
  worth another try," matching the hint in the system prompt?
- If it doesn't retry, does it acknowledge the gap in its final verdict, or
  does it quietly proceed as if the missing data didn't matter?

## Try this

Run it several times in a row. Because the failure is deterministic per
brand (first call fails, second succeeds) but the *decision to retry* is
Claude's own judgement each time, you may see it behave differently across
runs even though the underlying failure pattern never changes. That gap —
between a predictable failure and an unpredictable response to it — is
worth sitting with. It's the clearest version yet of the difference between
your code (which only ever does what you wrote) and Claude's reasoning
(which decides what to do about what your code reports).

You can also try editing `check_live_stock_feed` so it fails twice before
succeeding, or fails permanently, and see whether Claude eventually gives
up and reasons without it, and how it frames that gap in its verdict.
