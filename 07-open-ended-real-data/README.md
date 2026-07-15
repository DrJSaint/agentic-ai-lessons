# Lesson 7 — real data, genuinely open-ended

Same two real tools as v6 — no mock data. What's different is the task
itself.

## Why this version exists

v6 asked for a fixed checklist across two businesses: check rating, review
count, price tier, website, and opening hours, for both. That was fully
specified — Claude had nothing left to decide except the order to run the
calls in, and it ran everything in a single, efficient pass.

v7 removes the checklist. The task says: assess four real Bond Street
luxury flagships, decide for yourself what's worth checking for each one
and in what order, and stop once you're confident. Nothing forces a fixed
number of tool calls, and nothing guarantees interesting branching — this
version is genuinely testing whether real ambiguity produces different
behaviour than a fixed task did, not proving that it always will.

## The four businesses

Chanel, Dior, and Louis Vuitton are all famous, high-footfall flagships,
likely to have rich, complete Google listings. Brunello Cucinelli is a
real flagship too, but a quieter, smaller brand — plausibly (not
certainly) thinner on structured data. Nothing is scripted to make this
happen; it's a real business that might turn out that way, giving Claude
an honest chance to hit something worth reacting to mid-run.

## System prompt vs user prompt — the split in this version

The **system prompt** only contains standing rules that would make sense
attached to this agent no matter what task it's given: use only real tool
data, never invent facts, treat missing data as meaningful rather than a
gap to fill in quietly.

The **user prompt** (the task, at the bottom of the script) contains
everything about *how open-ended this particular exercise is* — deciding
what to check, deciding when to stop. That's deliberately not in the
system prompt, because it's specific to this experiment. Rewriting how
open-ended a task is should mean editing the task, not the agent's
standing rules.

## The toggles

Near the top of `07_open_ended_real_data.py`:

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

Once the run finishes, writes a file to `reports/run_report_07.html` at
the root of the repository — a static, readable page rendering the system
prompt, the task, and every piece of reasoning, tool call, and tool result
as cards. Since this lesson is open-ended, a single run can generate quite
a few cards across all four businesses — the report is a genuinely useful
way to review the whole path Claude took after the fact, not just what
scrolled past in the terminal. The path is anchored to the script's own
location, not to whatever directory you happen to run it from, so it
always lands in the same `reports` folder at the repo root regardless of
where you invoke it from; that folder is created automatically if it
doesn't already exist. The filename is unique to this lesson so it won't
collide with any other lesson's report. Reports aren't timestamped, so
running this lesson again overwrites its own previous report.

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

Same as lesson 6 — this lesson needs both `ANTHROPIC_API_KEY` and
`GOOGLE_PLACES_KEY`, read from the single `.env` file at the root of this
repository, shared by every lesson. Then:

```
py 07_open_ended_real_data.py
```

## What to watch for

- How many businesses does it actually check, out of the four available?
  Does it check all four, or decide partway through that it has enough?
- Does it call both tools for every business, or skip `check_opening_status`
  for some of them if it decides that signal isn't relevant?
- If Brunello Cucinelli's data does come back thinner than the others,
  does Claude notice and react to that explicitly, or just report it
  flatly alongside the rest?
- Compare the shape of this run to v6's. Is it genuinely less "one-pass,"
  or does Claude still end up checking everything anyway, just because
  that happens to be the thorough thing to do?

## Try this

Run it more than once. Because this task is genuinely open-ended, and the
underlying data is real, you may see real variation between runs — not
just in wording, but in which businesses get checked with which tools, and
in what order. That variation, if you see it, is worth treating as data in
itself: it's the clearest possible evidence that the decision-making is
real, not scripted.
