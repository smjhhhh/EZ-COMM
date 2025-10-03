# adk_prompt_agent_single_poi.py
# Purpose: Ultra-simple, prompt-centric agent that guides an LLM to emit a
# normalized single-POI trip plan in JSON, using previously integrated info.
# Scope: Structure-first; real LLM call, auth, and IO are left as TODOs.

import json
from typing import Any, Dict, Optional

JSONDict = Dict[str, Any]

# -----------------------------
# Agent config (minimal)
# -----------------------------
class AgentConfig:
    def __init__(self,
                 model_name: str = "gemini-1.5-flash",
                 temperature: float = 0.2,
                 max_output_tokens: int = 800):
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        # TODO: add safety settings, timeouts, retries, tracing toggles

# -----------------------------
# Prompt builder
# -----------------------------
SINGLE_POI_JSON_SCHEMA_SNIPPET = """
Required JSON schema (single POI):
{
  "schema_version": "1.0.0",
  "plan": {
    "poi_name": "string",
    "poi_category": "string",                 // e.g., museum, park, landmark
    "location": {
      "address": "string",
      "lat": number,                          // nullable allowed via null
      "lon": number                           // nullable allowed via null
    },
    "timeframe": {
      "start_time_local": "string",           // ISO-8601 or HH:MM
      "duration_minutes": number
    },
    "transport": {
      "mode": "string",                       // walk/bike/drive/transit/rideshare
      "notes": "string"
    },
    "dining_suggestion": {
      "name": "string",
      "diet_fit": ["string"],                 // aligns with user dining prefs
      "notes": "string"
    },
    "budget_estimate_usd": {
      "tickets": number,                      // 0 if free
      "transport": number,
      "food": number
    },
    "accessibility": {
      "stroller_ok": boolean,
      "wheelchair_ok": boolean
    },
    "risks": ["string"],                      // e.g., weather-sensitive, queues
    "packing_tips": ["string"],
    "citations": ["string"]                   // optional, short text URLs or names
  }
}
Rules:
- Output MUST be valid JSON only (no prose, no markdown fences).
- If a field is unknown, use a reasonable placeholder or null (for lat/lon).
- Align choices with user preferences (transport, dining, kids/pets).
- Keep it concise and actionable; one POI only.
"""

def build_prompt(normalized_spec: JSONDict) -> str:
    """
    Create a system-style prompt that:
    - Gives the model the normalized spec as context.
    - Instructs it to output a single-POI JSON plan.
    """
    # NOTE: This stays readable and stable for debugging.
    return f"""
You are a precise trip-planning agent. You will produce a single-POI visit plan
as JSON only, following the schema below. Use the provided normalized spec to
align transport, dining preferences, party size, pets/children, locale, and
timezone. When unknown, pick reasonable, safe defaults and keep the plan local
to the user's implied region.

Normalized spec (for context):
{json.dumps(normalized_spec, indent=2)}

{SINGLE_POI_JSON_SCHEMA_SNIPPET}

Now produce ONLY the JSON object.
""".strip()

# -----------------------------
# LLM call placeholder
# -----------------------------
def call_llm(prompt: str, cfg: AgentConfig) -> str:
    """
    TODO: Implement actual call to your LLM provider (e.g., Gemini).
    - Use cfg.model_name, cfg.temperature, cfg.max_output_tokens.
    - Return the raw string response (expected to be JSON).
    """
    # Stub response for structure demonstration only:
    stub = {
        "schema_version": "1.0.0",
        "plan": {
            "poi_name": "National Gallery of Art Sculpture Garden",
            "poi_category": "park",
            "location": {
                "address": "7th St & Constitution Ave NW, Washington, DC 20408",
                "lat": None,
                "lon": None
            },
            "timeframe": {
                "start_time_local": "14:00",
                "duration_minutes": 90
            },
            "transport": {
                "mode": "transit",
                "notes": "Use the nearest metro stop; short walk required."
            },
            "dining_suggestion": {
                "name": "Nearby casual spot",
                "diet_fit": ["no_spicy", "no_pork"],
                "notes": "Order mild options; verify ingredients."
            },
            "budget_estimate_usd": {
                "tickets": 0,
                "transport": 6,
                "food": 20
            },
            "accessibility": {
                "stroller_ok": True,
                "wheelchair_ok": True
            },
            "risks": ["Weather dependent", "Weekend crowds"],
            "packing_tips": ["Water bottle", "Sun protection", "Light jacket"],
            "citations": []
        }
    }
    return json.dumps(stub)

# -----------------------------
# JSON parsing guard
# -----------------------------
def parse_json_maybe(content: str) -> JSONDict:
    """
    Attempt to parse the model output as JSON; raise with a short message on error.
    """
    try:
        return json.loads(content)
    except Exception as e:
        # TODO: Add a recovery prompt or JSON repair step if desired.
        raise ValueError(f"Model did not return valid JSON: {e}")

# -----------------------------
# Agent runner
# -----------------------------
class PromptAgentSinglePOI:
    def __init__(self, cfg: Optional[AgentConfig] = None):
        self.cfg = cfg or AgentConfig()

    def run(self, normalized_spec: JSONDict) -> JSONDict:
        """
        - Build a strict prompt that encodes the JSON schema + constraints.
        - Call LLM to generate the single-POI plan.
        - Parse and return the JSON.
        """
        # TODO: Validate normalized_spec shape if needed.
        prompt = build_prompt(normalized_spec)
        raw = call_llm(prompt, self.cfg)
        out = parse_json_maybe(raw)
        # TODO: Optional: validate against JSON Schema.
        return out

# -----------------------------
# Example (reference only)
# -----------------------------
# if __name__ == "__main__":
#     # Assume this is the normalized spec from the previous step.
#     normalized_spec = {
#       "schema_version": "1.0.0",
#       "user": {
#         "user_id": "u_123",
#         "profile": {
#           "display_name": "JY",
#           "locale": "en-US",
#           "timezone": "America/New_York",
#           "units": {"length": "metric", "temperature": "C", "currency": "USD"}
#         },
#         "preferences": {
#           "transport_mode": "transit",
#           "dining": ["no_spicy", "no_pork"],
#           "party_size": "3-4",
#           "has_pets": False,
#           "has_children": True
#         }
#       },
#       "request": {
#         "raw_text": "An easy kid-friendly afternoon plan near NEU Arlington.",
#         "structured": {
#           "intent": "plan_local_trip",
#           "salient_entities": [],
#           "constraints": {"time_window": None, "max_budget_usd": None},
#           "risk_flags": [],
#           "language": "en"
#         }
#       },
#       "routing_hints": {"preferred_mode": "transit", "needs_rag": False, "needs_tools": ["maps"]},
#       "provenance": {"source": "adk_agent_pipeline", "llm": {"provider": "google", "model": "gemini", "variant": "gemini-1.5-flash"}}
#     }
#     agent = PromptAgentSinglePOI()
#     result = agent.run(normalized_spec)
#     print(json.dumps(result, indent=2))
