# Outfit Formulas

A formula is a reusable outfit template: `top + bottom + third piece + shoe (+ outer layer)`.
Phase 3 uses these to score whether an item slots into ≥1 formula.
Phase 4 uses them to pick daily outfits.

Each formula specifies:
- **Slots** — what kinds of items fill each role
- **Formality range** — what formality levels work for the formula
- **Weather** — when the formula applies
- **Activity** — what bucket(s) it serves

## How to read a formula

```
[slot]: <kind>(formality 2–3, season ?)
```

For each slot, the kind narrows what items can fill it. Items in
`inventory.json` qualify if their `subcategory`, `formality`, and `season`
match the slot's constraints.

---

## Casual formulas (formality 1–2)

### F1. Casual core

```
top:    tee | tank | henley | long_sleeve_tee (formality 1–2)
bottom: jeans_* | chinos | shorts (formality 1–2)
third:  none | denim_jacket_heavy | cardigan | sweatshirt (formality 1–2)
shoe:   sneaker | sandal_flat | flat_ballet (formality 1–2)
outer:  optional, season-dependent
```
**Activity:** casual, errands, weekends, casual WFH
**Weather:** any (third piece + outer adjust for temperature)
**Notes:** the workhorse formula. Most casual wardrobes live here.

### F2. Athleisure-polished

```
top:    tee | hoodie | sweatshirt (formality 1–2)
bottom: joggers | leggings | shorts (formality 1–2)
third:  bomber | light_jacket | none (formality 2)
shoe:   sneaker | athletic_shoe (formality 1–2)
```
**Activity:** WFH, errands, light social
**Weather:** any
**Notes:** clean version of athleisure — no logos, fitted joggers (not baggy).

### F3. Weekend layered

```
top:    long_sleeve_tee | henley | turtleneck (formality 2)
bottom: jeans_* | chinos (formality 2)
third:  cardigan | flannel_shirt | denim_jacket_heavy (formality 2)
shoe:   sneaker | boot_chelsea | boot_ankle (formality 2)
outer:  field_jacket | wool_coat (cool seasons)
```
**Activity:** casual, weekend, social-casual
**Weather:** cool to cold

---

## Smart-casual formulas (formality 3)

### F4. Smart-casual core

```
top:    button_down | blouse | polo | knit_pullover (formality 3)
bottom: chinos | dress_pants | jeans_dark_straight | skirt_midi (formality 3)
third:  cardigan | blazer | vest (formality 3)
shoe:   loafer | mule | flat_ballet | boot_ankle (formality 3)
```
**Activity:** office (casual), client meetings (informal), nice dinners, dates
**Weather:** any
**Notes:** the modern office default. Dark jeans + button-down + blazer is
the canonical "elevated casual."

### F5. Polished monochrome

```
top:    knit_pullover | turtleneck | mock_neck (formality 3)
bottom: trousers | dress_pants | skirt_pencil — same color family as top (formality 3)
third:  blazer | wool_coat — contrast color (formality 3)
shoe:   loafer | boot_chelsea | heel_block (formality 3)
```
**Activity:** office, dinner, social
**Weather:** any
**Notes:** column-of-color = lengthening, polished. Single contrasting third
piece adds visual interest without breaking the silhouette.

### F6. Dress + layer

```
top + bottom: dress_midi | dress_mini (formality 3)
third:        cardigan | blazer | denim_jacket_heavy (formality 2–3)
shoe:         flat_ballet | mule | boot_ankle | heel_block (formality 3)
outer:        season-dependent
```
**Activity:** social, casual office, daytime events
**Weather:** any (layers manage temperature)

---

## Business formulas (formality 4)

### F7. Business standard

```
top:    button_down | blouse | knit_pullover (formality 4)
bottom: dress_pants | trousers | skirt_pencil (formality 4)
third:  blazer | suit_jacket (formality 4)
shoe:   loafer | oxford | heel_pump (formality 4)
```
**Activity:** in-office (formal dress code), important client meetings
**Weather:** any (with appropriate outerwear)

