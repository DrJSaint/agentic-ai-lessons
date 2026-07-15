"""
Lesson 7 — real data, genuinely open-ended.

The tools here are identical to v6 — two real Google Places lookups, no
mock data anywhere. What's different is the task. v6 asked for a fixed
checklist ("check rating, review count, price tier, website, and opening
hours for both") — fully specified, so Claude had nothing left to decide
except the order to do it in. That produced a single, efficient pass with
no real branching.

v7 asks something genuinely open instead: assess four real Bond Street
luxury flagships, decide for yourself what's worth checking for each one
and in what order, and stop once you're confident. No fixed checklist.

Three of the four businesses (Chanel, Dior, Louis Vuitton) are famous
flagships likely to have rich, complete listings. The fourth, Brunello
Cucinelli, is a genuinely smaller, quieter brand — real, but plausibly
thinner on Google's data. Nothing is scripted to make it thin; it's just
a real business that might turn out that way, giving Claude an honest
chance (not a guarantee) to hit something worth reacting to mid-run.
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
# Real tools — identical to v6. Both genuinely call the Google Places API.
# No mock data anywhere in this script.
# ---------------------------------------------------------------------------

def check_place_profile(business_name: str) -> dict:
    """Real Google Places Text Search plus a Details call for the website
    field. Returns actual rating, review count, price tier, and whether a
    website is listed — or a genuine not-found result if nothing matches."""

    # A real network call — a genuine round trip to Google's servers.
    search_result = gmaps.places(query=business_name)

    # Google's response wraps matches in a "results" list. Fall back to an
    # empty list if that key's somehow missing, rather than crashing below.
    results = search_result.get("results", [])

    # A genuine, unscripted failure case: if Google found nothing matching
    # this name, say so honestly rather than reading data that isn't there.
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

    # A second, separate network call. Legacy Text Search doesn't include
    # a website field, so this asks specifically for it, by place_id.
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


# TOOL_FUNCTIONS maps the tool names Claude can request onto the real
# Python functions above. Claude only ever sees the names and descriptions
# in TOOLS below — never this dictionary, never the function code itself.
TOOL_FUNCTIONS = {
    "check_place_profile": check_place_profile,
    "check_opening_status": check_opening_status,
}

# ---------------------------------------------------------------------------
# Tool definitions — the descriptions Claude actually reads. Only two
# tools this time, not four-per-brand as in earlier versions — with a
# genuinely open task, Claude decides how many times to call each one and
# for which businesses, rather than being handed one tool per signal.
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# System prompt — the standing job description. Notice what's deliberately
# NOT here: nothing about deciding what to check or when to stop. That
# belongs in the task below, since it's specific to this exercise, not a
# permanent trait of the agent. Keeping it out here means it's easy to
# rewrite the open-endedness of the task between runs without touching
# these standing rules.
# ---------------------------------------------------------------------------

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
# The agentic loop — identical shape to every earlier version.
# ---------------------------------------------------------------------------

def run(task: str):
    messages = [{"role": "user", "content": task}]
    print(f"\nTASK: {task}\n{'-'*60}")

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

        if response.stop_reason != "tool_use":
            print(f"\n{'-'*60}\nDONE.")
            return

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []

        for block in response.content:
            if block.type == "tool_use":
                fn = TOOL_FUNCTIONS[block.name]
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
    # This is the user prompt — today's specific assignment. Everything
    # about HOW open-ended this run is lives here, not in the system
    # prompt, deliberately, so it's easy to rewrite between experiments.
    run(
        "You're assessing four Bond Street luxury flagships — Chanel, "
        "Dior, Louis Vuitton, and Brunello Cucinelli — for a discoverability "
        "consultancy. Decide for yourself what's worth checking for each "
        "business and in what order, and stop once you're confident in "
        "your overall assessment. Explain your reasoning as you go, then "
        "give your final assessment."
    )
