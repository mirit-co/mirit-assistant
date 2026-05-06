# Schemas

JSON structures for the working files in `wardrobe/`. Use these field names
exactly — later phases assume they're stable.

## inventory.json

```json
{
  "version": 1,
  "created_at": "2026-05-05T10:00:00Z",
  "updated_at": "2026-05-05T10:00:00Z",
  "items": [
    {
      "id": "top-001",
      "category": "top",
      "subcategory": "tee",
      "color_primary": "white",
      "color_secondary": null,
      "pattern": "solid",
      "pattern_scale": null,
      "material_guess": "cotton",
      "fabric_weight": "lightweight",
      "fit": "regular",
      "silhouette": "fitted",
      "formality": 2,
      "season": ["spring", "summer", "fall"],
      "layering_position": "base",
      "neckline": "crew",
      "sleeve_length": "short",
      "rise": null,
      "length": "regular",
      "condition": "excellent",
      "style_tags": ["minimalist", "classic"],
      "wear_cycle_days": 1,
      "excluded_from_capsule": false,
      "confidence": {"material": "high", "fit": "high"},
      "photo_url": "https://storage.cloud.google.com/rstestbucketname/capsule/IMG_1201.png",
      "notes": "from photo IMG_1201"
    }
  ]
}
```

## preferences.json

```json
{
  "version": 1,
  "updated_at": "2026-05-05T10:30:00Z",
  "lifestyle_pie": {
    "work_in_office": 0.20,
    "work_from_home": 0.30,
    "casual": 0.20,
    "exercise": 0.10,
    "social": 0.15,
    "formal": 0.00,
    "lounge": 0.05
  },
  "style_words": {
    "realistic": "minimalist",
    "aspirational": "sharp",
    "emotional": "confident"
  },
  "palette": {
    "neutrals": ["black", "white", "mid_grey"],
    "mains": ["navy", "olive"],
    "accents": ["rust"],
    "target_distribution": {"neutrals": 0.65, "mains": 0.25, "accents": 0.10}
  },
  "climate": {
    "city": "Tbilisi",
    "zone": "humid_continental",
    "summer_high_c": 32,
    "summer_low_c": 18,
    "winter_high_c": 8,
    "winter_low_c": -2,
    "indoor_outdoor_split": 0.7
  },
  "constraints": {
    "laundry_frequency_days": 7,
    "body_shape": null,
    "fit_notes": null,
    "budget_monthly_usd": null
  },
  "pain_points": [
    "too many shirts I never wear",
    "no good rainy-day outfit"
  ],
  "favorite_items": ["top-007", "btm-001", "shoe-002"]
}
```

Notes:
- `lifestyle_pie` values should sum to ~1.0
- `palette.target_distribution` is the *aspirational* split; the actual
  inventory split may differ — Phase 3 surfaces the gap
- Any field can be `null` if the user hasn't specified — never invent values

## scoring.json

```json
{
  "version": 1,
  "scored_at": "2026-05-05T11:00:00Z",
  "items": [
    {
      "id": "top-001",
      "pair_count": 18,
      "formula_fit": ["casual_core", "athleisure_polished"],
      "lifestyle_fit_score": 0.85,
      "versatility_test_passed": true,
      "recommendation": "keep_high_versatility",
      "rationale": "Pairs with 18 items across 2 outfit formulas. Serves the user's 50% casual+WFH life ratio."
    },
    {
      "id": "drs-002",
      "pair_count": 0,
      "formula_fit": [],
      "lifestyle_fit_score": 0.0,
      "versatility_test_passed": false,
      "recommendation": "archive_candidate",
      "rationale": "Formal cocktail dress; user has 0% formal events. Pairs with no current shoes for full outfit."
    }
  ],
  "gap_analysis": {
    "lifestyle_gaps": [
      {"activity": "work_from_home", "life_pct": 0.30, "wardrobe_pct": 0.10, "gap": "under"}
    ],
    "structural_gaps": [
      "tops_to_bottoms_ratio_low",
      "no_third_piece_at_smart_casual"
    ],
    "buy_recommendations": [
      {"item": "smart cardigan in mid_grey or charcoal", "fills_gap": "no_third_piece_at_smart_casual", "priority": "high"}
    ]
  }
}
```

`recommendation` enum values:
- `keep_high_versatility` — score well on all four metrics
- `keep_workhorse` — high lifestyle fit + pair count, low style score is OK
- `keep_statement` — low pair count is OK if formula fit + emotional anchor
- `archive_candidate` — low scores; recommend archiving but ask first
- `decluttering_candidate` — low scores AND user said they don't wear it

## Weekly capsule file

Path: `wardrobe/capsules/{YYYY}-W{WW}.json` (ISO week number).

```json
{
  "version": 1,
  "week": "2026-W19",
  "generated_at": "2026-05-05T12:00:00Z",
  "city": "Tbilisi",
  "weather_summary": [
    {"day": "Mon", "date": "2026-05-04", "high_c": 18, "low_c": 12, "precip": "rain", "wind": "moderate"},
    {"day": "Tue", "date": "2026-05-05", "high_c": 17, "low_c": 11, "precip": "rain", "wind": "moderate"},
    {"day": "Wed", "date": "2026-05-06", "high_c": 24, "low_c": 16, "precip": "none", "wind": "low"},
    {"day": "Thu", "date": "2026-05-07", "high_c": 26, "low_c": 17, "precip": "none", "wind": "low"},
    {"day": "Fri", "date": "2026-05-08", "high_c": 23, "low_c": 15, "precip": "none", "wind": "low"},
    {"day": "Sat", "date": "2026-05-09", "high_c": 22, "low_c": 15, "precip": "none", "wind": "low"},
    {"day": "Sun", "date": "2026-05-10", "high_c": 21, "low_c": 14, "precip": "none", "wind": "low"}
  ],
  "activity_plan": [
    {"day": "Mon", "primary_activity": "work_from_home", "secondary": null},
    {"day": "Thu", "primary_activity": "work_in_office", "secondary": "social"}
  ],
  "pool": [
    "top-003", "top-007", "top-012",
    "btm-001", "btm-004",
    "lay-002", "lay-005",
    "out-001", "out-003",
    "shoe-001", "shoe-002", "shoe-004"
  ],
  "daily_anchors": [
    {
      "day": "Mon",
      "formula": "wfh_cool_layered",
      "items": ["top-007", "btm-001", "lay-002", "shoe-001", "out-001"],
      "rationale": "Cool & rainy WFH; layered for indoor/outdoor temp delta. Cardigan as third piece."
    }
  ],
  "laundry_forecast": [
    {"day": "Wed evening", "wash": ["top-003", "top-007"], "reason": "next-to-skin tops worn 1× each, batch with whites"},
    {"day": "Mon next week", "wash": ["btm-001"], "reason": "jeans worn 4×, at end of wear cycle"}
  ],
  "notes": "Pool covers 7 days with 2 backup tops. Blazer (lay-005) reserved for Thu only."
}
```

## Validation rules

When writing any of these files, sanity-check:

1. **`inventory.json`** — every `id` is unique; every `category`/`subcategory`
   pair is in `taxonomy.md`; every color is in the controlled list
2. **`preferences.json`** — `lifestyle_pie` sums to 0.95–1.05; palette has
   1–3 neutrals, 0–4 mains, 0–4 accents
3. **`scoring.json`** — every `id` exists in `inventory.json`; recommendation
   values are from the enum
4. **Weekly capsule** — every item ID in `pool` and `daily_anchors` exists
   and has `excluded_from_capsule != true`; no item appears in
   consecutive-day anchors if its `wear_cycle_days > 1`
