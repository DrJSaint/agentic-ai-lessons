"""
Lesson 3 — a genuine branch.

Same shape as v1, but with a THIRD tool that Claude only needs sometimes:
check_review_authenticity. It's there for cases where the review data looks
thin or worth double-checking before trusting it in a verdict.

Because it's optional, the number of tool calls Claude makes can genuinely
vary between runs and between brands — this is the difference between a
scripted pipeline (always the same steps) and a real agentic decision
(the path depends on what Claude decides it needs).

Try running this with a few different brand pairs (edit the task at the
bottom) and watch whether it calls two tools or three.

Every step is printed so you can watch the loop happen — that terminal
output never changes, no matter how the toggles below are set. Tool
calls/results are numbered (`[Tool call 1]`, `[Tool result 1]`, `[Tool
call 2]`...) so a run with several tool calls is easier to follow in both
the terminal and the HTML report.

Independent, additive extras, controlled by the booleans just below the
imports (see lesson 1 for the full explanation):

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
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# ---------------------------------------------------------------------------
# The toggles. Flip any of these independently of the others.
# ---------------------------------------------------------------------------

SHOW_HTML_REPORT = True
SHOW_MESSAGE_INTERNALS = True
FILLED_MESSAGE_BACKGROUNDS = True

# ---------------------------------------------------------------------------
# Mock tools — now three. The first two are the same as v1.
# ---------------------------------------------------------------------------

def check_brand_data(brand_name: str) -> dict:
    # Deliberately thin review count for Lumière, to invite a closer look.
    data = {
        "Lumière": {
            "has_structured_pricing": True,
            "has_availability_api": False,
            "average_review_score": 4.7,
            "review_count": 1600,
        },
        "Solenne": {
            "has_structured_pricing": True,
            "has_availability_api": True,
            "average_review_score": 4.3,
            "review_count": 1560,
        },
    }
    return {"brand": brand_name, **data.get(brand_name, data["Lumière"])}


def check_competitor_data(brand_name: str) -> dict:
    return check_brand_data(brand_name)


def check_review_authenticity(brand_name: str) -> dict:
    """Optional third tool — flags whether a brand's review data looks
    trustworthy, based on its verified purchase ratio.

    The ratio is the only thing that varies here; the flag text is always
    derived from it, so the tool result can't contradict itself the way
    it did earlier (a healthy ratio paired with a stale caution message).
    """
    ratios = {
        "Lumière": 0.67,
        "Solenne": 0.88,
    }
    ratio = ratios.get(brand_name, 0.31)

    if ratio < 0.5:
        flag = f"low verified purchase ratio ({ratio:.0%}) — treat the average with caution"
    else:
        flag = f"healthy verified purchase ratio ({ratio:.0%}) — average is reliable"

    return {
        "brand": brand_name,
        "verified_purchase_ratio": ratio,
        "flag": flag,
    }


MOCK_FUNCTIONS = {
    "check_brand_data": check_brand_data,
    "check_competitor_data": check_competitor_data,
    "check_review_authenticity": check_review_authenticity,
}

# ---------------------------------------------------------------------------
# Tool definitions — note the third tool's description explicitly signals
# it's optional and situational, not a required step.
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "check_brand_data",
        "description": "Look up structured discoverability data for a luxury brand: pricing, availability API, and review profile.",
        "input_schema": {
            "type": "object",
            "properties": {"brand_name": {"type": "string"}},
            "required": ["brand_name"],
        },
    },
    {
        "name": "check_competitor_data",
        "description": "Look up the same discoverability data for a named competitor brand.",
        "input_schema": {
            "type": "object",
            "properties": {"brand_name": {"type": "string"}},
            "required": ["brand_name"],
        },
    },
    {
        "name": "check_review_authenticity",
        "description": (
            "Check how reliable a brand's review data is — verified purchase "
            "ratio and a caution flag. Only worth calling if a brand's review "
            "count looks low or its score looks surprisingly high relative to "
            "its competitor, and you want to verify the number is trustworthy "
            "before using it in your verdict. Not needed if the review data "
            "already looks solid."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"brand_name": {"type": "string"}},
            "required": ["brand_name"],
        },
    },
]

SYSTEM_PROMPT = """
You are evaluating luxury brands for AI shopping agent discoverability.
When weighing signals against each other, treat verified review trustworthiness
as at least as important as live availability data.
"""

# ---------------------------------------------------------------------------
# Helpers for the two additive extras — the HTML report and the raw
# message-internals view. Neither of these touches the loop's actual
# behaviour; they only observe and record what's already happening.
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
    path = os.path.join(reports_dir, "run_report_03.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path

# ---------------------------------------------------------------------------
# The agentic loop — identical in structure to v1.
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
                fn = MOCK_FUNCTIONS[block.name]
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
        "Would 'Lumière' get shortlisted by an AI shopping agent over "
        "its competitor 'Solenne'? Check both brands' data, and check "
        "review authenticity if you think it's warranted, then give a "
        "verdict with your reasoning."
    )
