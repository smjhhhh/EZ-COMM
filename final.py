# trip_plan_merger_agent.py
"""
Trip Plan Merger Agent (minimal, LLM-decided)
- Input: multiple "nodes" (each is a formatted trip-plan JSON from your earlier step)
- Input: user_ctx with preferences/constraints (time window, timezone, budget, pace, interests, home base, etc.)
- Process: build a compact payload and let an LLM (e.g., Gemini) decide the final merged itinerary
- Output: normalized unified plan JSON ready for downstream use
- No external calls implemented here; use llm_planner callback or pass llm_response directly.
"""

from typing import Any, Dict, List, Optional, Callable
import time

# Shared type alias for readability across the agent surface.
JSONDict = Dict[str, Any]

# -------- Expected Inputs (contracts) --------
# node (example minimal shape you produced earlier):
# {
#   "meta": {"session_id": "...", "generated_at": 169... , "locale":"en", "timezone":"Europe/Madrid"},
#   "context": {"trip_window": {"start":"YYYY-MM-DD","end":"YYYY-MM-DD"}, "weather_daily":[...], "global_notes":[...]},
#   "pois": [{
#       "poi_id": "string",
#       "name": "string",
#       "coords": {"lat": float, "lng": float},
#       "score": float,
#       "tags": ["architecture",...],
#       "rating": 4.7,
#       "fit": {"budget":"ok|warn","pace":"ok|warn","interest_match": ["architecture"]},
#       "time_suggestions": {"stay_min": 90, "best_slots": ["AM","PM"]},
#       "hours": [...],
#       "ticket": {"min_eur": 26} | null,
#       "nearby": [{"name":"...", "eta_min_walk": 12}] | [],
#       "tips": ["..."],
#       "citations": [{"title":"...", "url":"...", "domain_trust":0.9}]
#   }],
#   "routing_hints": {"center":{"lat":..,"lng":..},"transit_samples":[...] }
# }

# -------- Output (normalized unified plan) --------
# {
#   "meta": {"session_id": "...", "generated_at": 169..., "llm":"gemini-*", "version":"1.0"},
#   "sources": [{"node_id": "string|hash", "used_pois": ["poi_id", ...]}],
#   "plan": {
#     "date_range": ["YYYY-MM-DD","YYYY-MM-DD"],
#     "timezone": "Area/City",
#     "kpis": {"walk_km": 7.5, "cost_estimate": 180.0, "attractions": 6, "confidence": 0.86},
#     "days": [{
#       "date": "YYYY-MM-DD",
#       "city": "string",
#       "items": [
#         {"start":"09:30","end":"11:00","title":"Visit Sagrada Familia","poi_id":"sfam","location":{"lat":..,"lng":..},"note":"Buy tickets in advance"},
#         {"transfer": {"mode":"walk|drive|transit","eta_min":15,"polyline":"optional"}},
#         {"start":"12:00","end":"13:00","title":"Lunch","category":"dining","place":"X Restaurant","note":"Local set menu"}
#       ],
#       "lodging": {"name":"Hotel ABC","address":"...","checkin_time":"15:00","note":"Near metro"},
#       "meals": [{"time":"12:00","type":"lunch","place":"X Restaurant"}]
#     }]
#   }
# }

DEFAULT_NODE_LIMIT = 6  # keep prompt compact

def build_planner_prompt_payload(
    *,
    session_id: str,
    nodes: List[JSONDict],
    user_ctx: JSONDict,
    node_ids: Optional[List[str]] = None
) -> JSONDict:
    """Create the normalized payload that the trip-plan LLM expects."""
    capped_nodes = (nodes or [])[:DEFAULT_NODE_LIMIT]
    node_meta = []
    for i, n in enumerate(capped_nodes):
        node_meta.append({
            "node_id": (node_ids[i] if node_ids and i < len(node_ids) else f"node_{i}"),
            "poi_count": len(n.get("pois", [])),
            "time_window": (n.get("context", {}) or {}).get("trip_window", {}),
            "timezone": (n.get("meta", {}) or {}).get("timezone")
        })

    payload: JSONDict = {
        "meta": {
            "session_id": session_id,
            "timestamp": int(time.time()),
            "instruction": (
                "You are a trip-plan merger. Given multiple candidate plan-nodes and user constraints, "
                "produce ONE unified, conflict-free itinerary covering the date range. "
                "Respect daily time windows, travel feasibility, closures, and user interests/budget/pace. "
                "Do not explain. Output strictly in JSON matching the expected schema."
            )
        },
        "user_ctx": user_ctx,
        "nodes": capped_nodes,
        "nodes_meta": node_meta,
        "expected_output_schema": {
            "meta": {"session_id":"string","generated_at":"int","llm":"string","version":"string"},
            "sources": [{"node_id":"string","used_pois":["string"]}],
            "plan": {
                "date_range":["string","string"],
                "timezone":"string",
                "kpis":{"walk_km":"float","cost_estimate":"float","attractions":"int","confidence":"float"},
                "days":[
                    {
                        "date":"string",
                        "city":"string",
                        "items":[
                            {
                                # either a scheduled activity...
                                "start":"HH:MM","end":"HH:MM","title":"string",
                                "poi_id":"string|null","location":{"lat":"float","lng":"float"},"note":"string|optional",
                                # ...or a transfer record
                                # {"transfer":{"mode":"walk|drive|transit","eta_min":"int","polyline":"string|optional"}}
                            }
                        ],
                        "lodging":{"name":"string","address":"string","checkin_time":"HH:MM","note":"string|optional"},
                        "meals":[{"time":"HH:MM","type":"breakfast|lunch|dinner","place":"string","note":"string|optional"}]
                    }
                ]
            }
        }
    }
    return payload

