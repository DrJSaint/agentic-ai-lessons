"""
Lesson 1: the smallest possible agentic loop.

Claude is asked whether "Brand X" would get shortlisted by an AI shopping
agent over a competitor. It decides for itself which of two tools to call,
in what order, and produces a verdict based on what the (fake) data says.

Every step is printed so you can watch the loop happen.
"""

import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# ---------------------------------------------------------------------------
# Mock "tools" — plain Python functions returning made-up but plausible data.
# In a real system these would call a real API, database, or scraper.
# ---------------------------------------------------------------------------

def check_brand_data(brand_name: str) -> dict:
    return {
        "brand": brand_name,
        "has_structured_pricing": True,
        "has_availability_api": False,
        "average_review_score": 4.1,
        "review_count": 812,
    }

def check_competitor_data(brand_name: str) -> dict:
    return {
        "brand": brand_name,
        "has_structured_pricing": True,
        "has_availability_api": True,
        "average_review_score": 4.6,
        "review_count": 2140,
    }

MOCK_FUNCTIONS = {
    "check_brand_data": check_brand_data,
    "check_competitor_data": check_competitor_data,
}

# ---------------------------------------------------------------------------
# Tool definitions Claude actually sees — name, description, expected input.
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "check_brand_data",
        "description": "Look up structured discoverability data for a luxury brand: whether it has machine-readable pricing, an availability API, and its review profile.",
        "input_schema": {
            "type": "object",
            "properties": {"brand_name": {"type": "string"}},
            "required": ["brand_name"],
        },
    },
    {
        "name": "check_competitor_data",
        "description": "Look up the same discoverability data for a named competitor brand, for comparison.",
        "input_schema": {
            "type": "object",
            "properties": {"brand_name": {"type": "string"}},
            "required": ["brand_name"],
        },
    },
]

# ---------------------------------------------------------------------------
# The agentic loop
# ---------------------------------------------------------------------------

def run_agentic_loop(task: str):
    messages = [{"role": "user", "content": task}]
    print(f"\nTASK: {task}\n{'-'*60}")

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

        # Show any reasoning/text Claude produced this turn
        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"\n[Claude says]\n{block.text.strip()}")

        # If Claude didn't ask for a tool, it's done — print final answer and stop
        if response.stop_reason != "tool_use":
            print(f"\n{'-'*60}\nDONE.")
            return

        # Claude wants to use one or more tools — run each, print what happened
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
        # loop continues — Claude sees the result and decides what's next


if __name__ == "__main__":
    run_agentic_loop(
        "Would 'Lumière' get shortlisted by an AI shopping agent over "
        "its competitor 'Aurelio'? Check both brands' data and give a "
        "verdict with your reasoning."
    )
