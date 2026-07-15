"""
Lesson 8 — seeing the innards.

Same real tools and open-ended task as v7. The terminal log (the familiar
[Claude says] / [Tool call] / [Tool result] / DONE lines) is completely
unchanged, no matter what the two toggles below are set to.

Two independent, additive extras, controlled by the two booleans just
below the imports:

SHOW_HTML_REPORT — when True, once the run finishes, writes a static HTML
file rendering the whole run as readable cards, similar in spirit to v2's
live browser view, but built after the fact from a plain Python list of
events rather than streamed. No yield, no Flask, no live server — the run
happens exactly as normal, and a file gets written at the very end.

SHOW_MESSAGE_INTERNALS — when True, after every single change to the
`messages` list, prints the ENTIRE list, raw, exactly as it will be sent
to Claude on the next loop iteration. This is deliberately not pretty —
the point is to see precisely what's being passed back and forth, with
nothing hidden or reformatted for readability.
"""

import os
import json
import googlemaps
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
gmaps = googlemaps.Client(key=os.environ["GOOGLE_PLACES_KEY"])

# ---------------------------------------------------------------------------
# The two toggles. Flip either independently of the other.
# ---------------------------------------------------------------------------

SHOW_HTML_REPORT = True
SHOW_MESSAGE_INTERNALS = True

# ---------------------------------------------------------------------------
# Real tools — identical to v6/v7. Both genuinely call the Google Places
# API. No mock data anywhere in this script.
# ---------------------------------------------------------------------------

def check_place_profile(business_name: str) -> dict:
    search_result = gmaps.places(query=business_name)
    results = search_result.get("results", [])

    if not results:
        return {
            "business_name": business_name,
            "error": "not_found",
            "message": "No matching business was found in Google Places for this name.",
        }

    place = results[0]
    place_id = place.get("place_id")

    details = gmaps.place(place_id=place_id, fields=["website"])
    website = details.get("result", {}).get("website")

    return {
        "business_name": place.get("name"),
        "address": place.get("formatted_address"),
        "rating": place.get("rating"),
        "review_count": place.get("user_ratings_total"),
        "price_level": place.get("price_level"),
        "has_website": bool(website),
    }


def check_opening_status(business_name: str) -> dict:
    search_result = gmaps.places(query=business_name)
    results = search_result.get("results", [])

    if not results:
        return {
            "business_name": business_name,
            "error": "not_found",
            "message": "No matching business was found in Google Places for this name.",
        }

    place_id = results[0].get("place_id")
    details = gmaps.place(place_id=place_id, fields=["opening_hours", "current_opening_hours"])
    hours = details.get("result", {}).get("current_opening_hours") or details.get("result", {}).get("opening_hours")

    if not hours:
        return {
            "business_name": business_name,
            "hours_data_available": False,
            "message": "Google does not have structured opening-hours data listed for this business.",
        }

    return {
        "business_name": business_name,
        "hours_data_available": True,
        "open_now": hours.get("open_now"),
    }


TOOL_FUNCTIONS = {
    "check_place_profile": check_place_profile,
    "check_opening_status": check_opening_status,
}

TOOLS = [
    {
        "name": "check_place_profile",
        "description": (
            "Look up a real business's discoverability profile via Google "
            "Places: rating, review count, price tier, and whether it has a "
            "website listed. Call this once per business you want to assess."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"business_name": {"type": "string"}},
            "required": ["business_name"],
        },
    },
    {
        "name": "check_opening_status",
        "description": (
            "Check whether a business has real, structured opening-hours "
            "data listed with Google, and whether it's open right now. Some "
            "real listings do not have this data at all. Use your own "
            "judgement about whether this signal is worth checking for a "
            "given business."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"business_name": {"type": "string"}},
            "required": ["business_name"],
        },
    },
]

SYSTEM_PROMPT = """\
You are evaluating real businesses on how well-represented they are in
structured, publicly queryable data — the kind of data a system like an
AI assistant or shopping agent would actually be able to see and act on.

Use only the real data the tools return. Do not invent or assume facts
that weren't in a tool result. If a tool reports missing data (no website,
no hours listed, or the business wasn't found at all), treat that as
meaningful information in itself, not as a gap to quietly fill in.
"""

# ---------------------------------------------------------------------------
# Helpers for the two extras. Neither of these touches the loop's actual
# behaviour — they only observe and record what's already happening.
# ---------------------------------------------------------------------------

