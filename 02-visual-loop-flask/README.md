# Lesson 2 — visual version

## Setup (run this on your own machine, not in any chat)
1. This lesson only needs `ANTHROPIC_API_KEY`, read from the single `.env`
   file at the root of this repository, shared by every lesson.
2. Install the one extra dependency:
   ```
   py -m pip install flask
   ```
3. Run:
   ```
   py app.py
   ```
4. Open http://localhost:5000 in your browser and click "Run".

## Lesson 2 scenario
Same agentic loop as lesson 1's `01_first_agentic_loop.py`, but instead of
printing to a terminal, each step streams to a webpage as a card, live, as
it happens.

The agentic loop itself (`run_agentic_loop` in `app.py`) is the same logic
as lesson 1 — same two mock tools, same reasoning, same decision. The only
change is that each step is `yield`ed as a small event instead of
`print()`ed, and a webpage listens for those events (via Server-Sent
Events) and draws a card for each one as it arrives. Tool call/result
cards are numbered (`Tool call 1`, `Tool result 1`, `Tool call 2`...), so
a run with several tool calls is easier to follow.

This is the first step toward a genuine demo: the mechanism is identical,
but now it's watchable by someone who isn't reading a terminal.

## What to watch for
The cards appearing live, one per step, as Claude works through the loop
— same order of events as lesson 1's terminal output, just rendered as
cards instead of lines. Open browser dev tools (F12) → Network tab →
click on the `/stream` request while it's running to see the raw
Server-Sent Events landing in real time, underneath the cards.

## Try this
Edit the task box before clicking Run — ask about different brands —
then click Run again and compare.
