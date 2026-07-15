# Agentic AI Lessons

Eight lessons building up an agentic AI system version by version.

## Setup

- Python 3.10+.
- A single `.env` file at the root of this repository, shared by every
  lesson. It should contain `ANTHROPIC_API_KEY` (required for all lessons)
  and `GOOGLE_PLACES_KEY` (required only for lessons 06-08).
- Install dependencies:
  ```
  py -m pip install anthropic python-dotenv
  ```
  Lessons 06-08 also need:
  ```
  py -m pip install googlemaps
  ```

Each lesson's own README has the exact run command and any extra setup it needs.

1. **[01-first-agentic-loop](01-first-agentic-loop/)** — The smallest possible agentic loop: two mock tools, one real decision, proving the mechanism is genuine rather than scripted.
2. **[02-visual-loop-flask](02-visual-loop-flask/)** — The same loop as lesson 1, rendered live in a browser instead of a terminal, using Flask and Server-Sent Events.
3. **[03-branching-tool-choice](03-branching-tool-choice/)** — Introduces a third, optional tool, so the number and choice of tool calls genuinely varies depending on the data.
4. **[04-failure-recovery](04-failure-recovery/)** — Introduces a tool that fails on its first call, testing whether Claude notices and decides to retry on its own.
5. **[05-human-checkpoint](05-human-checkpoint/)** — Introduces a consequential action tool that pauses and requires real human approval before anything happens.
6. **[06-real-data-google-places](06-real-data-google-places/)** — Replaces all mock data with genuine, live Google Places API calls — real businesses, real failures, real uncertainty.
7. **[07-open-ended-real-data](07-open-ended-real-data/)** — Removes the fixed checklist from lesson 6, giving Claude genuine freedom to decide what to check and when to stop.
8. **[08-html-report-and-internals](08-html-report-and-internals/)** — Adds two optional, independent toggles: a readable HTML report of the run, and full visibility into the raw, growing message list sent to Claude on every loop iteration.

Each lesson folder has its own README with setup instructions and things to try.