### F8. Business-casual hybrid

```
top:    button_down | knit_pullover (formality 3–4)
bottom: dark_jeans_straight | chinos | trousers (formality 3)
third:  blazer | wool_cardigan (formality 3–4)
shoe:   loafer | boot_chelsea | oxford (formality 3–4)
```
**Activity:** modern office (no strict dress code), client calls,
work-then-dinner days
**Weather:** any

---

## Active / specialty formulas

### F9. Workout

```
top:    activewear top | tank
bottom: leggings | shorts | joggers (athletic)
shoe:   athletic_shoe
outer:  optional zip-up or windbreaker
```
**Activity:** exercise, sports
**Notes:** kept separate from main capsule; flag items as `activewear` category.

### F10. Rainy day

```
top:    any (formality 2–4)
bottom: any (avoid suede, light fabrics)
third:  optional
shoe:   waterproof: boot_chelsea | boot_ankle | rain-rated sneaker
outer:  raincoat | trench (treated)
```
**Activity:** any
**Weather:** rain, wet
**Notes:** weather override formula — applies on top of an underlying activity
formula. Swaps the shoe and outer layer.

### F11. Cold day (winter)

```
top:    base layer + mid-knit (turtleneck or thermal under sweater_pullover)
bottom: trousers | jeans_straight | wool trousers (mid/heavy weight)
third:  blazer | wool_cardigan | vest (mid layer)
shoe:   boot_ankle | boot_chelsea | boot_knee (insulated)
outer:  wool_coat | parka | puffer
acc:    scarf_wool | beanie | gloves
```
**Activity:** any
**Weather:** cold, <10°C
**Notes:** weather override. The base/mid/outer layering system is critical
for indoor/outdoor temp deltas.

### F12. Hot day (summer)

```
top:    tee | tank | linen blouse (lightweight only)
bottom: shorts | linen pants | midi skirt (lightweight)
third:  none — third piece is the fabric texture, not an extra layer
shoe:   sandal_flat | espadrille | sneaker (breathable)
outer:  none
acc:    sun_hat | sunglasses
```
**Activity:** any
**Weather:** hot, >25°C
**Notes:** weather override. The "third piece rule" relaxes here — texture
mixing (linen + cotton + leather sandal) replaces the visual third piece.

---

## Formula-fit test (used by Phase 3 scoring)

An item passes formula-fit if:
1. Its `category` and `subcategory` match a slot in ≥1 formula
2. Its `formality` falls within that formula's range
3. Its `season` overlaps the formula's weather constraint

An item failing formula-fit is decoration, not a wardrobe-functional piece.
That's not always bad — emotional anchors (a loved sentimental jacket) can
stay — but it should be flagged as "low formula utility" so the user knows.

## Formula coverage check (used by Phase 3 gap analysis)

After Phase 1, count how many formulas the inventory can fully populate.

- **Coverage = 0** in a formula corresponding to a >5% lifestyle bucket → hard gap
- **Coverage = 1** (only one possible outfit in that formula) → fragile, needs
  one more option
- **Coverage ≥ 2 versions per slot** → healthy

Formula coverage is more honest than total item count. A 50-item wardrobe
that can't make a single business outfit fails its 30%-business owner.

## Combinatorics — used carefully

Naive math:
```
outfits = T × B × (S+1) × (L+1) + D
```
where `+1` accounts for "no shoe change" / "no layer" being valid.

But raw multiplication overstates by 5–7×. The realistic count is:
```
wearable = sum over formulas of (compatible_tops × compatible_bottoms × compatible_thirds × compatible_shoes)
```
filtered by color/palette compatibility (no clashing patterns; ≤3 colors per
outfit; one base neutral anchor) and formality consistency (all slots within
±1 level).

For weekly capsule sizing: aim for ≥3× as many wearable outfits as days
in the period. A 7-day capsule needs ≥21 distinct wearable combinations
in the pool.
