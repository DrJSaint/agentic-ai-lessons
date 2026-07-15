"""
Lesson 6 — real data.

Every earlier version used invented data: fictional brands, fictional review
ratios, a fictional "availability API" flag that no real system actually
has. This version drops all of that. Both tools here make genuine calls to
the Google Places API and return only fields that are actually real:
- a business's real star rating and real review count
- its real price tier, if Google has one on file
- whether it genuinely has a website listed
- its real, live opening-hours status

Nothing is scripted to fail or succeed on a schedule. If a business isn't
found, or has no hours data, that's a genuine limitation of what's publicly
listed — not a rehearsed failure like v4's stock feed.

The scenario has changed to match what real data can honestly answer:
comparing two real businesses on how well-represented they are in
structured, queryable data — not "AI shopping agent shortlisting," which
was never something Google Places could genuinely speak to.

Every step is printed so you can watch the loop happen — that terminal
output never changes, no matter how the toggles below are set. Tool
calls/results are numbered (`[Tool call 1]`, `[Tool result 1]`, `[Tool
call 2]`...), matching lesson 8, so a run with several tool calls is
easier to follow in both the terminal and the HTML report.

Independent, additive extras, controlled by the booleans just below the
imports. These are the same two extras introduced in lesson 8, brought
forward here so they're available this early too:

SHOW_HTML_REPORT — when True, once the run finishes, writes a static HTML
file rendering the whole run as readable cards. No live streaming — the
run happens exactly as normal, and a file gets written at the very end.

SHOW_MESSAGE_INTERNALS — when True, after every single change to the
`messages` list, records the ENTIRE list, raw, exactly as it will be sent
to Claude on the next loop iteration. In the HTML report, each message is
rendered as its own block, alternately coloured white/light blue by its
position in the list — so a message's colour never changes between
snapshots, and whatever's been newly appended since the last snapshot is
immediately visible as the block(s) continuing the pattern past where it
last left off.

FILLED_MESSAGE_BACKGROUNDS — only has any visible effect when
SHOW_MESSAGE_INTERNALS is also True. When True (the default), each message
block is filled with a white or light-blue background, with dark text.
When False, the block keeps the same dark background as the rest of the
report, and the white/light-blue colour is applied to the text instead.
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
# The toggles. Flip any of these independently of the others.
# ---------------------------------------------------------------------------

SHOW_HTML_REPORT = True
SHOW_MESSAGE_INTERNALS = True
FILLED_MESSAGE_BACKGROUNDS = True

# ---------------------------------------------------------------------------
# Real tools — both genuinely call the Google Places API. No mock data.
# ---------------------------------------------------------------------------

def check_place_profile(business_name: str) -> dict:
    """Real Google Places Text Search plus a Details call for the website
    field. Returns actual rating, review count, price tier, and whether a
    website is listed — or a genuine not-found result if nothing matches."""

    # This is a real network call — a genuine round trip to Google's
    # servers, same category of event as the Anthropic API call in the
    # loop below, just a different destination.
    search_result = gmaps.places(query=business_name)

    # Google's response is a bigger dictionary with a "results" list
    # inside it. Fall back to an empty list if that key's somehow missing,
    # rather than crashing on the next line.
    results = search_result.get("results", [])

    # A genuine, unscripted failure case — not rehearsed like v4's stock
    # feed. If Google found nothing matching this name, say so honestly
    # rather than trying to read data that was never there.
    if not results:
        return {
            "business_name": business_name,
            "error": "not_found",
            "message": "No matching business was found in Google Places for this name.",
        }

    # Text Search can return several possible matches — take only the
    # first, most relevant one. place_id is Google's unique identifier
    # for this business, needed for the follow-up call below.
    place = results[0]
    place_id = place.get("place_id")

    # A second, separate network call. The legacy Text Search response
    # doesn't include a website field, so this asks specifically for it,
    # by place_id.
    details = gmaps.place(place_id=place_id, fields=["website"])
    website = details.get("result", {}).get("website")

    # Assemble the final dictionary. bool(website) turns "is there a
    # website string, or is it empty/missing" into a clean True/False.
    return {
        "business_name": place.get("name"),
        "address": place.get("formatted_address"),
        "rating": place.get("rating"),
        "review_count": place.get("user_ratings_total"),
        "price_level": place.get("price_level"),
        "has_website": bool(website),
    }


def check_opening_status(business_name: str) -> dict:
    """Real Places Details call for live opening-hours data. Returns
    whether the business is open right now, if Google has hours data for
    it at all — some real listings genuinely don't."""

    # Same Text Search step as check_place_profile, done again here since
    # this is a separate tool — Claude might call one without the other,
    # so each function needs to be able to find the place on its own.
    search_result = gmaps.places(query=business_name)
    results = search_result.get("results", [])

    if not results:
        return {
            "business_name": business_name,
            "error": "not_found",
            "message": "No matching business was found in Google Places for this name.",
        }

    # Ask specifically for hours data by place_id. current_opening_hours
    # is the live, real-time version; opening_hours is the general weekly
    # schedule. Try the live one first, fall back to the general one.
    place_id = results[0].get("place_id")
    details = gmaps.place(place_id=place_id, fields=["opening_hours", "current_opening_hours"])
    hours = details.get("result", {}).get("current_opening_hours") or details.get("result", {}).get("opening_hours")

    # A second genuine, real gap: some real businesses simply have no
    # structured hours data on file with Google. Report that honestly
    # rather than guessing or defaulting to something plausible-looking.
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
    "check_competitor_profile": check_place_profile,
    "check_opening_status": check_opening_status,
}

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "check_place_profile",
        "description": "Look up a real business's discoverability profile via Google Places: rating, review count, price tier, and whether it has a website listed.",
        "input_schema": {
            "type": "object",
            "properties": {"business_name": {"type": "string"}},
            "required": ["business_name"],
        },
    },
    {
        "name": "check_competitor_profile",
        "description": "Look up the same discoverability profile for a named competitor business.",
        "input_schema": {
            "type": "object",
            "properties": {"business_name": {"type": "string"}},
            "required": ["business_name"],
        },
    },
    {
        "name": "check_opening_status",
        "description": "Check whether a business has real, structured opening-hours data listed with Google, and whether it's open right now. Some real listings do not have this data at all.",
        "input_schema": {
            "type": "object",
            "properties": {"business_name": {"type": "string"}},
            "required": ["business_name"],
        },
    },
]

