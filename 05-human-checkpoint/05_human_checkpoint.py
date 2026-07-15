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
"""

import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

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
# The agentic loop — identical shape to v1/v3/v4.
# ---------------------------------------------------------------------------

def run_agentic_loop(task: str):
    messages = [{"role": "user", "content": task}]
    print(f"\nTASK: {task}\n{'-'*60}")

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

        if response.stop_reason != "tool_use":
            print(f"\n{'-'*60}\nDONE.")
            return

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []

        for block in response.content:
            if block.type == "tool_use":
                fn = MOCK_FUNCTIONS[block.name]
                result = fn(**block.input)

                if block.name != "draft_partnership_outreach":
                    print(f"\n[Tool call] {block.name}({block.input})")
                    print(f"[Tool result] {json.dumps(result)}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

        messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    run_agentic_loop(
        "Evaluate 'Lumière' against its competitor 'Solenne' for AI shopping "
        "agent discoverability. Check both brands' data, verify review "
        "authenticity if warranted, and check Lumière's live stock feed. "
        "If you find a clear, specific improvement Lumière should make, "
        "propose an outreach message recommending it. Then give your "
        "overall verdict."
    )
