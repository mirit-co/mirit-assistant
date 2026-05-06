# Taxonomy

Controlled vocabulary for tagging clothing items. Use these exact strings in
`inventory.json` so later phases can filter and group reliably.

## Top-level categories

| `category` value | What goes here |
|---|---|
| `top` | T-shirts, tanks, blouses, button-downs, sweaters worn next-to-skin |
| `bottom` | Jeans, trousers, chinos, leggings, joggers, shorts, skirts |
| `dress` | Dresses, jumpsuits, rompers, overalls (one-pieces) |
| `outerwear` | Coats, parkas, raincoats, heavy jackets — full outdoor protection |
| `layer` | Cardigans, blazers, vests, sweaters worn over a base — the "third piece" |
| `shoe` | All footwear |
| `accessory` | Bags, belts, scarves, hats, jewelry, watches, sunglasses, ties |
| `activewear` | Workout-specific tops, leggings, shorts, sports bras |
| `loungewear` | Home-only items — tag `excluded_from_capsule: true` |
| `sleepwear` | Pajamas, robes — tag `excluded_from_capsule: true` |
| `underwear` | Underwear, bras, socks, hosiery, undershirts — tag `excluded_from_capsule: true` |

## Subcategories

### Tops (`category: "top"`)
`tee`, `tank`, `long_sleeve_tee`, `button_down`, `blouse`, `polo`, `henley`,
`bodysuit`, `tunic`, `sweater_pullover`, `turtleneck`, `mock_neck`, `hoodie`,
`sweatshirt`

### Bottoms (`category: "bottom"`)
**Jeans:** `jeans_skinny`, `jeans_straight`, `jeans_wide_leg`, `jeans_bootcut`,
`jeans_relaxed`, `jeans_mom`
**Pants:** `trousers`, `chinos`, `dress_pants`, `leggings`, `joggers`, `shorts`
**Skirts:** `skirt_mini`, `skirt_midi`, `skirt_maxi`, `skirt_pencil`,
`skirt_a_line`, `skirt_pleated`

### Dresses (`category: "dress"`)
`dress_mini`, `dress_midi`, `dress_maxi`, `jumpsuit`, `romper`, `overalls`

### Outerwear (`category: "outerwear"`)
`trench`, `peacoat`, `parka`, `puffer`, `raincoat`, `wool_coat`,
`leather_jacket`, `denim_jacket_heavy`, `field_jacket`, `windbreaker`

### Layers (`category: "layer"`)
`cardigan`, `blazer`, `vest`, `sweater_over` (a sweater worn on top of a tee
or shirt as a third piece), `kimono`, `light_jacket`

### Shoes (`category: "shoe"`)
`sneaker`, `loafer`, `flat_ballet`, `mule`, `oxford`, `boot_ankle`,
`boot_chelsea`, `boot_knee`, `heel_pump`, `heel_block`, `heel_kitten`,
`sandal_flat`, `sandal_heel`, `espadrille`, `slipper`, `athletic_shoe`,
`hiking_boot`

### Accessories (`category: "accessory"`)
**Bags:** `bag_tote`, `bag_crossbody`, `bag_clutch`, `bag_backpack`,
`bag_briefcase`, `bag_weekender`
**Belts:** `belt_leather`, `belt_fabric`, `belt_statement`
**Scarves:** `scarf_silk`, `scarf_wool`, `bandana`
**Hats:** `cap_baseball`, `beanie`, `fedora`, `sun_hat`
**Jewelry:** `necklace`, `earrings`, `bracelet`, `ring`, `watch`
**Other:** `sunglasses`, `tie`, `bow_tie`, `pocket_square`

## Per-item attributes

Every item in `inventory.json` should have these fields. Required fields are
marked **R**; optional but recommended are **O**.

