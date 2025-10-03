# mcp_image_to_place.py
import json
import time
from typing import List, Dict, Any, Optional

JSONDict = Dict[str, Any]

# ---------------------
# Config (replace with actual Key / Endpoint)
# ---------------------
CONFIG = {
    "USE_GEMINI": True,                # True: use Gemini multimodal first; False: fallback to local model + cloud APIs
    "GEMINI_API_KEY": "<YOUR_GEMINI_KEY>",
    "GOOGLE_MAPS_API_KEY": "<YOUR_GOOGLE_MAPS_KEY>",
    "SEARCH_API": "google",            # or "bing" / custom
    "CACHE_TTL_SECONDS": 24 * 3600,
    "CONFIDENCE_THRESHOLD": 0.6,      # confidence threshold for recognition
}

# ---------------------
# Simple in-memory cache (example)
# ---------------------
_cache = {}

def cache_get(key: str):
    """Return a cached payload if it is still fresh."""
    entry = _cache.get(key)
    if not entry:
        return None
    value, ts = entry
    if time.time() - ts > CONFIG["CACHE_TTL_SECONDS"]:
        _cache.pop(key, None)
        return None
    return value

def cache_set(key: str, value):
    """Store a payload in the in-memory cache with current timestamp."""
    _cache[key] = (value, time.time())

# ---------------------
# Output JSON schema (for frontend consumption)
# ---------------------
def make_output_json(original_image_id: str,
                     top_candidates: List[JSONDict],
                     chosen_place: Optional[JSONDict],
                     aggregated_info: JSONDict,
                     logs: List[str]) -> JSONDict:
    """Assemble the response JSON expected by the frontend layer."""
    return {
        "image_id": original_image_id,
        "timestamp": int(time.time()),
        "candidates": top_candidates,         # candidate landmark list from vision
        "place": chosen_place,                # final chosen place or null
        "info": aggregated_info,              # aggregated info from wiki/web/places
        "ui_hints": {                         # hints for frontend UI (buttons, warnings)
            "confidence": chosen_place.get("confidence") if chosen_place else 0.0,
            "suggested_actions": [
                {"type": "view_on_map"},
                {"type": "open_details"},
                {"type": "ask_followup"} 
            ]
        },
        "logs": logs
    }

# ---------------------
# Tool: Gemini multimodal call (stub)
# ---------------------
def call_gemini_multimodal(image_bytes: bytes, prompt: str) -> JSONDict:
    """
    TODO: Implement actual Gemini multimodal call
    - Upload image_bytes as attachment/multipart
    - prompt should instruct the model to return landmark name, coords, confidence, brief reason
    Example return:
    {
      "candidates":[{"name":"Eiffel Tower","lat":48.8584,"lng":2.2945,"confidence":0.92,"reason":"distinctive structure"}],
      "raw_text":"..."
    }
    """
    # TODO: replace with real API call
    raise NotImplementedError("call_gemini_multimodal needs implementation")

# ---------------------
# Tool: Local vision model (CLIP/BLIP) stub
# ---------------------
def local_vision_search(image_bytes: bytes, top_k: int = 5) -> List[JSONDict]:
    """
    TODO: Implement local retrieval: CLIP/BLIP matching against prebuilt landmark index
    Return candidate format same as above
    """
    return []

# ---------------------
# Tool: OCR fallback (Google OCR / Tesseract)
# ---------------------
def do_ocr(image_bytes: bytes) -> str:
    """
    TODO: Extract text from image (signs, road signs, language clues) to help recognition
    Returns plain text
    """
    return ""

# ---------------------
# Tool: Places / Geocoding (Google Maps / OpenStreetMap)
# ---------------------
def places_lookup_by_name_or_coordinate(name: Optional[str], lat: Optional[float], lng: Optional[float]) -> List[JSONDict]:
    """
    TODO: If name or coordinates are available, call Places API to get nearby info
    (opening_hours, rating, price, address, place_id)
    Returns POI list
    """
    return []

# ---------------------
# Tool: Web Search & Summarization
# ---------------------
def web_search_and_summarize(query: str, top_k: int = 3) -> List[JSONDict]:
    """
    TODO: Use Google Search / Bing / Gemini Search to fetch top_k pages,
    then summarize with LLM (Gemini): opening hours, tickets, short history, tips
    Returns:
    [{"source":"wikipedia.org/...","summary":"...","type":"official|wiki|blog","reliability":0.9}, ...]
    """
    return []

