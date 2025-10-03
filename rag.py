# adk_gemini_agent_template.py
# Purpose: ADK-style agent that (conceptually) calls Gemini to enrich context,
# then normalizes user text + options into a single JSON spec for downstream use.
# Scope: Structure only—use TODOs for actual SDK calls, auth, and IO.

import json
from typing import Any, Dict, Optional

JSONDict = Dict[str, Any]

# -----------------------------
# ADK agent configuration
# -----------------------------
class ADKAgentConfig:
    def __init__(self,
                 model_name: str = "gemini-2.5-flash",
                 temperature: float = 0.3,
                 top_p: float = 0.9,
                 max_output_tokens: int = 1024):
        self.model_name = model_name
        self.temperature = temperature
        self.top_p = top_p
        self.max_output_tokens = max_output_tokens
        # TODO: add safety settings, rate limits, tracing toggles, etc.

# -----------------------------
# Gemini client (placeholder)
# -----------------------------
class GeminiClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        # TODO: initialize real Gemini SDK client with api_key and options

    def enrich(self, user_text: str, options: JSONDict) -> JSONDict:
        """
        Use Gemini to infer/complete missing intent signals from user_text + options.
        Return a small dict of inferred fields (e.g., constraints, timeline, budget hints).
        """
        # TODO: replace with real API call and parsing logic.
        # This is a stubbed, deterministic placeholder for structure demonstration.
        inferred = {
            "detected_language": "en",
            "extracted_intent": "plan_local_trip",
            "constraints": {
                "max_budget_usd": None,             # TODO: infer if present
                "time_window": None,                # TODO: infer if present
                "accessibility": {"stroller_ok": options.get("has_children", False)}
            },
            "risk_flags": [],                       # e.g., missing dates/locations
            "salient_entities": [],                 # e.g., places/venues detected
        }
        return inferred

# -----------------------------
# Normalization helpers
# -----------------------------
DEFAULTS: Dict[str, Any] = {
    "user_id": "u_default",
    "display_name": "Guest",
    "locale": "en-US",
    "timezone": "America/New_York",
    "pref_metric": True,
    "transport_mode": "walk",                 # walk/bike/drive/transit/rideshare
    "dining_preferences": ["no_preference"],  # e.g., vegan/no_pork/no_spicy
    "party_size": "1",                        # "1","2","3-4","5+"
    "has_pets": False,
    "has_children": False,
}

def with_defaults(options: JSONDict) -> JSONDict:
    """Shallow defaults fill for options."""
    return {**DEFAULTS, **(options or {})}

def build_normalized_spec(user_text: str,
                          options: JSONDict,
                          gemini_inferred: JSONDict) -> JSONDict:
    """
    Produce a compact, downstream-friendly JSON spec that blends:
    - user profile & preferences,
    - explicit needs (from user_text),
    - inferred signals (from Gemini).
    """
    opts = with_defaults(options)

    # Minimal, readable schema for downstream agents/tools
    spec = {
        "schema_version": "1.0.0",
        "user": {
            "user_id": opts["user_id"],
            "profile": {
                "display_name": opts["display_name"],
                "locale": opts["locale"],
                "timezone": opts["timezone"],
                "units": {
                    "length": "metric" if opts["pref_metric"] else "imperial",
                    "temperature": "C" if opts["pref_metric"] else "F",
                    "currency": "USD"
                }
            },
            "preferences": {
                "transport_mode": opts["transport_mode"],
                "dining": opts["dining_preferences"],
                "party_size": opts["party_size"],
                "has_pets": opts["has_pets"],
                "has_children": opts["has_children"]
            }
        },
        "request": {
            "raw_text": user_text,
            # TODO: if you already structured user_text upstream, include it here (slots/entities).
            "structured": {
                "intent": gemini_inferred.get("extracted_intent"),
                "salient_entities": gemini_inferred.get("salient_entities", []),
                "constraints": gemini_inferred.get("constraints", {}),
                "risk_flags": gemini_inferred.get("risk_flags", []),
                "language": gemini_inferred.get("detected_language"),
            }
        },
        "routing_hints": {
            # Downstream routing/strategy hints for ADK orchestrator:
            "preferred_mode": opts["transport_mode"],
            "needs_rag": False,        # TODO: set True if user_text suggests factual lookup
            "needs_tools": ["maps"],   # TODO: infer tool set based on intent/entities
        },
        "provenance": {
            "source": "adk_agent_pipeline",
            "llm": {
                "provider": "google",
                "model": "gemini",
                "variant": gemini_inferred.get("_model_variant", "gemini-1.5-flash")
            }
        }
    }
    return spec

# -----------------------------
# Agent orchestration (minimal)
# -----------------------------
class ADKGeminiAgent:
    def __init__(self, cfg: ADKAgentConfig, client: GeminiClient):
        self.cfg = cfg
        self.client = client
        # TODO: attach tracing/logging if needed

    def run(self, user_text: str, options: JSONDict) -> JSONDict:
        """
        1) Accept pre-collected user_text and options (already available upstream).
        2) Ask Gemini to enrich/complete key signals (intent, constraints, etc.).
        3) Build normalized JSON spec for downstream planners/tools.
        """
        # TODO: add input validation/guardrails
        inferred = self.client.enrich(user_text=user_text, options=options)
        # Optionally include chosen model variant for provenance
        inferred["_model_variant"] = self.cfg.model_name
        spec = build_normalized_spec(user_text, options, inferred)
        return spec

# -----------------------------
# Serialization (optional)
# -----------------------------
def write_json(path: str, data: JSONDict) -> None:
    """
    Persist the normalized spec for downstream consumption (optional).
    """
    # TODO: replace with real file IO and error handling
    _ = (path, data)
    # Example:
    # with open(path, "w", encoding="utf-8") as f:
    #     json.dump(data, f, indent=2, ensure_ascii=False)

# -----------------------------
# Example usage (reference only)
# -----------------------------
# def example():
#     cfg = ADKAgentConfig(model_name="gemini-1.5-flash")
#     client = GeminiClient(api_key="YOUR_API_KEY")  # TODO: supply securely via env/secret manager
#     agent = ADKGeminiAgent(cfg, client)
#
#     # Assume upstream already produced both structures:
#     user_text = "Plan an afternoon around NEU Arlington with easy transit and kid-friendly spots."
#     options = {
#         "user_id": "u_123",
#         "display_name": "JY",
#         "locale": "en-US",
#         "timezone": "America/New_York",
#         "pref_metric": True,
#         "transport_mode": "transit",
#         "dining_preferences": ["no_spicy", "no_pork"],
#         "party_size": "3-4",
#         "has_pets": False,
#         "has_children": True
#     }
#
#     spec = agent.run(user_text=user_text, options=options)
#     write_json("normalized_request.json", spec)
#
# if __name__ == "__main__":
#     example()