def merge_trip_nodes_with_llm(
    *,
    session_id: str,
    nodes: List[JSONDict],
    user_ctx: JSONDict,
    llm_planner: Optional[Callable[[JSONDict], JSONDict]] = None,
    llm_response: Optional[JSONDict] = None,
    llm_name: str = "gemini-1.5-pro"
) -> JSONDict:
    """Merge candidate nodes into a unified itinerary using an external LLM."""
    prompt_payload = build_planner_prompt_payload(
        session_id=session_id,
        nodes=nodes,
        user_ctx=user_ctx
    )

    # Acquire LLM output
    result = llm_response
    if result is None:
        if llm_planner is None:
            # TODO: Implement your Gemini API call here if not using a callback.
            # result = call_gemini_json(prompt_payload, model=llm_name, api_key=...)
            raise RuntimeError("No llm_response provided and llm_planner is None.")
        result = llm_planner(prompt_payload)  # must return a dict following expected_output_schema

    # Minimal passthrough (no local edits)
    unified = result

    return {
        "meta": {"session_id": session_id, "generated_at": int(time.time()), "llm": llm_name},
        "prompt_payload": prompt_payload,
        "llm_result": result,
        "unified_plan": unified
    }

# ---- Minimal dry run (no external call) ----
if __name__ == "__main__":
    # Fake inputs
    nodes = [
        {
            "meta": {"session_id":"s1","generated_at":1690000000,"locale":"en","timezone":"Europe/Madrid"},
            "context": {"trip_window":{"start":"2025-10-10","end":"2025-10-12"}},
            "pois": [{"poi_id":"sfam","name":"Sagrada Familia","coords":{"lat":41.4036,"lng":2.1744},"score":0.9}],
            "routing_hints": {"center":{"lat":41.39,"lng":2.17}}
        },
        {
            "meta": {"session_id":"s1","generated_at":1690001000,"locale":"en","timezone":"Europe/Madrid"},
            "context": {"trip_window":{"start":"2025-10-10","end":"2025-10-12"}},
            "pois": [{"poi_id":"batllo","name":"Casa Batlló","coords":{"lat":41.3917,"lng":2.1649},"score":0.85}],
            "routing_hints": {"center":{"lat":41.39,"lng":2.17}}
        }
    ]
    user_ctx = {
        "session_id": "s1",
        "timezone": "Europe/Madrid",
        "locale": "en",
        "date_range": ["2025-10-10","2025-10-12"],
        "daily_time_window": {"from":"09:30","to":"19:00"},
        "budget": "medium",
        "pace": "relaxed",
        "max_walk_km_per_day": 8,
        "interests": ["architecture","local_food"]
    }

    # Fake LLM output (pretend Gemini returned this)
    fake_llm = {
      "meta": {"session_id": "s1", "generated_at": int(time.time()), "llm": "gemini-1.5-pro", "version":"1.0"},
      "sources": [{"node_id":"node_0","used_pois":["sfam"]},{"node_id":"node_1","used_pois":["batllo"]}],
      "plan": {
        "date_range": ["2025-10-10","2025-10-12"],
        "timezone": "Europe/Madrid",
        "kpis": {"walk_km": 7.2, "cost_estimate": 180.0, "attractions": 6, "confidence": 0.86},
        "days": [
          {
            "date": "2025-10-10",
            "city": "Barcelona",
            "items": [
              {"start":"09:45","end":"11:15","title":"Sagrada Familia","poi_id":"sfam","location":{"lat":41.4036,"lng":2.1744},"note":"Book skip-the-line"},
              {"transfer":{"mode":"walk","eta_min":15}},
              {"start":"12:00","end":"13:00","title":"Lunch","category":"dining","place":"Local Bistro","note":"Menu del día"}
            ],
            "lodging": {"name":"Hotel ABC","address":"Eixample","checkin_time":"15:00"}
          },
          {
            "date": "2025-10-11",
            "city": "Barcelona",
            "items": [
              {"start":"10:00","end":"11:30","title":"Casa Batlló","poi_id":"batllo","location":{"lat":41.3917,"lng":2.1649}},
              {"transfer":{"mode":"walk","eta_min":10}},
              {"start":"12:00","end":"13:00","title":"Tapas","category":"dining","place":"Bar XYZ"}
            ],
            "lodging": {"name":"Hotel ABC","address":"Eixample","checkin_time":"15:00"}
          }
        ]
      }
    }

    out = merge_trip_nodes_with_llm(
        session_id="s1",
        nodes=nodes,
        user_ctx=user_ctx,
        llm_response=fake_llm
    )
    print(out)
