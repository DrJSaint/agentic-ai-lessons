# Lesson 1, v2 — visual version

Same agentic loop as `shortlist_demo.py`, but instead of printing to a
terminal, each step streams to a webpage as a card, live, as it happens.

## Setup

1. Copy your `.env` file from the v1 folder into this one (same key, same format).
2. Install the one extra dependency:
   ```
   py -m pip install flask
   ```
3. Run:
   ```
   py app.py
   ```
4. Open http://localhost:5000 in your browser and click "Run".

## What's different from v1

The agentic loop itself (`run_loop` in `app.py`) is the same logic as
`shortlist_demo.py` — same two mock tools, same reasoning, same decision.
The only change is that each step is `yield`ed as a small event instead of
`print()`ed, and a webpage listens for those events (via Server-Sent Events)
and draws a card for each one as it arrives.

This is the first step toward a genuine demo: the mechanism is identical,
but now it's watchable by someone who isn't reading a terminal.

## Try this
- Edit the task box before clicking Run — ask about different brands.
- Open browser dev tools (F12) → Network tab → click on the `/stream`
  request while it's running to see the raw events landing in real time.