# ---------------------
# Main pipeline: process image and generate JSON
# ---------------------
def process_image_to_place_json(image_id: str, image_bytes: bytes, user_context: Optional[JSONDict] = None) -> JSONDict:
    """
    Input:
      - image_id: unique id from frontend
      - image_bytes: binary of the image
      - user_context: {"lat":..., "lng":..., "user_locale":"en-US", "date":"2025-10-03", ...} (optional)
    Output: JSON for frontend (see make_output_json)
    """
    logs = []
    cache_key = f"imghash:{image_id}"
    cached = cache_get(cache_key)
    if cached:
        logs.append("hit_cache")
        return cached

    # ---------- 1) Vision recognition: prefer Gemini multimodal ----------
    candidates = []
    try:
        if CONFIG["USE_GEMINI"]:
            logs.append("use_gemini_multimodal")
            prompt = (
                "You are an assistant that identifies landmarks in the provided image. "
                "Return JSON: candidates list with fields: name, lat, lng (optional), confidence (0-1), evidence."
            )
            gm = call_gemini_multimodal(image_bytes, prompt)
            candidates = gm.get("candidates", [])
            logs.append(f"gemini_candidates:{len(candidates)}")
    except Exception as e:
        logs.append(f"gemini_error:{str(e)}")
        # Fallback to local vision + OCR
        try:
            ocr_text = do_ocr(image_bytes)
            logs.append("ocr_done")
            local_cand = local_vision_search(image_bytes, top_k=5)
            # If OCR contains landmark names, use as hint
            if ocr_text:
                logs.append("ocr_used_for_disambiguation")
            candidates = local_cand
            logs.append(f"local_candidates:{len(candidates)}")
        except Exception as e2:
            logs.append(f"local_vision_error:{str(e2)}")
            candidates = []

    # ---------- 2) Confidence filtering & geographic disambiguation ----------
    if user_context and ("lat" in user_context and "lng" in user_context):
        user_lat, user_lng = user_context["lat"], user_context["lng"]
        # TODO: adjust candidate confidence based on distance to user
        logs.append("applied_user_location_bias")

    # If no candidates, fallback to OCR + web search
    if not candidates:
        logs.append("no_candidates_fallback_to_websearch")
        ocr_text = do_ocr(image_bytes)
        search_q = ocr_text or "landmark in image"
        web_hits = web_search_and_summarize(search_q, top_k=5)
        logs.append(f"web_hits:{len(web_hits)}")

    # ---------- 3) For top candidates, do Places lookup and web aggregation ----------
    top_candidates = sorted(candidates, key=lambda c: c.get("confidence",0), reverse=True)[:5]
    aggregated_info = {"sources": [], "places": [], "wiki": None}
    chosen_place = None
    for cand in top_candidates:
        name = cand.get("name")
        lat = cand.get("lat")
        lng = cand.get("lng")
        conf = cand.get("confidence", 0.0)

        # Query Places API if high confidence or has coordinates
        if conf >= CONFIG["CONFIDENCE_THRESHOLD"] or (lat and lng):
            logs.append(f"lookup_places_for:{name or 'coord'}")
            place_results = places_lookup_by_name_or_coordinate(name, lat, lng)
            if place_results:
                place = place_results[0]
                place["confidence"] = max(conf, place.get("match_score", conf))
                aggregated_info["places"].append(place)
                if not chosen_place:
                    chosen_place = {**cand, **place}
                    logs.append(f"chosen_place_by_places:{place.get('name')}")
                continue

        # Otherwise, fallback to web search
        if name:
            logs.append(f"websearch_for:{name}")
            summaries = web_search_and_summarize(name, top_k=3)
            aggregated_info["sources"].extend(summaries)
            if not chosen_place and summaries:
                chosen_place = {**cand, "info_summary": summaries[0]}
                logs.append(f"chosen_place_by_web:{cand.get('name')}")

    if not chosen_place and top_candidates:
        cp = top_candidates[0]
        cp["confidence"] = cp.get("confidence", 0.0)
        chosen_place = cp
        logs.append("fallback_chosen_top_candidate")

    # ---------- 4) Final synthesis: generate narrative with LLM ----------
    narrative = ""
    try:
        # TODO: call Gemini text model, input candidates + places + sources
        narrative = "TODO: call Gemini to synthesize narrative"
    except Exception as e:
        logs.append(f"narrative_error:{str(e)}")
        narrative = chosen_place.get("name", "") + " - information summary not available."

    aggregated_info["summary"] = narrative

    # ---------- 5) Final output + cache ----------
    final_json = make_output_json(
        original_image_id=image_id,
        top_candidates=top_candidates,
        chosen_place=chosen_place,
        aggregated_info=aggregated_info,
        logs=logs
    )

    cache_set(cache_key, final_json)
    return final_json

# ---------------------
# Example: pseudo REST API (Flask-like)
# ---------------------
def api_upload_image_handler(request):
    """
    POST /identify
    body: multipart form-data: image (file), image_id (str), optional user_lat,user_lng
    returns: application/json (the structure from make_output_json)
    """
    image_file = request.files.get("image")
    image_id = request.form.get("image_id") or f"img_{int(time.time())}"
    user_lat = request.form.get("user_lat")
    user_lng = request.form.get("user_lng")
    user_context = {}
    if user_lat and user_lng:
        user_context["lat"] = float(user_lat)
        user_context["lng"] = float(user_lng)

    image_bytes = image_file.read()
    try:
        result_json = process_image_to_place_json(image_id, image_bytes, user_context)
        return json.dumps(result_json), 200, {"Content-Type": "application/json"}
    except Exception as e:
        return json.dumps({"error": str(e)}), 500, {"Content-Type": "application/json"}

# ---------------------
# For unit test / local test
# ---------------------
if __name__ == "__main__":
    # TODO: Load local test image, call process_image_to_place_json, print JSON
    pass
