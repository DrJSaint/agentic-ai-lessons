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

## Setup

You'll need `GOOGLE_PLACES_KEY` in your `.env`, alongside `ANTHROPIC_API_KEY`.
Install the one extra dependency:

```
py -m pip install googlemaps
```

Then run:

```
py shortlist_demo_v6.py
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
