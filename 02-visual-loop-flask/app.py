"""
Lesson 2 — same agentic loop as lesson 1, but steps stream to a webpage as
cards instead of printing to a terminal. Tool call/result cards are
numbered (Tool call 1, Tool result 1, Tool call 2...), so a run with
several tool calls is easier to follow.

Run this, then open http://localhost:5000 in your browser and click "Run".
"""

import os
import json
import time
from flask import Flask, Response, render_template, request
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
app = Flask(__name__)

# ---------------------------------------------------------------------------
# Same mock tools as before
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
]

# ---------------------------------------------------------------------------
# The agentic loop, yielding one event per step instead of printing
# ---------------------------------------------------------------------------

def run_agentic_loop(task: str):
    messages = [{"role": "user", "content": task}]
    tool_call_number = 0  # increments with every tool call, for readability
    yield {"type": "task", "content": task}

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

        for block in response.content:
            if block.type == "text" and block.text.strip():
                yield {"type": "reasoning", "content": block.text.strip()}

        if response.stop_reason != "tool_use":
            yield {"type": "done"}
            return

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []

        for block in response.content:
            if block.type == "tool_use":
                tool_call_number += 1
                fn = MOCK_FUNCTIONS[block.name]
                result = fn(**block.input)

                yield {"type": "tool_call", "name": block.name, "input": block.input, "number": tool_call_number}
                time.sleep(0.6)  # tiny pause so the UI can show the call before the result
                yield {"type": "tool_result", "name": block.name, "result": result, "number": tool_call_number}

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

        messages.append({"role": "user", "content": tool_results})


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/stream")
def stream():
    task = request.args.get(
        "task",
        "Would 'Lumière' get shortlisted by an AI shopping agent over "
        "its competitor 'Aurelio'? Check both brands' data and give a "
        "verdict with your reasoning.",
    )

    def event_stream():
        for event in run_agentic_loop(task):
            yield f"data: {json.dumps(event)}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