| Field | Type | Values | Notes |
|---|---|---|---|
| `id` **R** | string | `top-001`, `btm-003`, etc. | Stable across sessions |
| `category` **R** | string | from top-level table above | |
| `subcategory` **R** | string | from subcategory list above | |
| `color_primary` **R** | string | see color list below | |
| `color_secondary` | string | see color list below | For 2-color items |
| `pattern` **R** | string | `solid`, `stripe_horizontal`, `stripe_vertical`, `plaid`, `check`, `floral`, `polka_dot`, `animal`, `geometric`, `abstract`, `graphic`, `camo` | |
| `pattern_scale` | string | `micro`, `small`, `medium`, `large` | Only if `pattern != solid` |
| `material_guess` **R** | string | `cotton`, `linen`, `wool`, `cashmere`, `silk`, `polyester`, `viscose`, `nylon`, `denim`, `leather`, `suede`, `synthetic_blend`, `unknown` | Best guess from photo |
| `fabric_weight` | string | `lightweight`, `midweight`, `heavyweight` | |
| `fit` **R** | string | `slim`, `regular`, `relaxed`, `oversized` | |
| `silhouette` | string | `fitted`, `structured`, `flowy`, `drapey` | |
| `formality` **R** | int 1–5 | 1=lounge, 2=casual, 3=smart-casual, 4=business, 5=formal | See scale below |
| `season` **R** | array of strings | any of `spring`, `summer`, `fall`, `winter`, `all_season` | |
| `layering_position` | string | `base`, `mid`, `outer`, `n/a` | For tops/layers/outerwear |
| `neckline` | string | `crew`, `v_neck`, `scoop`, `mock`, `turtle`, `boat`, `off_shoulder`, `halter`, `square`, `sweetheart`, `collared`, `n/a` | For tops/dresses |
| `sleeve_length` | string | `sleeveless`, `cap`, `short`, `three_quarter`, `long`, `n/a` | For tops/dresses |
| `rise` | string | `low`, `mid`, `high`, `n/a` | For bottoms |
| `length` | string | `cropped`, `regular`, `long`, `mini`, `midi`, `maxi`, `n/a` | |
| `condition` **O** | string | `new`, `excellent`, `good`, `fair`, `retire_soon` | |
| `style_tags` **O** | array | from archetype menu in `methodologies.md` | e.g., `["minimalist","sharp"]` |
| `wear_cycle_days` **O** | int | from `wear-cycles.md` defaults | Days "in laundry" after wear |
| `excluded_from_capsule` **O** | bool | `true` for sleepwear/loungewear/underwear | |
| `confidence` **O** | object | `{material: "low", fit: "high", ...}` | Mark fields you're unsure about |
| `notes` **O** | string | free text | "from photo IMG_1234, has small stain on hem" |

## Color list (controlled vocabulary)

Use these exact strings for `color_primary` and `color_secondary`. Group by
neutrals vs. main colors vs. accents — this lets later phases compute palette
balance.

**Neutrals:** `black`, `white`, `cream`, `ivory`, `light_grey`, `mid_grey`,
`dark_grey`, `charcoal`, `beige`, `tan`, `camel`, `taupe`, `brown`, `chocolate`,
`navy`, `denim_light`, `denim_mid`, `denim_dark`

**Main colors:** `red`, `burgundy`, `pink`, `coral`, `orange`, `rust`,
`yellow`, `mustard`, `gold`, `green`, `olive`, `forest_green`, `mint`,
`teal`, `blue`, `royal_blue`, `light_blue`, `purple`, `lavender`, `magenta`

**Metallic/special:** `silver`, `gold_metal`, `rose_gold`

**Pattern-dominant:** `multicolor` (when no single primary color dominates)

## Formality scale (5 levels)

Use the `formality` field as an integer 1–5:

| Level | Name | Examples |
|---|---|---|
| 1 | Lounge | Sweatpants at home, oversized tee, slippers |
| 2 | Casual | Jeans + tee + sneakers, athleisure as outerwear |
| 3 | Smart-casual | Chinos + button-down + loafers, midi dress + cardigan |
| 4 | Business | Tailored trousers + button-down + blazer + dress shoes |
| 5 | Formal | Suit, formal dress, dress shoes only |

Items within ±1 level of each other can be mixed in the same outfit.
Mixing level 2 and level 4 in one outfit usually fails (sneakers + suit) —
the formula library in `outfit-formulas.md` flags exceptions where this works.

## Sizing tips for photo-based inventory

- **Color is hardest** under non-neutral lighting. If unsure, ask the user
  to confirm the basic color family (e.g., "is this navy or black?").
- **Material is mostly a guess.** Ask the user only when it matters — for
  outerwear (waterproof?), knits (wool vs. acrylic?), and shoes
  (leather vs. synthetic?).
- **Fit is observable** if the item is on a person or hanger; impossible if
  it's folded. Mark folded items as `confidence.fit: "low"`.
- **Formality requires context.** A black t-shirt is level 2 casual; a
  black silk t-shirt with elegant draping is level 3. Use material + cut
  context together.

## Examples

### A canonical inventory entry

```json
{
  "id": "top-003",
  "category": "top",
  "subcategory": "button_down",
  "color_primary": "white",
  "color_secondary": null,
  "pattern": "solid",
  "material_guess": "cotton",
  "fabric_weight": "midweight",
  "fit": "regular",
  "silhouette": "structured",
  "formality": 3,
  "season": ["all_season"],
  "layering_position": "base",
  "neckline": "collared",
  "sleeve_length": "long",
  "condition": "excellent",
  "style_tags": ["classic", "minimalist"],
  "wear_cycle_days": 2,
  "confidence": {"material": "high", "fit": "high"},
  "notes": "from photo IMG_1234"
}
```

### Edge case: same item, two photos

```json
{
  "id": "out-001",
  "category": "outerwear",
  "subcategory": "trench",
  "color_primary": "camel",
  "pattern": "solid",
  "material_guess": "cotton",
  "fabric_weight": "midweight",
  "fit": "regular",
  "formality": 3,
  "season": ["spring", "fall"],
  "layering_position": "outer",
  "notes": "from photos IMG_1241 (front) and IMG_1242 (back)"
}
```
