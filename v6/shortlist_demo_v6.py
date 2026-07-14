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
# The agentic loop — same shape as every earlier version.
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
    run(
        "Compare 'Chanel Bond Street London' and 'Dior New Bond Street London' "
        "on real discoverability signals — rating, review count, price tier, "
        "website presence, and live opening status. Give an honest verdict on "
        "which is currently better represented in structured, queryable data."
    )
