# Lesson 7 — real data, genuinely open-ended

## Setup (run this on your own machine, not in any chat)
Same as lesson 6 — this lesson needs both `ANTHROPIC_API_KEY` and
`GOOGLE_PLACES_KEY`, read from the single `.env` file at the root of this
repository, shared by every lesson. Then:
```
py 07_open_ended_real_data.py
```

Near the top of the script are three toggles — `SHOW_HTML_REPORT`,
`SHOW_MESSAGE_INTERNALS`, `FILLED_MESSAGE_BACKGROUNDS` — that write an
optional HTML report of the run to `reports/run_report_07.html`, including
a view of the raw, growing message list. Since this lesson is open-ended,
a single run can generate quite a few cards across all four businesses —
the report is a genuinely useful way to review the whole path Claude took
after the fact, not just what scrolled past in the terminal. See the
top-level README for the full explanation; none of them change the
terminal output described below.

## Lesson 7 scenario
Same two real tools as v6 — no mock data. What's different is the task
itself.

v6 asked for a fixed checklist across two businesses: check rating,
review count, price tier, website, and opening hours, for both. That was
fully specified — Claude had nothing left to decide except the order to
run the calls in, and it ran everything in a single, efficient pass.

v7 removes the checklist. The task says: assess four real Bond Street
luxury flagships, decide for yourself what's worth checking for each one
and in what order, and stop once you're confident. Nothing forces a fixed
number of tool calls, and nothing guarantees interesting branching — this
version is genuinely testing whether real ambiguity produces different
behaviour than a fixed task did, not proving that it always will.

Chanel, Dior, and Louis Vuitton are all famous, high-footfall flagships,
likely to have rich, complete Google listings. Brunello Cucinelli is a
real flagship too, but a quieter, smaller brand — plausibly (not
certainly) thinner on structured data. Nothing is scripted to make this
happen; it's a real business that might turn out that way, giving Claude
an honest chance to hit something worth reacting to mid-run.

The **system prompt** only contains standing rules that would make sense
attached to this agent no matter what task it's given: use only real tool
data, never invent facts, treat missing data as meaningful rather than a
gap to fill in quietly. The **user prompt** (the task, at the bottom of
the script) contains everything about *how open-ended this particular
exercise is* — deciding what to check, deciding when to stop. That's
deliberately not in the system prompt, because it's specific to this
experiment. Rewriting how open-ended a task is should mean editing the
task, not the agent's standing rules.

## What to watch for
- How many businesses does it actually check, out of the four available?
  Does it check all four, or decide partway through that it has enough?
- Does it call both tools for every business, or skip
  `check_opening_status` for some of them if it decides that signal isn't
  relevant?
- If Brunello Cucinelli's data does come back thinner than the others,
  does Claude notice and react to that explicitly, or just report it
  flatly alongside the rest?
- Compare the shape of this run to v6's. Is it genuinely less
  "one-pass," or does Claude still end up checking everything anyway,
  just because that happens to be the thorough thing to do?

## Try this
Run it more than once. Because this task is genuinely open-ended, and the
underlying data is real, you may see real variation between runs — not
just in wording, but in which businesses get checked with which tools,
and in what order. That variation, if you see it, is worth treating as
data in itself: it's the clearest possible evidence that the
decision-making is real, not scripted.
