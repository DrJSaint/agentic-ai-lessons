# Lesson 5 — the human checkpoint

## Setup (run this on your own machine, not in any chat)
This lesson only needs `ANTHROPIC_API_KEY`, read from the single `.env`
file at the root of this repository, shared by every lesson. Then:
```
py 05_human_checkpoint.py
```

When the checkpoint appears, read what's being proposed before answering.
Try approving it once, then run the script again and decline it, to see
how Claude's final verdict differs depending on your answer.

Near the top of the script are three toggles — `SHOW_HTML_REPORT`,
`SHOW_MESSAGE_INTERNALS`, `FILLED_MESSAGE_BACKGROUNDS` — that write an
optional HTML report of the run to `reports/run_report_05.html`, including
a view of the raw, growing message list. See the top-level README for the
full explanation; none of them change the terminal output described below.

One thing specific to this lesson: the terminal deliberately suppresses
the generic `[Tool call]`/`[Tool result]` lines for
`draft_partnership_outreach`, since that tool already prints its own
human-checkpoint dialog and printing both would just be noise. That
suppression is terminal-only — the HTML report still captures that tool
call and its result (approved or declined) in full, numbered the same as
every other tool call, so the report stays a complete, traceable record
of everything that happened even when the terminal deliberately shows
less.

## Lesson 5 scenario
Everything from v4 is here, plus one new tool that's different in kind,
not just in number: `draft_partnership_outreach`.

Every tool before this one only *observes* — it looks something up and
reports back, and nothing in the world changes as a result. This tool
*acts* — it proposes sending a real message to a real brand. That's the
observe-vs-act line from the layered approach document, built into actual
code for the first time.

When Claude calls `draft_partnership_outreach`, the function does not
send anything. It stops, prints exactly what Claude wants to send, and
waits for you — a real human, typing into the terminal — to approve or
decline it.

Whatever you decide gets reported back to Claude as a genuine tool
result, the same way any other tool's output would be. If you decline,
Claude sees `"status": "declined"` and has to continue reasoning from
there — it can't assume the message went out just because it asked to
send it.

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
