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
"""

import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

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
# The agentic loop — identical in structure to v1.
# ---------------------------------------------------------------------------

def run(task: str):
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
    run(
        "Would 'Lumière' get shortlisted by an AI shopping agent over "
        "its competitor 'Solenne'? Check both brands' data, and check "
        "review authenticity if you think it's warranted, then give a "
        "verdict with your reasoning."
    )