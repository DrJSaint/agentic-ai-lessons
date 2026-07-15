# Agentic AI Lessons

Seven lessons building up an agentic AI system version by version.

## Setup

- Python 3.10+.
- A single `.env` file at the root of this repository, shared by every
  lesson. It should contain `ANTHROPIC_API_KEY` (required for all lessons)
  and `GOOGLE_PLACES_KEY` (required only for lessons 06-07).
- Install dependencies:
  ```
  py -m pip install anthropic python-dotenv
  ```
  Lessons 06-07 also need:
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

Each lesson folder has its own README with setup instructions and things to try.

## Observability toggles

Every lesson from lesson 1 onwards (except the Flask one, which streams
live to a browser instead) has three booleans near the top of its script:

- `SHOW_HTML_REPORT` — once the run finishes, writes a static HTML report
  of the whole run — reasoning, tool calls, tool results — as readable
  cards, to `reports/run_report_NN.html` at the root of this repository.
- `SHOW_MESSAGE_INTERNALS` — only has an effect if `SHOW_HTML_REPORT` is
  also on. Adds a section to the report for every change to the `messages`
  list: the entire list, raw, exactly as it will be sent to Claude on the
  next loop iteration. Each message is coloured by its position in the
  list, so whatever's newly appended since the last snapshot is obvious at
  a glance.
- `FILLED_MESSAGE_BACKGROUNDS` — only has an effect if
  `SHOW_MESSAGE_INTERNALS` is also on. Switches the message colouring
  between filled white/light-blue backgrounds (default) or coloured text
  on the existing dark background.

Tool calls and results are also numbered everywhere they appear — terminal,
HTML report, and lesson 2's live browser cards — so a run with several
tool calls is easy to follow. None of this changes what any lesson's loop
actually does; it only changes how much of it you can see afterward.
