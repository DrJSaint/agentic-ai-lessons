# Lesson 1 — the smallest agentic loop

## What this is
Claude is asked to decide whether a fictional brand ("Lumière") would be
shortlisted by an AI shopping agent over a competitor ("Aurelio"). It has
two tools available — fake data lookups — and decides for itself whether
and in what order to use them, then gives a verdict based on what comes
back. Every step prints to the screen so you can watch it happen.

## Setup (run this on your own machine, not in any chat)

1. Make sure you have Python 3.10+ installed.
2. In this folder, install the dependencies:
   ```
   pip install anthropic python-dotenv
   ```
3. Open `.env` in a text editor and replace `paste-your-key-here` with your
   real Anthropic API key. Nobody but your own machine ever sees this file —
   it's excluded from git via .gitignore if you later put this in a repo.
4. Run it:
   ```
   python shortlist_demo.py
   ```

## What to watch for
- The `[Claude says]` lines — this is Claude reasoning, before and between
  tool calls.
- The `[Tool call]` lines — the moment Claude decides to use a tool, and
  what input it chose to send.
- The `[Tool result]` lines — the fake data coming back.
- The final verdict — notice it's built from the actual data returned, not
  hardcoded anywhere in the script.

## Try this
Open `shortlist_demo.py` and change the numbers in `check_brand_data` or
`check_competitor_data` — e.g. give Lumière a higher review score than
Aurelio — then run it again. If the verdict flips accordingly, that's
proof the decision is genuinely happening at runtime, not scripted.
