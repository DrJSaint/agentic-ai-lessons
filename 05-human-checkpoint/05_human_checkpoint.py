"""
Lesson 5 — the human checkpoint.

Everything from v4 is here — four observe-only tools, the system prompt,
failure recovery — plus one new tool that's different in kind, not just in
number: draft_partnership_outreach. Calling it doesn't just gather more
information. It proposes sending a real message to a real brand.

This is the observe-vs-act line from the layered document, built into code.
The three tools before it can run freely, no questions asked, because
nothing in the world changes as a result. This one cannot. When Claude
calls it, the script stops, shows you exactly what it wants to send, and
waits for a real yes or no before anything happens. Whatever you decide
gets reported back to Claude as a genuine tool result — approved or
declined — and Claude continues reasoning from there, same as it would
react to any other tool's output.

Every step is printed so you can watch the loop happen — with one
deliberate exception: draft_partnership_outreach prints its own human
checkpoint dialog directly, so the generic [Tool call]/[Tool result] lines
are suppressed for that one tool to avoid printing it twice. That
suppression is terminal-only, though — the toggles below still capture it
in full for the HTML report regardless, so the report stays a complete,
traceable record of everything that happened even when the terminal
deliberately shows less. Whenever the generic lines do print, tool
calls/results are numbered (`[Tool call 1]`, `[Tool result 1]`, `[Tool
call 2]`...), matching lesson 8 — the counter still increments for the
suppressed tool too, so its number stays consistent with the report.

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
# Mock data — shared by the tool functions below.
# ---------------------------------------------------------------------------

BRAND_DATA = {
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

REVIEW_RATIOS = {
    "Lumière": 0.67,
    "Solenne": 0.88,
}

_stock_feed_attempts = {}

# ---------------------------------------------------------------------------
# Observe-only tools — same as v4. These can run freely: nothing in the
# world changes as a result of calling them.
# ---------------------------------------------------------------------------

def check_brand_data(brand_name: str) -> dict:
    return {"brand": brand_name, **BRAND_DATA.get(brand_name, BRAND_DATA["Lumière"])}


def check_competitor_data(brand_name: str) -> dict:
    return check_brand_data(brand_name)


def check_review_authenticity(brand_name: str) -> dict:
    ratio = REVIEW_RATIOS.get(brand_name, 0.31)
    if ratio < 0.5:
        flag = f"low verified purchase ratio ({ratio:.0%}) — treat the average with caution"
    else:
        flag = f"healthy verified purchase ratio ({ratio:.0%}) — average is reliable"
    return {"brand": brand_name, "verified_purchase_ratio": ratio, "flag": flag}


def check_live_stock_feed(brand_name: str) -> dict:
    """A live stock-checking service. The first call for any given brand
    times out, exactly like a real flaky API would."""
    attempts = _stock_feed_attempts.get(brand_name, 0) + 1
    _stock_feed_attempts[brand_name] = attempts

    if attempts == 1:
        return {
            "brand": brand_name,
            "error": "service_timeout",
            "message": "The live stock feed did not respond in time. This can be transient — retrying may succeed.",
        }

    return {
        "brand": brand_name,
        "in_stock": True,
        "units_available": 14,
        "last_updated": "moments ago",
    }


# ---------------------------------------------------------------------------
# The act tool — different in kind, not just in number. This is the one
# tool in the whole script that does something rather than just reporting
# something. It never executes on its own; a human decides every time.
# ---------------------------------------------------------------------------

def draft_partnership_outreach(brand_name: str, message: str) -> dict:
    """Proposes sending a partnership outreach message to a brand. This
    function does NOT send anything by itself — it pauses and asks a human
    to approve or decline before anything happens. Whatever the human
    decides is what gets reported back to Claude as the tool's result."""

    print("\n" + "=" * 60)
    print("  HUMAN CHECKPOINT — consequential action proposed")
    print("=" * 60)
    print(f"  Brand:   {brand_name}")
    print(f"  Message: {message}")
    print("=" * 60)

    decision = input("  Approve sending this? (y/n): ").strip().lower()

    if decision == "y":
        print("  -> Approved. Sending.\n")
        return {
            "brand": brand_name,
            "status": "sent",
            "approved_by": "human reviewer",
        }
    else:
        print("  -> Declined. Nothing was sent.\n")
        return {
            "brand": brand_name,
            "status": "declined",
            "reason": "Human reviewer did not approve this message.",
        }


MOCK_FUNCTIONS = {
    "check_brand_data": check_brand_data,
    "check_competitor_data": check_competitor_data,
    "check_review_authenticity": check_review_authenticity,
    "check_live_stock_feed": check_live_stock_feed,
    "draft_partnership_outreach": draft_partnership_outreach,
}

# ---------------------------------------------------------------------------
# Tool definitions — the descriptions Claude actually reads.
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
            "Check how reliable a brand's review data is. Only worth calling if "
            "a brand's review score looks surprisingly high relative to its "
            "competitor and you want to verify it's trustworthy before using it "
            "in your verdict."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"brand_name": {"type": "string"}},
            "required": ["brand_name"],
        },
    },
    {
        "name": "check_live_stock_feed",
        "description": (
            "Check a brand's real-time stock feed for current availability. "
            "This is a live external service. If it reports a timeout, you "
            "may want to try again before concluding the data is unavailable."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"brand_name": {"type": "string"}},
            "required": ["brand_name"],
        },
    },
    {
        "name": "draft_partnership_outreach",
        "description": (
            "Propose a partnership outreach message to a brand, for example "
            "recommending they close a discoverability gap such as a missing "
            "availability API. This is a real, consequential action: a human "
            "reviewer will see exactly what you propose to send and decide "
            "whether to approve it before anything is sent. Only call this "
            "once you have enough information to justify a specific, useful "
            "message — do not call it speculatively."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "brand_name": {"type": "string"},
                "message": {
                    "type": "string",
                    "description": "The actual outreach message you want to send, addressed to the brand.",
                },
            },
            "required": ["brand_name", "message"],
        },
    },
]

SYSTEM_PROMPT = """\
You are evaluating luxury brands for AI shopping agent discoverability, and
you have the ability to propose outreach to a brand if you find a clear,
specific improvement worth recommending.

When weighing signals against each other, treat verified review trustworthiness
as at least as important as live availability data. A brand with excellent,
verified reviews should not be automatically disqualified just because it
lacks a live availability feed.

Tools that represent live external services can fail. If one reports an
error, use your judgement about whether it's worth retrying, or whether
it's reasonable to proceed with the information you already have.

The draft_partnership_outreach tool is different from your other tools: it
proposes a real action rather than gathering information. Only use it if
your analysis surfaces a specific, actionable gap worth flagging to a
brand. A human will always review what you propose before it is sent, and
may decline it — if that happens, continue your analysis taking that
outcome into account rather than assuming the message went out.
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
    path = os.path.join(reports_dir, "run_report_05.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path

# ---------------------------------------------------------------------------
# The agentic loop — identical shape to v1/v3/v4.
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

                # Terminal printing is suppressed for the human-checkpoint
                # tool (it prints its own dialog above) — but the event log
                # captures every tool call/result unconditionally, so the
                # HTML report stays a complete, traceable record regardless
                # of what the terminal chooses to show.
                if block.name != "draft_partnership_outreach":
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
        "Evaluate 'Lumière' against its competitor 'Solenne' for AI shopping "
        "agent discoverability. Check both brands' data, verify review "
        "authenticity if warranted, and check Lumière's live stock feed. "
        "If you find a clear, specific improvement Lumière should make, "
        "propose an outreach message recommending it. Then give your "
        "overall verdict."
    )
