# Lesson 6 — real data

Every earlier version used invented data. This one doesn't. Both tools make
genuine calls to the Google Places API and return only fields that are
actually real.

## Why the scenario changed

The original "AI shopping agent shortlisting" scenario relied on two
invented signals — `has_availability_api` and `has_structured_pricing` —
that don't correspond to anything a real API can tell you. Bolting real
Google Places data onto that scenario would have meant mixing real numbers
with fictional ones, which defeats the point of this version.

Instead, the task changed to something real data can honestly answer:
**how well-represented is a real business in structured, publicly
queryable data** — rating, review count, price tier, website presence, and
live opening-hours status. That's a genuine, answerable question, using
only fields Google Places actually provides.

## The toggles

Near the top of `06_real_data_google_places.py`:

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

Once the run finishes, writes a file to `reports/run_report_06.html` at
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

This lesson needs both `ANTHROPIC_API_KEY` and `GOOGLE_PLACES_KEY`, read from
the single `.env` file at the root of this repository, shared by every
lesson. Install the one extra dependency:

```
py -m pip install googlemaps
```

Then run:

```
py 06_real_data_google_places.py
```

## What's genuinely different from every earlier version

- **The data is real.** Whatever comes back is whatever Google Places
  actually has on file, right now, for a real business.
- **Failures are real, not scripted.** If a business name doesn't match
  anything, or has no hours data listed, that's an honest limitation of
  the real listing — not a rehearsed failure like v4's stock feed, which
  was engineered to fail exactly once.
- **You don't know the outcome in advance.** Every earlier version, you
  could predict the verdict because you controlled the data. Here, you
  genuinely don't know what Chanel's or Dior's current rating and review
  count are until the tool call comes back.

## Try this

Run it with a business name that's likely to fail — something obscure or
misspelled — and see how `check_place_profile` reports the not-found case,
and how Claude reasons when a real gap in the data shows up rather than an
invented one. Try comparing two businesses you already have a strong
intuition about, and see whether the real data confirms or challenges what
you expected.
