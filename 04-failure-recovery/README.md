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