SYSTEM_PROMPT = """\
You are evaluating two real businesses on how well-represented they are in
structured, publicly queryable data — the kind of data a system like an AI
assistant or shopping agent would actually be able to see and act on.

Use only the real data the tools return. Do not invent or assume facts
that weren't in a tool result. If a tool reports missing data (no website,
no hours listed, or the business wasn't found at all), treat that as
meaningful information in itself, not as a gap to quietly fill in.
"""

# ---------------------------------------------------------------------------
# Helpers for the two additive extras, rippled back from lesson 8 — the
# HTML report and the raw message-internals view. Neither of these touches
# the loop's actual behaviour; they only observe and record what's already
# happening.
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
    reads fine as a static section in a browser.

    Stored as a plain, JSON-safe list (not a pre-joined string) so the
    report can render each message as its own block below — that's what
    lets each message be coloured by its position in the list."""
    safe_messages = json.loads(json.dumps(messages, default=_safe_serialise))
    event_log.append({
        "type": "message_snapshot",
        "messages": safe_messages,
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
            # Each message in the list gets its own block, coloured by its
            # position (even/odd), not by snapshot — so a message keeps the
            # same colour in every snapshot it appears in, and whatever's
            # newly appended since the last snapshot is immediately obvious
            # as the block(s) continuing the pattern past where it last left off.
            message_blocks = []
            for i, message in enumerate(event["messages"]):
                colour_class = "msg-even" if i % 2 == 0 else "msg-odd"
                message_blocks.append(
                    f'<div class="message {colour_class}"><pre>{json.dumps(message, indent=2)}</pre></div>'
                )
            rows.append(
                f'<div class="card snapshot">'
                f'<div class="label">Raw messages snapshot ({len(event["messages"])} messages)</div>'
                f'<div class="messages">{"".join(message_blocks)}</div>'
                f'</div>'
            )

    # The two colour schemes for message blocks share everything except how
    # the white/light-blue distinction is applied: as a filled background
    # (with dark text) or as the text colour itself (on the existing dark
    # background). Built here, as plain CSS text, then dropped straight
    # into the stylesheet below.
    if FILLED_MESSAGE_BACKGROUNDS:
        message_colour_css = (
            "  .message pre { color: #14161a; }\n"
            "  .msg-even { background: #ffffff; }\n"
            "  .msg-odd { background: #cfe8ff; }"
        )
    else:
        message_colour_css = (
            "  .msg-even pre { color: #ffffff; }\n"
            "  .msg-odd pre { color: #cfe8ff; }"
        )

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
  .snapshot .messages {{ max-height: 500px; overflow-y: auto; }}
  .message {{ padding: 8px 10px; border-radius: 6px; margin-bottom: 6px; }}
  .message:last-child {{ margin-bottom: 0; }}
  .message pre {{ font-size: 11px; }}
{message_colour_css}
  pre {{ white-space: pre-wrap; font-family: ui-monospace, monospace; font-size: 13px; margin: 0; }}
</style></head>
<body>
<h1>Agentic run report</h1>
<div class="task"><div class="label">System prompt</div><pre>{SYSTEM_PROMPT}</pre></div>
<div class="task"><div class="label">Task</div><pre>{task}</pre></div>
{"".join(rows)}
</body></html>"""

    # Written into the "reports" folder at the repository root — anchored to
    # this script's own file location (not the current working directory),
    # so it lands in the same place whether you run this from inside the
    # lesson folder or from anywhere else. Filename is unique to this lesson
    # so it doesn't collide with any other lesson's report.
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    reports_dir = os.path.join(repo_root, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    path = os.path.join(reports_dir, "run_report_06.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path

# ---------------------------------------------------------------------------
# The agentic loop — same shape as every earlier version.
# ---------------------------------------------------------------------------

def run_agentic_loop(task: str):
    messages = [{"role": "user", "content": task}]
    event_log = []  # only used if SHOW_HTML_REPORT is True
    tool_call_number = 0  # increments with every tool call, for readability in the report
    print(f"\nTASK: {task}\n{'-'*60}")

    if SHOW_HTML_REPORT and SHOW_MESSAGE_INTERNALS:
        _record_messages_snapshot(event_log, messages)

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
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
        "Compare 'Chanel Bond Street London' and 'Dior New Bond Street London' "
        "on real discoverability signals — rating, review count, price tier, "
        "website presence, and live opening status. Give an honest verdict on "
        "which is currently better represented in structured, queryable data."
    )
