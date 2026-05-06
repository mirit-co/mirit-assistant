# Wear Cycles & Laundry Math

How many wears between washes, and how to calculate minimum item counts.

## Default wear cycles

| `subcategory` / type | Wears before wash | `wear_cycle_days` (assuming 1 wear/day) |
|---|---|---|
| Underwear, socks | 1 | 1 |
| Undershirts | 1 | 1 |
| Workout / activewear | 1 | 1 |
| Bras | 2–4 | 2 |
| `tee`, `tank`, `bodysuit` (next-to-skin) | 1–2 | 1 |
| `long_sleeve_tee`, `henley` (next-to-skin) | 1–2 | 1 |
| `button_down`, `blouse` (next-to-skin) | 1–2 | 2 |
| `polo` | 1–2 | 1 |
| `sweater_pullover`, `turtleneck` worn against skin | 1–2 | 2 |
| `sweater_over` worn over a shirt | 5–7 (or until soiled) | 5 |
| `cardigan`, `blazer`, `vest` | 5–6 | 5 |
| `hoodie`, `sweatshirt` | 2–3 | 2 |
| `jeans_*` | 4–5 (some stretch to 10+) | 4 |
| `chinos`, `trousers`, `dress_pants` | 2–3 | 2 |
| `joggers`, `leggings` | 2–3 (or 1 if used for workouts) | 2 |
| `shorts` | 1–2 | 1 |
| `skirt_*` (lined or fabric-dependent) | 3–5 | 3 |
| `dress_*` (next-to-skin) | 1–3 (fabric-dependent) | 2 |
| `trench`, `wool_coat`, `peacoat` | 30+ (seasonal cleaning) | 30 |
| `parka`, `puffer`, `raincoat` | 30+ | 30 |
| `denim_jacket_heavy`, `leather_jacket` | 10+ | 10 |
| Pajamas | 3–4 | 3 |
| Shoes | not laundered, but rotate to extend life | n/a |

These are general guidelines. Sweat level, climate (hot/humid), fabric type,
and personal odor sensitivity all modulate them. The user can override
defaults per item.

## Minimum item counts per category, given laundry frequency

Formula:
```
min_count = ceil(days_between_washes / wear_cycle_days)
```

If the user does laundry **once per week (every 7 days)** and wears items
roughly 1× per day in their category, the minimums are:

| Category | wear cycle | min count for weekly laundry |
|---|---|---|
| Underwear (per pair) | 1 | 7 |
| Socks (per pair) | 1 | 7 |
| Bras | 2 | 3–4 (rotate to let elastic recover) |
| Next-to-skin tops (tee, tank, etc.) | 1 | 7 (or 4 if worn 2× each) |
| Button-downs / blouses | 2 | 4 |
| Sweaters worn over | 5 | 1–2 |
| Cardigans / blazers / vests | 5 | 1–2 |
| Jeans | 4 | 1–2 pairs |
| Trousers / chinos | 2 | 3–4 pairs total |
| Workout sets | 1 | 1 per workout day |
| Pajamas | 3 | 2–3 sets |

**Realistic targets** for a year-round capsule wardrobe matching weekly laundry:
- 7+ pairs of underwear and socks
- 2–3 bras (if applicable)
- 7+ next-to-skin tops total (across categories)
- 3–4 pairs of bottoms total
- 1–2 pairs of jeans
- 1–2 layering pieces per active season
- 1 outerwear piece per active season

## Laundry math in the weekly capsule (Phase 4)

When picking daily outfits, track each item's "in laundry" status:

```
for each day in week:
  for each slot in chosen formula:
    pick item from pool where:
      - item.season fits day.weather
      - item.formality matches formula
      - item.last_worn_day + item.wear_cycle_days <= today

  for each item picked:
    item.last_worn_day = today
```

If no item satisfies the constraint for a slot, that's the laundry-headroom
failure. Two responses:

1. **Reduce the constraint** — if the user has 2 jeans and a 4-day wear
   cycle, picking jeans on days 1 and 5 works; picking on days 1, 4, 5
   fails. Suggest swapping in a non-jeans bottom on day 4.

2. **Flag a structural gap** — if no rearrangement avoids the conflict,
   tell the user: "you need ≥2 of [category] for weekly laundry to work
   without re-wearing items inside their wear cycle."

## Mid-week laundry (resetting cycles)

If the user does laundry mid-week (e.g., Saturday for a Mon–Sun cycle),
items washed that day are available again from the next day. The capsule
logic should reset `last_worn_day` for washed items.

By default assume Sunday-evening laundry → all items available Monday
morning. Confirm with the user if their schedule differs.

## Stretching wear cycles (user choice)

Many users stretch wear cycles to reduce laundry volume:
- **Jeans**: many wear 7–14× before washing (with airing between wears).
  This is fine for indigo/dark denim; light denim shows wear sooner.
- **Sweaters worn against skin**: airing them between wears extends to 3–5×.
- **Wool**: naturally odor-resistant; air-out between wears, wash only when
  visibly soiled.

If the user says "I wear my jeans 10× before washing," respect it and set
`wear_cycle_days: 10` for those items. Don't lecture.

## Special cases

- **Workout clothes**: always 1 wear per wash. No stretching.
- **Anything sweat-soaked**: 1 wear per wash regardless of the table.
- **White / very light items**: 1 wear next-to-skin to avoid yellowing.
- **Silk, cashmere, fine wool**: hand-wash or dry-clean — long wear cycles
  but expensive to launder, factor that into rotation.
- **Travel**: wear cycles often compress (hotel laundry expensive); pack
  with shorter cycles in mind.

## Putting it together — example

User's week: laundry on Sunday, weekly cycle.

Inventory: 5 tees, 2 jeans, 1 chinos, 2 cardigans, 1 blazer, 2 sneakers.

Wear-cycle map:
- 5 tees, cycle 1 → 5 days of fresh tees, then need to wash or repeat
- 2 jeans, cycle 4 → can wear A-day1, B-day2, A-day5, B-day6 (no conflict)
  - or A-day1, A-day2 (back-to-back), B-day3, B-day4, then both in laundry
- 1 chinos, cycle 2 → wear day 3 and day 6, fine
- Cardigans/blazer cycle 5 → freely interchangeable, no wash needed in week

Conclusion: tops are the bottleneck. Either wash mid-week (Wednesday rinse),
add 2 more tees, or wear some tees 2 days in a row (acceptable if not
sweat-soaked).
