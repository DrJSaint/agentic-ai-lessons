# Lesson 3 — a genuine branch

Same loop as v1, but with a THIRD tool — `check_review_authenticity` — that
Claude only needs to call sometimes, not always. This is the first version
where the *number* and *choice* of tool calls can genuinely vary, not just
their order.

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
