# Agent Overview (English)

This repository contains a set of travel-planning agents that communicate through
structured JSON payloads. Each module focuses on a single responsibility so the
overall pipeline can be orchestrated or extended as needed.

## Modules

### `final.py` — Trip Plan Merger Agent
- Accepts multiple candidate itinerary nodes plus the user context.
- Builds the merged-plan prompt payload and delegates the final decision to an
  external LLM (e.g., Gemini) via callback or pre-computed response.
- Returns the prompt, raw LLM output, and unified plan bundle for downstream use.

### `imagesearch.py` — Image-to-Place Agent
- Identifies landmarks from an uploaded photo using Gemini multimodal first, then
  falls back to local vision, OCR, and web search.
- Aggregates Places API data, web summaries, and narrative hints for the top
  candidates.
- Exposes a helper that formats the complete JSON response for front-end or API
  callers.

### `information.py` — Information Aggregation Agent
- Receives outputs from weather, search, maps, and RAG sub-agents.
- Produces a normalized JSON packet with session metadata so the information can
  be injected into LLM prompts or stored.

### `plan.py` — Single-POI Prompt Agent
- Configures prompt parameters for a lightweight Gemini call that produces a
  single attraction visit plan.
- Constructs the strict JSON-only prompt, invokes the (stubbed) LLM call, and
  validates the response parses as JSON before returning it.

### `rag.py` & `userchoice.py` — Request Normalization Agents
- Provide ADK-style templates that collect raw user text and options, call Gemini
  to infer intent/constraints, and emit a normalized spec for downstream tools.
- Include defaults for user preferences and provenance metadata so later agents
  share the same contract.

### `weightadjustment.py` — Weight Adjustment Agent
- Sends ratings and existing component weights to Gemini, requesting updated
  global/user weights under simple constraints.
- Wraps the resulting policy decision together with the original prompt payload
  and metadata for auditing.

## Suggested Flow
1. Normalize the user request (`rag.py` or `userchoice.py`).
2. Collect factual signals (RAG, search, weather) and aggregate them
   (`information.py`).
3. Generate or merge itineraries (`plan.py` for single POI, `final.py` for multi-day
   plans).
4. Refine weightings based on feedback (`weightadjustment.py`).
5. Identify places directly from user photos when needed (`imagesearch.py`).

Each component is a scaffold with TODO markers where real API integrations and
business logic can be added.

