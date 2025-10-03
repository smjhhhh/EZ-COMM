# weight_adjustment_agent_gemini.py
"""
LLM-decided Weight Adjustment Agent (minimal)
- Purpose: Let Gemini read user ratings + current weights and decide new weights.
- No local algorithms. No downstream usage. Just input → Gemini → output.
- You provide the Gemini call via `gemini_decider(prompt_payload)` OR implement TODO.

Components are flexible; defaults: ["destination","transport","dining","lodging"].
"""

from typing import Dict, Any, Optional, List, Callable
import time

JSONDict = Dict[str, Any]

DEFAULT_COMPONENTS = ["destination", "transport", "dining", "lodging"]

def build_policy_prompt_payload(
    *,
    session_id: str,
    components: List[str],
    ratings: Dict[str, float],
    current_global: Dict[str, float],
    current_user: Optional[Dict[str, float]] = None,
    mode: str = "both"
) -> JSONDict:
    """Create the Gemini payload that describes the weight-adjustment task."""
    return {
        "meta": {
            "session_id": session_id,
            "timestamp": int(time.time()),
            "mode": mode,
            "instruction": (
                "You are a weight adjustment decider for trip-planning. "
                "Read user ratings and current weights, then produce UPDATED weights. "
                "All decisions are yours. Do not explain; output strictly in JSON."
            )
        },
        "inputs": {
            "components": components,
            "ratings": ratings,                 # user-provided scores (already computed upstream)
            "current_global": current_global,   # existing global weights
            "current_user": current_user        # may be None (then you may derive from global)
        },
        "constraints": {
            "sum_to_one": True,                 # ask Gemini to ensure each weight set sums to 1
            "bounds_per_weight": [0.0, 1.0],    # typical probability-like weights
            "non_negative": True
        },
        "expected_output_schema": {
            # Gemini must fill these:
            "weights": {
                "global": {c: "float" for c in components},
                "user":   {c: "float" for c in components}
            },
            "rationale": "string (optional, short)",
            "audit": {
                "observed_ratings": {c: "float" for c in components},
                "policy_notes": "string (optional)"
            }
        }
    }

def adjust_weights_with_gemini(
    *,
    session_id: str,
    ratings: Dict[str, float],
    current_global: Dict[str, float],
    current_user: Optional[Dict[str, float]] = None,
    components: List[str] = DEFAULT_COMPONENTS,
    mode: str = "both",  # "global" | "user" | "both"
    gemini_decider: Optional[Callable[[JSONDict], JSONDict]] = None,
    gemini_response: Optional[JSONDict] = None,
    strict_llm_authority: bool = True
) -> JSONDict:
    """
    Returns:
      {
        "meta": {...},
        "prompt_payload": {...},  # what we sent to Gemini
        "llm_result": {...},      # raw Gemini JSON (as returned by your call/callback)
        "weights": { "global": {...}, "user": {...} }
      }

    Notes:
      - No local scoring or heuristics. Gemini decides final weights.
      - If strict_llm_authority=True, we do not post-process or normalize; we just pass through.
      - If you need normalization, do it in your Gemini prompt or set strict_llm_authority=False and add your own step.
    """
    prompt_payload = build_policy_prompt_payload(
        session_id=session_id,
        components=components,
        ratings=ratings,
        current_global=current_global,
        current_user=current_user,
        mode=mode
    )

    # Get LLM result
    llm_result = gemini_response
    if llm_result is None:
        if gemini_decider is None:
            # TODO: implement your Gemini API call here if you don't want to pass a callback
            # Example (pseudo):
            # llm_result = call_gemini_json(prompt_payload, api_key=..., model="gemini-1.5-pro")
            raise RuntimeError("No gemini_response provided and gemini_decider is None.")
        llm_result = gemini_decider(prompt_payload)  # must return a dict

    # Extract weights from LLM result
    out_global = (llm_result.get("weights") or {}).get("global") or {}
    out_user   = (llm_result.get("weights") or {}).get("user") or {}

    # Optional: enforce component keys only (no math)
    out_global = {k: out_global.get(k) for k in components if k in out_global}
    out_user   = {k: out_user.get(k)   for k in components if k in out_user}

    # If you need any guard-rails, do it at prompt level or flip strict_llm_authority to False and add code here.
    result = {
        "meta": {
            "session_id": session_id,
            "generated_at": int(time.time()),
            "mode": mode,
            "strict_llm_authority": strict_llm_authority
        },
        "prompt_payload": prompt_payload,
        "llm_result": llm_result,
        "weights": {
            "global": out_global if mode in ("global", "both") else {},
            "user":   out_user   if mode in ("user", "both") else {}
        }
    }
    return result

# --- Minimal example (dry run) ---
if __name__ == "__main__":
    # Pretend this is Gemini's JSON (already decided by the LLM)
    fake_gemini = {
        "weights": {
            "global": {"destination": 0.45, "transport": 0.20, "dining": 0.20, "lodging": 0.15},
            "user":   {"destination": 0.50, "transport": 0.15, "dining": 0.25, "lodging": 0.10}
        },
        "rationale": "User ratings emphasize destination and dining; modestly reduce lodging and transport.",
        "audit": {
            "observed_ratings": {"destination": 0.92, "transport": 0.55, "dining": 0.78, "lodging": 0.40},
            "policy_notes": "Kept changes within typical ranges; sums to 1 each."
        }
    }

    res = adjust_weights_with_gemini(
        session_id="sess-xyz",
        ratings={"destination": 0.92, "transport": 0.55, "dining": 0.78, "lodging": 0.40},
        current_global={"destination": 0.25, "transport": 0.25, "dining": 0.25, "lodging": 0.25},
        current_user={"destination": 0.30, "transport": 0.20, "dining": 0.30, "lodging": 0.20},
        components=DEFAULT_COMPONENTS,
        mode="both",
        gemini_response=fake_gemini  # or provide gemini_decider=...
    )
    print(res)