def _safe_serialise(obj):
    """The `messages` list contains real SDK objects (TextBlock,
    ToolUseBlock) once Claude's own replies get appended to it — these
    aren't plain dictionaries, so json.dumps can't handle them directly.
    This function is a fallback json.dumps calls automatically whenever it
    hits something it doesn't natively know how to serialise: if the
    object has a model_dump() method (the SDK's own objects do), use that
    to turn it into a plain dictionary; otherwise, just stringify it."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return str(obj)


def _record_messages_snapshot(event_log, messages):
    """Records the entire messages list, raw, exactly as it currently
    stands, into the event log for later inclusion in the HTML report.
    Deliberately not printed to the terminal — a growing, resent-in-full
    list is genuinely hard to follow scrolling past in a terminal, but
    reads fine as a static section in a browser."""
    event_log.append({
        "type": "message_snapshot",
        "content": json.dumps(messages, indent=2, default=_safe_serialise),
    })


def _build_html_report(event_log, task):
    """Builds a single static HTML file from the list of events recorded
    during the run. No live streaming — this runs once, after the loop has
    already finished, purely from data already collected."""

    rows = []
    for event in event_log:
        if event["type"] == "reasoning":
            rows.append(f'<div class="card reasoning"><div class="label">Claude reasons</div><pre>{event["content"]}</pre></div>')
        elif event["type"] == "tool_call":
            rows.append(f'<div class="card tool_call"><div class="label">Tool call {event["number"]}</div><pre>{event["name"]}({json.dumps(event["input"])})</pre></div>')
        elif event["type"] == "tool_result":
            rows.append(f'<div class="card tool_result"><div class="label">Tool result {event["number"]}</div><pre>{json.dumps(event["result"], indent=2)}</pre></div>')
        elif event["type"] == "message_snapshot":
            rows.append(f'<div class="card snapshot"><div class="label">Raw messages snapshot</div><pre>{event["content"]}</pre></div>')

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Agentic run report</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, sans-serif; background: #14161a; color: #e6e6e6;
          max-width: 780px; margin: 40px auto; padding: 0 20px; }}
  h1 {{ font-size: 20px; font-weight: 500; }}
  .task {{ padding: 14px 16px; border-radius: 10px; background: #1d1f24; border: 1px solid #3a3d44; margin-bottom: 20px; }}
  .card {{ margin-top: 14px; padding: 14px 16px; border-radius: 10px; border: 1px solid #3a3d44; background: #1d1f24; }}
  .label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }}
  .reasoning .label {{ color: #7f77dd; }}
  .tool_call .label, .tool_result .label {{ color: #5dcaa5; }}
  .snapshot {{ background: #101214; border-color: #2a2d33; }}
  .snapshot .label {{ color: #888; }}
  .snapshot pre {{ font-size: 11px; color: #aab; max-height: 400px; overflow-y: auto; }}
  pre {{ white-space: pre-wrap; font-family: ui-monospace, monospace; font-size: 13px; margin: 0; }}
</style></head>
<body>
<h1>Agentic run report</h1>
<div class="task"><div class="label">System prompt</div><pre>{SYSTEM_PROMPT}</pre></div>
<div class="task"><div class="label">Task</div><pre>{task}</pre></div>
{"".join(rows)}
</body></html>"""

    # Written into a "reports" folder, kept alongside the script. Not yet
    # timestamped — every run currently overwrites the previous report.
    os.makedirs("reports", exist_ok=True)
    path = os.path.join("reports", "run_report.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path

# ---------------------------------------------------------------------------
# The agentic loop. The core shape is identical to every earlier version —
# the two toggles only add extra observation around it, never change what
# the loop actually does.
# ---------------------------------------------------------------------------

def run_agentic_loop(task: str):
    messages = [{"role": "user", "content": task}]
    event_log = []  # only used if SHOW_HTML_REPORT is True
    tool_call_number = 0  # increments with every tool call, for readability

    print(f"\nTASK: {task}\n{'-'*60}")

    if SHOW_HTML_REPORT and SHOW_MESSAGE_INTERNALS:
        _record_messages_snapshot(event_log, messages)

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"\n[Claude says]\n{block.text.strip()}")
                event_log.append({"type": "reasoning", "content": block.text.strip()})

        if response.stop_reason != "tool_use":
            print(f"\n{'-'*60}\nDONE.")
            if SHOW_HTML_REPORT:
                path = _build_html_report(event_log, task)
                print(f"HTML report written to: {path}")
            return

        messages.append({"role": "assistant", "content": response.content})

        if SHOW_HTML_REPORT and SHOW_MESSAGE_INTERNALS:
            _record_messages_snapshot(event_log, messages)

        tool_results = []

        for block in response.content:
            if block.type == "tool_use":
                tool_call_number += 1
                fn = TOOL_FUNCTIONS[block.name]
                result = fn(**block.input)
                print(f"\n[Tool call {tool_call_number}] {block.name}({block.input})")
                print(f"[Tool result {tool_call_number}] {json.dumps(result)}")

                event_log.append({"type": "tool_call", "name": block.name, "input": block.input, "number": tool_call_number})
                event_log.append({"type": "tool_result", "name": block.name, "result": result, "number": tool_call_number})

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

        messages.append({"role": "user", "content": tool_results})

        if SHOW_HTML_REPORT and SHOW_MESSAGE_INTERNALS:
            _record_messages_snapshot(event_log, messages)


if __name__ == "__main__":
    run_agentic_loop(
        "You're assessing four Bond Street luxury flagships — Chanel, "
        "Dior, Louis Vuitton, and Brunello Cucinelli — for a discoverability "
        "consultancy. Decide for yourself what's worth checking for each "
        "business and in what order, and stop once you're confident in "
        "your overall assessment. Explain your reasoning as you go, then "
        "give your final assessment."
    )
