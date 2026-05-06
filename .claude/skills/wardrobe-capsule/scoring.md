# Scoring Rules

The Phase 3 scoring algorithm. For each item, compute four scores and combine
them into a recommendation.

## Score 1: Pair count

Number of other items in inventory that form a *valid* outfit pair with this
item. A pair is valid when:

1. **Color compatibility**: at least one of these holds:
   - Both items are neutral (any neutral pairs with any neutral)
   - One is neutral, one is non-neutral
   - Both are non-neutral but in the user's chosen palette (`palette.mains` or
     `palette.accents` from preferences.json)
   - Two non-palette colors → not compatible (skip)
2. **Pattern compatibility**:
   - Solid + anything = OK
   - Pattern + solid = OK
   - Pattern + pattern = only if scales differ (`micro` + `large` works;
     `medium` + `medium` does not) and color stories overlap
3. **Formality compatibility**: `|formality_a - formality_b| <= 1`
4. **Layering compatibility**: a top + a bottom is the base; a top + a top
   only counts if one is a `layer` (cardigan/blazer/vest) or has
   `layering_position: "outer"`

Compute pair_count for each top (vs. all bottoms), each bottom (vs. all tops),
each layer (vs. all top+bottom combos), each shoe (vs. all top+bottom combos),
each outer (vs. all complete outfits).

## Score 2: Formula fit

For each item, list which formulas in `outfit-formulas.md` it can fill at
least one slot in. Use:

```
formula_fit(item) = [f for f in formulas
                    if item.subcategory in f.slots[item.category]
                    and item.formality in f.formality_range
                    and item.season overlaps f.weather]
```

An item with `formula_fit = []` is decoration. An item with `formula_fit
length >= 2` is a multi-formula workhorse.

## Score 3: Lifestyle fit

Map the item's `formality` and typical activity to the user's lifestyle pie:

| Formality | Maps to activity buckets |
|---|---|
| 1 (lounge) | lounge, exercise (sometimes) |
| 2 (casual) | casual, work_from_home, social-casual |
| 3 (smart-casual) | work_from_home, work_in_office (modern), social, dates |
| 4 (business) | work_in_office (formal dress code), important meetings |
| 5 (formal) | formal events |

```
lifestyle_fit_score(item) = sum of pie_pct for activity buckets matching item.formality
```

Range 0–1. An item that maps only to formal events for a user with 0% formal
events scores 0. An item that maps to casual + WFH for a 60%-casual+WFH user
scores 0.6.

## Score 4: Versatility test (≥3)

Boolean. Does this item appear in ≥3 distinct wearable outfits using the rest
of the inventory?

Generate outfits by enumerating formula-slot fills with the item locked in,
then filtering for color/formality compatibility. If ≥3 distinct outfits
result, pass.

## Combining scores into a recommendation

```
if versatility_passed and lifestyle_fit_score >= 0.2 and len(formula_fit) >= 2:
    → keep_high_versatility

elif versatility_passed and lifestyle_fit_score >= 0.3:
    → keep_workhorse  # serves life even without high style score

elif len(formula_fit) >= 1 and item is emotionally significant (user said so):
    → keep_statement  # low pair count is OK for an anchor

elif lifestyle_fit_score < 0.05 and pair_count <= 2:
    → archive_candidate

elif user said "I never wear this" AND pair_count <= 2:
    → decluttering_candidate

else:
    → keep_workhorse  # default to keep when ambiguous
```

Bias toward **keep** when in doubt. Don't recommend purging without strong
evidence — the user is the final arbiter of what they're emotionally
attached to.

## Gap analysis

After scoring all items, surface two kinds of gaps.

### Lifestyle gaps

Compare lifestyle pie to wardrobe distribution:

```
wardrobe_pct[bucket] = sum(items where lifestyle_fit_score for bucket > 0) / total_items
gap[bucket] = life_pct[bucket] - wardrobe_pct[bucket]
```

- `gap > +0.15` → major UNDER (wardrobe doesn't serve life)
- `gap > +0.05` → minor UNDER
- `gap < -0.15` → major OVER (wardrobe serves a life user doesn't have —
  fantasy-self warning)
- `gap < -0.05` → minor OVER

Example: if user is 30% WFH but only 10% of wardrobe maps to that bucket,
that's a +0.20 UNDER gap → high-priority buy recommendation for
WFH-appropriate pieces.

### Structural gaps

Universal heuristics that apply regardless of lifestyle:

| Heuristic | Threshold | Meaning |
|---|---|---|
| Tops-to-bottoms ratio | <1.5 | Not enough tops for laundry rotation |
| Third pieces (layer category) at user's main formality | =0 | Outfits will look unstyled |
| Shoes spanning ≥2 formality levels | <2 | Outfit ceiling capped by footwear |
| Layering pieces for current season | =0 | Weekly capsule fails on cool/wet days |
| Color palette coherence | >40% items outside palette | Wardrobe fights itself |
| Formula coverage at >5% lifestyle bucket | =0 | Hard gap, can't make outfits for that activity |
| Outerwear for active season | =0 | Capsule fails on rain or cold |

For each gap, generate a specific buy recommendation:
- What kind of item (category + subcategory)
- What attributes it should have (color, formality, season)
- Why it fills the gap

Example:
```
{
  "item": "smart cardigan in mid_grey or charcoal, midweight, formality 3",
  "fills_gap": "no third piece at smart-casual (your dominant formality)",
  "priority": "high"
}
```

## Important: scoring is not law

These scores are inputs for a conversation with the user. Always present:

1. The score
2. The reasoning
3. The user's chance to override

Don't auto-archive items. The user is the final decision-maker — scoring is
an analytical aid, not a verdict.
