"""
Lesson 4 — real looping and failure recovery.

Everything from v3 is here (three tools, system prompt weighting), plus one
new twist: check_live_stock_feed can genuinely fail, the first time it's
called for a given brand, with a realistic-looking service error. It only
succeeds on a second attempt.

Nothing in the code tells Claude to retry. Watch what it actually does when
a tool comes back with an error instead of data — does it try again, give
up and note the gap, or route around it using what it already has?
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

# Tracks how many times the flaky tool has been called per brand, so it can
# fail on the first attempt and succeed on the second, deterministically —
# real-world flakiness with a predictable teaching outcome.
_stock_feed_attempts = {}

# ---------------------------------------------------------------------------
# Mock tools — same three as v3, plus one that can fail.
# ---------------------------------------------------------------------------

def check_brand_data(brand_name: str) -> dict:
    return {"brand": brand_name, **BRAND_DATA.get(brand_name, BRAND_DATA["Lumière"])}


# Deliberately just calls check_brand_data with the same lookup. Claude still
# needs this as a separately named tool, distinct from check_brand_data, so
# its own reasoning can tell "the brand" and "the competitor" apart when it
# decides what to call and why — even though the underlying data is identical.
def check_competitor_data(brand_name: str) -> dict:
    return check_brand_data(brand_name)


# The flag text is generated from the ratio, not hardcoded separately, so the
# two can't drift out of sync with each other.
def check_review_authenticity(brand_name: str) -> dict:
    ratio = REVIEW_RATIOS.get(brand_name, 0.31)
    if ratio < 0.5:
        flag = f"low verified purchase ratio ({ratio:.0%}) — treat the average with caution"
    else:
        flag = f"healthy verified purchase ratio ({ratio:.0%}) — average is reliable"
    return {"brand": brand_name, "verified_purchase_ratio": ratio, "flag": flag}


def check_live_stock_feed(brand_name: str) -> dict:
    """A live stock-checking service. Genuinely unreliable: the first call
    for any given brand times out, exactly like a real flaky API would."""
    attempts = _stock_feed_attempts.get(brand_name, 0) + 1
    _stock_feed_attempts[brand_name] = attempts

    if attempts < 5:
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


MOCK_FUNCTIONS = {
    "check_brand_data": check_brand_data,
    "check_competitor_data": check_competitor_data,
    "check_review_authenticity": check_review_authenticity,
    "check_live_stock_feed": check_live_stock_feed,
}

# ---------------------------------------------------------------------------
# Tool definitions — the descriptions Claude actually reads. These never
# expose the real Python code above; they're plain-English summaries of
# what each tool does and what input it needs.
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
]

SYSTEM_PROMPT = """\
You are evaluating luxury brands for AI shopping agent discoverability.

When weighing signals against each other, treat verified review trustworthiness
as at least as important as live availability data. A brand with excellent,
verified reviews should not be automatically disqualified just because it
lacks a live availability feed.

Tools that represent live external services can fail. If one reports an
error, use your judgement about whether it's worth retrying once, or
whether it's reasonable to proceed with the information you already have.
"""

# ---------------------------------------------------------------------------
# The agentic loop — same shape as v1/v3.
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
        "Would 'Lumière' get shortlisted by an AI shopping agent over its "
        "competitor 'Solenne'? Check both brands' data, check review "
        "authenticity if warranted, and check Lumière's live stock feed "
        "before giving your verdict."
    )
