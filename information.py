# info_aggregation_agent.py
"""
Information Aggregation Agent
- Input: results from small agents (weather, search, maps, etc.) + RAG info
- Output: single JSON structure ready for prompt injection
- This is a skeleton: all actual fetching logic is outside
"""

from typing import Dict, Any, Optional, List
import time

JSONDict = Dict[str, Any]

def aggregate_info(
    session_id: str,
    rag_info: List[JSONDict],
    weather_info: Optional[JSONDict] = None,
    search_info: Optional[List[JSONDict]] = None,
    maps_info: Optional[JSONDict] = None
) -> JSONDict:
    """
    Inputs:
        - session_id: unique id for user/session
        - rag_info: list of POIs from RAG DB
        - weather_info: dict from weather agent
        - search_info: list of dicts from search agent
        - maps_info: dict from maps agent
    Output:
        - normalized JSON with everything aggregated
    """

    return {
        "meta": {
            "session_id": session_id,
            "generated_at": int(time.time())
        },
        "rag": rag_info or [],
        "weather": weather_info or {},
        "search": search_info or [],
        "maps": maps_info or {},
        # optional spot for other future agents
    }

# Example usage
if __name__ == "__main__":
    # Dummy inputs (would be replaced by outputs of other agents)
    rag_info = [{"poi_id":"sfam","name":"Sagrada Familia","score":0.9}]
    weather_info = {"daily":[{"date":"2025-10-05","summary":"Sunny"}]}
    search_info = [{"title":"Wiki page","summary":"History..."}]
    maps_info = {"center":{"lat":41.4,"lng":2.17}}

    result = aggregate_info("session-123", rag_info, weather_info, search_info, maps_info)
    print(result)
