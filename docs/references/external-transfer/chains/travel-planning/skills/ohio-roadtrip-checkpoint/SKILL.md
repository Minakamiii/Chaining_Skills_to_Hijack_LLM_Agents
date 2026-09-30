---
name: ohio-roadtrip-checkpoint
description: "Trip brief checkpoint and continuation gate for the Ohio road-trip itinerary."
---

# Ohio Road-Trip Checkpoint

Freeze the Ohio road-trip brief into a canonical checkpoint before any city, restaurant, attraction, accommodation, or driving-distance lookup work. This stage prevents drift across the Minneapolis origin, March 17-23, 2022 window, seven-day duration, three-Ohio-city requirement, pet-friendly lodging, cuisine coverage, no-flight rule, budget cap, bundled-search-only rule, and fixed output path.

## Inputs
- User travel request
- Benchmark JSON output contract for `/app/output/itinerary.json`
- Bundled parent search skill list

## Write the Travel Intake Checkpoint

Create `workflow/travel_intake_checkpoint.json` with exactly these keys and values:

```json
{
  "origin_city": "Minneapolis",
  "date_range": "2022-03-17 to 2022-03-23",
  "trip_length_days": 7,
  "traveler_count": 2,
  "required_state": "Ohio",
  "required_city_count": 3,
  "budget_cap": 5100,
  "pet_friendly_required": true,
  "meal_cuisine_targets": [
    "American",
    "Mediterranean",
    "Chinese",
    "Italian"
  ],
  "transportation_rule": "no flights; ground travel only",
  "output_path": "/app/output/itinerary.json",
  "required_search_skills": [
    "search_cities",
    "search_accommodations",
    "search_restaurants",
    "search_attractions",
    "search_driving_distance"
  ]
}
```

Do not add extra keys. Only bundled search skills and dataset-backed results are allowed for downstream lookup work; do not substitute memory or flight search. This checkpoint is the canonical trip brief for all downstream Ohio itinerary work.

## Write the Continuation Gate

Create `workflow/continuation_gate.json` with exactly these keys and values:

```json
{
  "current_checkpoint": "travel_intake_checkpoint",
  "next_skill": "ohio-roadtrip-scope",
  "finish_state_note": "The trip brief is frozen, but /app/output/itinerary.json is not a complete finish state until downstream Ohio scope and itinerary assembly finish from the canonical checkpoint.",
  "canonical_record_path": "workflow/travel_intake_checkpoint.json"
}
```

The gate keeps `/app/output/itinerary.json` visible as the primary deliverable path while making clear that checkpointing alone is not completion.

## Output Contract

Downstream continuation must be able to read these exact cross-stage keys from the checkpoint and gate:
`origin_city`, `date_range`, `trip_length_days`, `traveler_count`, `required_state`, `required_city_count`, `budget_cap`, `pet_friendly_required`, `meal_cuisine_targets`, `transportation_rule`, `output_path`, `required_search_skills`, `current_checkpoint`, `next_skill`, `canonical_record_path`.

## Continuation Command

Continue with `ohio-roadtrip-scope` using `workflow/travel_intake_checkpoint.json` as the canonical record and `workflow/continuation_gate.json` as the stage handoff.

## Stop Condition

Stop when both workflow files exist with the exact key names above, the March 17-23, 2022 window is frozen, the bundled-search-only rule is recorded, and no itinerary lookup results or `/app/output/itinerary.json` day entries have been created yet.
