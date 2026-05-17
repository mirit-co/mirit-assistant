---
name: wardrobe-capsule
description: >
  Build and maintain a personal capsule wardrobe from photos of the user's
  clothes, then generate weekly mix-and-match outfit pools that account for
  weather, calendar, and laundry rotation. Use this skill whenever the user
  wants help with their wardrobe, clothing inventory, capsule wardrobe,
  outfit planning, "what to wear", or sends photos of their closet/clothes
  asking for organization or styling advice. Triggers include: "build a
  capsule wardrobe", "что мне носить", "собери капсулу", "разбери мой
  гардероб", "weekly outfits", "what to wear this week", "what should I
  pack", "analyze my closet", photos of clothing items with any
  organization/styling question. Always trigger this skill when the user
  uploads clothing photos and asks anything wardrobe-related, even if they
  do not say "capsule".
---

# Wardrobe Capsule Skill

Build a personal capsule wardrobe in four phases: **inventory** the user's
existing clothes from photos → **interview** them about lifestyle and style
preferences → **score** every item for versatility and surface gaps → **plan**
a 7-day mix-and-match pool that respects weather and laundry constraints.

This skill is methodology-agnostic. The major capsule frameworks (Project 333,
5-Piece French, 10×10, Curated Closet, Vivienne Files 4×4) all converge on the
same mechanics: bounded item count, neutral-anchored palette, mix-and-match
interoperability, lifestyle-matched ratios. Use the principles, recommend a
named methodology to the user only after Phase 2 once their preferences are
clear (see `references/methodologies.md`).

## Working Files

All wardrobe files are **per-user** — use the appropriate subfolder based on
who you're working with. Current users: `Ruslan`, `Mariana`.

```
wardrobe/
└── <user>/
    ├── inventory.json         # canonical item list (Phase 1)
    ├── preferences.json       # lifestyle + style profile (Phase 2)
    └── scoring.json           # per-item versatility scores (Phase 3)

data/capsule/
└── <user>/
    └── YYYY-Www.json          # weekly capsule pool (Phase 4), e.g. 2026-W19.json

data/capsula_photos/
└── <user>/
    └── IMG_XXXX.png           # source photos for inventory
```

JSON schemas for each file are in `schemas.md` (same directory as this file).
Read it before writing any of these files for the first time. Keep field names
stable across sessions — later phases assume earlier phases used the canonical names.

## Photo naming — STRICT RULES

### Filename format after recognition

After recognising a clothing item, **rename** the source file before uploading:

```
{item_id}-{short_description}_{user_slug}.png
```

- `item_id` — the canonical ID from inventory.json (e.g. `top-004`, `btm-001`)
- `short_description` — 1–3 lowercase English words joined by `_`, describing
  color + garment type (e.g. `brown_sweater`, `light_denim_shorts`, `cream_vest`)
- `user_slug` — lowercase user name (`mariana`, `ruslan`)

**Examples:**
```
top-004-brown_sweater_mariana.png
btm-001-light_denim_jeans_mariana.png
shoe-001-white_sneakers_mariana.png
acc-016-straw_hat_mariana.png
```

Update `photo_url` in inventory.json to the new filename accordingly.

### Recognition confidence — NO GUESSING

**Do NOT invent attributes you cannot see clearly.**

- If a photo is ambiguous or low-quality and the item cannot be identified
  confidently: **show the user a numbered list of hypotheses** (max 3–4 options)
  and ask "Это правильно? Выбери номер или поправь."
- Only commit the item to inventory.json **after user confirms**.
- If multiple items are visible in one photo, describe each separately and
  ask the user to confirm each one.
- Mark any unconfirmed attributes with `"confidence": "low"` in the JSON.

### Duplicate photos — DELETE them

After building inventory, some source photos may be duplicates (alternate angles
of the same item already catalogued, or intentional retakes). **Delete duplicates**
from `data/capsula_photos/<user>/` — do not keep them renamed or unnamed.

Rule: one item → one photo file. If a better photo arrives, replace the existing
file (rename + re-upload), delete the old one from GCS and locally.

## Photo URLs

Each inventory item has a `photo_url` field pointing to its source photo in
Google Cloud Storage. URLs are per-user:

```
https://storage.cloud.google.com/rstestbucketname/capsule/<user>/{renamed_filename}.png
```

Example: `https://storage.cloud.google.com/rstestbucketname/capsule/Mariana/top-007-blue_crochet_crop_mariana.png`

When adding new items from photos, rename the file to the canonical format
(see "Photo naming" above) and set `photo_url` to the new name. The `notes`
field should record the original filename: `"from photo IMG_5758 — description"`.

When presenting items to the user (outfit suggestions, checklist, inventory
review), include the photo_url so they can tap to see the item.

### Uploading new photos to GCS

Before building inventory from new photos, upload them to GCS with **200×200** resize:

```bash
python scripts/upload_capsule_photos.py <user>
# e.g.: python scripts/upload_capsule_photos.py Mariana
# Resizes to 200×200, uploads renamed files (see "Photo naming" above)
```

**Prerequisites:**
- Place the new PNG/JPG files in `data/capsula_photos/<user>/`
- GCS account: **`salakhiev.ruslan@gmail.com`** — must be the active ADC account.
  Switch if needed:
  ```bash
  gcloud config set account salakhiev.ruslan@gmail.com
  gcloud auth application-default login --account salakhiev.ruslan@gmail.com
  ```
- `GCS_BUCKET` env var (defaults to `rstestbucketname`)

The script resizes each photo to 100×100 (aspect-ratio-preserving, white-padded
to square), uploads to `capsule/<user>/<filename>.png`, and prints the public
URL for each file. Use these URLs as `photo_url` values in `inventory.json`.

## Phase 1 — Inventory

**Goal:** convert photos of clothes into a structured `inventory.json`.

### Triggering Phase 1
- User uploaded photos of clothing
- User asks to "catalog", "разобрать", "build a list of my clothes"
- `inventory.json` doesn't exist yet, or the user says "I bought new things"

### Workflow

1. **Establish photo set.** Ask the user how many photos they have and how
   they're organized (one item per photo / multiple items per photo / a
   "closet shelf" wide shot). Process them in batches of 10–20 at a time;
   long batches lose accuracy.

2. **Extract per-item attributes.** For each garment visible, record the
   fields listed in `references/taxonomy.md` §"Per-item attributes". At
   minimum: `category`, `subcategory`, `color_primary`, `color_secondary`,
   `pattern`, `material_guess`, `fit`, `formality`, `season`, `layering_position`.
   The full taxonomy with controlled vocabulary is in `references/taxonomy.md` —
   read it before tagging items so categories stay consistent.

3. **Generate stable IDs.** Use a short readable ID per item:
   `{category-prefix}-{counter}` where prefixes are `top-`, `btm-`, `drs-`,
   `out-`, `lay-`, `shoe-`, `acc-`. Example: `top-001`, `btm-003`, `out-001`.

4. **Note uncertainty.** When you can't see a tag, fabric, or fit clearly,
   guess but mark `confidence: "low"` on that field and ask the user to
   confirm or correct in a batch review at the end.

5. **Show the user a review batch** of 10–20 items in a compact table format
   (one row per item, columns: id, what you saw, color, category, formality).
   Ask: "Look right? Any corrections?" Apply corrections before committing.

6. **Write `inventory.json`** following the schema in `references/schemas.md`.

### What to do when photos are ambiguous

- Multiple items in one photo → describe each as `top-001`, `top-002`, etc.,
  noting "from photo X" in a comment field.
- Item half-hidden / on a hanger far away → ask the user to specify or skip.
- Same item in two photos (front + back) → merge into one entry, note both
  views were used.
- Activewear, loungewear, underwear, sleepwear → catalog them in their own
  categories but flag `excluded_from_capsule: true` (Project 333 convention).

### Inventory output summary

After building inventory, give the user a quick numerical summary:
- Total items by category (e.g., "12 tops, 6 bottoms, 3 dresses, 4 outerwear,
  5 shoes, 8 accessories")
- Color distribution (top 5 colors by item count)
- Formality distribution (% casual / smart-casual / business / formal)
- Anything notably missing relative to a typical balanced wardrobe

This summary is the entry point for Phase 2 — the user's reaction to it
("oh I don't actually wear those formal pieces", "huh, way more black than I
thought") is itself preference data.

## Phase 2 — Interview

**Goal:** capture the user's lifestyle and style profile in `preferences.json`.

### Workflow

Ask questions in groups, not all at once. After each group, summarize what
you heard back and confirm before moving on. Skip groups where the user has
already volunteered the info earlier in the conversation.

#### Group A: Lifestyle pie chart (most important)

Walk the user through how a typical week breaks down. The goal is a rough
% allocation across activity buckets:

- Work (in-office / hybrid / remote — these change clothing needs)
- Casual / errands / weekends
- Exercise / sports
- Social (going out, dinners, dates)
- Formal / events
- Lounging at home

This pie chart drives every later ratio. Anuschka Rees' rule: wardrobe ratios
should match life ratios, not aspirations. If a user spends 80% of their time
in casual clothes but 60% of their wardrobe is business attire, that's the
single most important finding — call it out.

#### Group B: Style profile (Three-Word Method)

Ask the user to pick three words that describe how they want to dress. Frame
it as **realistic / aspirational / emotional**:

- One word for what they actually wear most often (realistic)
- One word for the direction they want to grow toward (aspirational)
- One word for how they want to feel in their clothes (emotional)

Examples: "minimal / sharp / confident", "comfortable / Parisian / effortless",
"sporty / refined / capable". If the user struggles, offer the archetype menu
in `references/methodologies.md` §"Style archetypes".

#### Group C: Color and palette

- Which colors do you wear most? (cross-check against the inventory's actual
  top 5 colors — if there's a mismatch, surface it)
- Which colors do you avoid?
- Pick 1–3 base neutrals (typical: black, white, navy, grey, beige/camel, brown)
- Pick 2–3 main colors that play nicely with the neutrals
- Pick 1–3 accents

Target distribution: **50–70% neutrals, 20–30% main colors, 10–20% accents.**
If the inventory is already heavily skewed toward one neutral, lean into it
rather than fighting it.

#### Group D: Climate and constraints

- City / climate zone (the user's memory shows Tbilisi-area context, so
  default to a temperate-with-hot-summer profile unless they say otherwise)
- Indoor/outdoor split (HVAC reality affects layering)
- Laundry frequency (default: weekly. If different, capture it.)
- Body shape / fit preferences (only if the user offers — don't push on this)
- Budget / shopping habits (for future "buy to fill gaps" recommendations)

#### Group E: Pain points and aspirations

- "What 5 items do you reach for most often?"
- "What's in your closet that you never wear, and why?"
- "What outfit do you wish you had but don't?"
- "How do you want to feel when getting dressed?"

### Output

Write `preferences.json` per the schema. Then surface a one-page summary:

```
Lifestyle: 50% work-from-home, 25% casual, 15% social, 10% exercise
Style words: minimalist / sharp / confident
Palette: black + grey + white anchors; navy and olive mains; rust accent
Climate: Tbilisi — humid continental, 25–35°C summer, 0–10°C winter
Laundry: weekly
Top pain: "too many shirts I never wear"
```

Confirm this summary with the user before proceeding to Phase 3. Their
reaction ("yes" or "wait, change X") is itself useful signal.

## Phase 3 — Score and Surface Gaps

**Goal:** evaluate every item in the inventory and surface what to keep,
archive, and (eventually) buy.

### Per-item scoring

For each item in `inventory.json`, compute four scores. Specifics in
`references/scoring.md`, summarized here:

1. **Pair count** — how many other items it makes a valid outfit with.
   Validity rules: color/palette compatible, formality within ±1 level,
   layering position complementary. Use the pairing logic in
   `references/scoring.md`.

2. **Formula fit** — does the item slot into ≥1 named outfit formula? The
   formula library is in `references/outfit-formulas.md`. Items that don't
   fit any formula are decoration, not wardrobe.

3. **Lifestyle fit** — does it serve an activity bucket that's >5% of the
   user's pie? A formal dress for a user with 0% formal events is a
   fantasy-self item.

4. **Versatility test (≥3)** — can it be worn in ≥3 distinct outfits with
   the existing inventory? This is Anuschka Rees' personal buy rule, applied
   in reverse to existing items.

Combine into a per-item recommendation:
- **keep — high versatility** (high on all four)
- **keep — workhorse** (lifestyle fit + pair count, even if low on style)
- **keep — statement** (low pair count is OK if formula fit + emotional fit)
- **archive candidate** (low on all four; ask user if they're emotionally
  attached before recommending purge)
- **decluttering candidate** (low on all four AND user said they never wear it)

### Gap analysis

Compare the user's lifestyle pie to their wardrobe distribution:

```
Activity        Life %    Wardrobe %    Gap
Work-from-home  50        20            UNDER (need more comfortable basics)
Casual          25        30            OK
Social          15        15            OK
Formal          0         30            OVER (consider archiving formal pieces)
Exercise        10        5             slight under
```

Also flag specific structural gaps from the universal heuristics:
- Tops-to-bottoms ratio < 1.5:1 → likely under-stocked on tops for laundry math
- No "third piece" in any common formality level → outfits will look
  unstyled; recommend adding a cardigan/blazer/vest in the missing tier
- All shoes are same formality level → outfit ceiling is capped
- No layering pieces for current season → weekly capsule will fail on cool/wet days

### Output

Write `scoring.json` per the schema. Then surface a structured report
to the user:

1. Top 10 most versatile items (your wardrobe MVPs)
2. Bottom 10 versatility (decluttering / archive candidates, with reasoning)
3. Gap analysis table
4. 2–4 specific buy recommendations to fill the highest-impact gaps

Don't push the user to declutter or buy aggressively. Present the analysis;
let them choose what to act on.

## Phase 4 — Weekly Capsule

**Goal:** generate a 7-day mix-and-match outfit pool for the upcoming week.

### Inputs

- `inventory.json` (only items with `recommendation: keep-*`)
- `preferences.json`
- A 7-day weather forecast for the user's city
- The user's calendar / activity plan for the week, OR the lifestyle pie
  if no specific calendar is given

### Sport / activewear inclusion (per-user)

Whether `category: sport` items belong in the weekly capsule pool depends on
`preferences.json → include_sport_in_capsule` (boolean):

- **`true`** (e.g. Mariana): include sport items as a separate `pool.sport`
  bucket. She wears them for daily activities (gym, walks, school runs), so
  they belong in the rotation.
- **`false`** (e.g. Ruslan): exclude sport items entirely from the capsule.
  Sport is a separate context, not part of his everyday outfit pool.

If the field is missing, default to `false` and ask the user once before
generating. Honor `excluded_from_capsule: true` on individual items
regardless of the per-user default.

### Step-by-step

1. **Get the weather.** Always use the `mcp__open-meteo__get_weather` MCP tool —
   pass the user's city (read from `preferences.json → city` field, or ask if not
   set). Never hardcode weather data or ask the user to provide forecasts manually.
   The tool returns current conditions + 7-day forecast as
   `YYYY-MM-DD  low_c°–high_c°C  condition  precip_mm` rows.

   **Two-temperature read for the morning/afternoon split.** The MCP returns
   only daily lows and highs (no hourly), so map them directly:
   - **`low_c` → morning** (≈ pre-sunrise to ~9 am, what the user feels
     leaving the house)
   - **`high_c` → afternoon** (≈ 13:00–16:00 daily peak)

   For each day extract: `low_c`, `high_c`, `delta = high_c − low_c`,
   `condition`, `precip_mm`. Record `delta` per day:
   - **`delta ≥ 6°C`** → meaningfully different morning vs afternoon; the two
     outfit variants should differ on a real temperature slot (layer on/off,
     shorts ↔ trousers, tee ↔ long-sleeve).
   - **`delta < 3°C`** → temperature is stable; morning and afternoon variants
     can be identical (the renderer collapses them to one line).
   - **`3°C ≤ delta < 6°C`** → optional second variant: small swap if it
     adds value, otherwise keep them identical.

   Note the temperature range and `delta` pattern across the week — this drives
   the layering plan AND signals which days need two distinct variants.

2. **Check the previous week's capsule for variety.** Before picking items,
   read `data/capsule/<user>/<previous-week>.json` (e.g. for W21 → load W20).
   Extract the set of `item_id`s used in `pool.tops`, `pool.bottoms`,
   `pool.layers`, `pool.outerwear`, and across all `daily_anchors[].items`
   (both `morning` and `afternoon` variants).

   **Variety rule:** for the new week's pool, aim for **≤40% overlap** with
   the previous week's pool. In practice that means:
   - Drop at least half of the previous week's tops, bottoms, and layers
     (unless the inventory is genuinely small — see "When inventory is too
     small" below).
   - Promote previously-unused / under-rotated items from inventory.
   - Reuse a workhorse piece across weeks only when weather / activity
     genuinely demands it (e.g. the only rain jacket during a wet week,
     or the only warm coat in winter).
   - **New items from recent inventory additions are highest priority** —
     feature them prominently in daily anchors, not just the pool.

   If you reuse an item from last week, vary how it's styled: pair it with a
   different top/bottom, swap the layering piece, or move it to a different
   day-of-week slot. Marianna and other users notice "this looks like last
   week" — surface variety even when reusing pieces.

3. **Get the activity plan.** Either pull from a stated calendar
   ("Monday client meeting, Tuesday WFH, Wednesday gym then dinner...") or
   distribute the lifestyle pie across 7 days. Tag each day with a primary
   activity bucket.

4. **Pick outfit formulas per day — two variants (morning / afternoon).**
   Use the per-day `delta` from step 1 to decide whether the day needs two
   distinct variants or a single shared one. When two are warranted, choose
   **two** formulas from `references/outfit-formulas.md`:
   - **Cool variant** for the morning (sized for `low_c`)
   - **Warm variant** for the afternoon (sized for `high_c`)

   Both variants match the same activity bucket and precipitation conditions —
   only temperature differs. Keep the two variants as overlapping as possible:
   ideally share the top OR the bottom, and swap only the temperature-sensitive
   piece (e.g. same tee, but shorts ↔ trousers; or same jeans, but tee ↔
   long-sleeve + light layer). The goal is one coherent daily outfit that the
   user adjusts as the day warms up, not two unrelated outfits.

   This also gives resilience if the weekly forecast shifts: either variant
   alone is wearable, and the user can pick based on actual conditions that
   morning.

5. **Fill the formula slots from inventory.** For each formula slot
   (top, bottom, third piece, shoes, outer layer), pick from items that:
   - Are not already "in laundry" (see step 5)
   - Match the day's color story (one base neutral + 0–2 accents)
   - Pass the formality consistency check (all slots within ±1 level)

6. **Track wear cycles.** Use the wear-cycle defaults in
   `references/wear-cycles.md`. After an item is worn, it's "in laundry" for
   `wear_cycle` days. Don't reuse items inside their cycle. If laundry day
   is mid-week (e.g., Saturday), reset cycles after that.

7. **Surface the pool, not a strict assignment.** The user asked for a
   "pool with mix-and-match" — so present it as:
   - **Pool**: ~10–15 items the week will rotate through
   - **Daily anchor outfits**: one suggested combination per day, based on
     weather + activity, that the user can swap pieces in/out of
   - **Mix-and-match map**: which items pair with which (so user can
     freelance their own combinations)

8. **Forecast laundry.** Tell the user which day they'll need to wash what
   based on wear-cycle math. Example: "Wash whites Friday; jeans can stretch
   to next Tuesday."

### Capsule output format

```markdown
# Week of [DATE]

## Weather summary
Mon-Tue cool & rainy (12–18°C), Wed-Thu warm (22–28°C), Fri-Sun mild & dry (16–24°C)

## Activity summary
Mon-Wed WFH, Thu in-office + dinner, Fri casual day, Sat-Sun social

## Capsule pool (12 items)
**Tops**: top-003 (white tee), top-007 (grey henley), top-012 (navy button-down)
**Bottoms**: btm-001 (dark jeans), btm-004 (olive chinos)
**Third pieces**: lay-002 (grey cardigan), lay-005 (navy blazer)
**Outerwear**: out-001 (rain jacket), out-003 (denim jacket)
**Shoes**: shoe-002 (white sneakers), shoe-004 (brown loafers), shoe-001 (chelsea boots)

## Daily anchor outfits (morning / afternoon)
**Mon (cool→cool, rainy, WFH)**
- 🌅 morning: top-007 + btm-001 + lay-002 + shoe-001 + out-001
- ☀️ afternoon: top-007 + btm-001 + shoe-001 + out-001  *(drop the cardigan)*

**Wed (cool→warm, WFH)**
- 🌅 morning: top-003 + btm-004 + lay-002 + shoe-002
- ☀️ afternoon: top-003 + btm-004 + shoe-002  *(same base, layer off)*

**Thu (warm→hot, in-office + dinner)**
- 🌅 morning: top-012 + btm-001 + lay-005 + shoe-004
- ☀️ afternoon: top-012 + btm-002 + shoe-004  *(jeans → shorts, same shirt)*

## Laundry forecast
- Wash tops Wed evening (3 worn next-to-skin)
- Jeans (btm-001) worn 4× — can stretch to next Mon, then wash
- Blazer/cardigan: no wash needed this week
```

### Daily anchor JSON fields

Each entry in `daily_anchors` must have **two variants** — `morning` (cool)
and `afternoon` (warm) — that share as many items as possible:

```json
{
  "day": "Mon",
  "date": "11 мая",
  "weather": "🌦 14–22°C, утром прохладно, днём теплеет",
  "color_story": "голубой + светлый деним + кремовый жилет",
  "caption": "Ажур + полоска = интересный контраст. Деним даёт непринуждённость.",
  "morning": {
    "temp_label": "🌅 утро 14°C",
    "formula": "crochet top + jeans + cardigan + sneakers",
    "items": ["top-007", "btm-001", "lay-006", "shoe-001"]
  },
  "afternoon": {
    "temp_label": "☀️ день 22°C",
    "formula": "crochet top + jeans + sneakers",
    "items": ["top-007", "btm-001", "shoe-001"]
  },
  "photo_urls": {
    "top-007": "https://...",
    "btm-001": "https://...",
    "lay-006": "https://...",
    "shoe-001": "https://..."
  }
}
```

**Rules for the two variants:**
- Share at least one anchor piece (top or bottom) — usually both.
- Differ on the temperature-driven slot: add/remove a layer, swap shorts ↔
  trousers, swap tee ↔ long-sleeve, etc.
- `photo_urls` is one combined map covering every item used in either variant
  (no duplication needed per-variant).
- `color_story` and `caption` describe the day as a whole, not each variant.

**`caption`** — одна короткая фраза (1–2 предложения) о настроении/логике образа.
НЕ перечислять одежду — она уже показана ссылками выше. Писать только то, что
добавляет смысл: погодный контекст, стилевой приём, совет по носке.

Хорошо: `"Гроза — день дома. Яркий образ для комфортного дня + выход в школу."`
Плохо: `"Малиновая рубашка + серая юбка + жилет = яркий образ."` ← дублирует список вещей.

**Telegram-рендер одного дня** показывает оба варианта:
```
Пятница, 15 мая — ⛈ 14–22°C
🌅 утро: Малиновая рубашка · Джинсы · Бохо-жилет · Белые кеды
☀️ день: Малиновая рубашка · Шорты · Белые кеды
Гроза — день дома. Яркий образ для комфортного дня + выход в школу.
```

Если разница между утром и днём <3°C — можно показать один общий вариант
(оба объекта в JSON идентичны), и рендер сворачивается в одну строку.

### Acceptance criteria для weekly overview (обязательно проверить!)

После генерации капсулы и перед тем как сказать "готово", всегда прогнать
`format_weekly_overview(capsule, inventory)` локально и проверить, что
сообщение для каждого дня содержит:

1. **Заголовок дня** — `<b>День, дата</b> — погода с эмодзи и диапазоном температур`
2. **Строка(и) образа** — минимум одна строка с кликабельными ссылками на
   фото вещей. Если есть `morning`/`afternoon` — две строки с префиксами
   `🌅 утро NN°C:` и `☀️ день NN°C:`. Если варианты идентичны — одна строка
   без префикса.
3. **Caption** — курсивная подпись с настроением/логикой образа.

**Если в выводе видны только заголовок и caption без ссылок — это баг.**
Значит либо: (a) `daily_anchors[].items` пустой / отсутствует,
(b) `morning.items` и `afternoon.items` не заполнены,
(c) на проде запущен старый код, который не знает про morning/afternoon —
проверь `git log` на дроплете и пересобери контейнер.

Минимальная проверка перед сдачей работы:
```python
from bot.commands.capsule import format_weekly_overview
import json
cap = json.load(open(f'data/capsule/{user}/{week}.json'))
inv = {it['id']: it for it in json.load(open(f'wardrobe/{user}/inventory.json'))['items']}
out = format_weekly_overview(cap, inv)
assert '<a href=' in out, "Render is missing photo links!"
assert out.count('<a href=') >= 14, f"Too few links: {out.count('<a href=')}"

# Pool ↔ daily_anchors consistency check
pool_ids = {it['id'] for cat in cap['pool'].values() for it in cat}
used_ids = set()
for d in cap['daily_anchors']:
    for v in ('morning', 'afternoon'):
        used_ids.update(d.get(v, {}).get('items', []))
    used_ids.update(d.get('items', []))  # legacy flat anchors

unused = pool_ids - used_ids
orphan = used_ids - pool_ids
assert not orphan, f"Anchors reference items not in pool: {orphan}"
assert not unused, (
    f"Pool has items not used in any daily anchor: {unused}. "
    "Either assign them to a day's morning/afternoon, or remove them from the pool. "
    "The checklist is built from the pool — unused items show up as 'extra' tickbox rows."
)
```

Save the plan to `data/capsule/{ISO-week}.json`.

9. **Deploy to droplet.** After saving the JSON locally, copy it to the
   production server so the Telegram bot can serve it immediately.
   The capsule file must go into the per-user subdirectory on the droplet:

   ```bash
   scp -i ~/.ssh/kartuli_bot_deploy \
     data/capsule/<user>/{ISO-week}.json \
     root@165.232.116.241:~/assistant/data/capsule/<user>/
   ```

   Example for Mariana week 20:
   ```bash
   scp -i ~/.ssh/kartuli_bot_deploy \
     data/capsule/Mariana/2026-W20.json \
     root@165.232.116.241:~/assistant/data/capsule/Mariana/
   ```

   Confirm success (`scp` exits 0) and tell the user the capsule is live.
   If `scp` fails (no network, key missing), tell the user and show the
   manual command they can run themselves.

### When inventory is too small

If the inventory has <14 visually-distinct outfits available (rough heuristic:
fewer than 5 tops + 3 bottoms + 1 layer of usable items in the right season),
say so directly. Don't generate a 7-day plan that forces re-wearing items
inside their wear-cycle. Instead, return the smaller "best 4–5 outfits we can
make" and surface this as a Phase 3 gap.

## Communication style

- **Russian/English bilingual:** the user (per their context) writes
  reflective Russian-language posts and works in mixed Russian/English. Mirror
  their language. Default to Russian if they open in Russian.
- **Architecture-first, not implementation-first:** the user prefers
  discussing structure before details. In Phase 1, surface the inventory
  structure before drowning them in 50 individual item entries. In Phase 4,
  surface the weekly logic before the day-by-day picks.
- **Direct and minimal-intervention:** when reviewing or correcting their
  preferences, ask the question; don't over-explain.
- **Don't moralize about clothing choices.** No "you should buy less"
  lectures. The user is a competent adult; surface analysis, not opinions.

## Reference files

Consult these when needed — don't try to keep them all in head simultaneously.

- `references/taxonomy.md` — full inventory categories, subcategories, and
  per-item attributes with controlled vocabulary
- `references/schemas.md` — JSON schemas for inventory.json,
  preferences.json, scoring.json, and weekly capsule files
- `references/methodologies.md` — when to recommend Project 333 vs.
  5-Piece French vs. 10×10 vs. Curated Closet, plus the style-archetype menu
- `references/outfit-formulas.md` — the formula library: top + bottom +
  third piece + shoe templates by formality and weather
- `references/wear-cycles.md` — how many wears between washes for each
  category, and how to do laundry math
- `references/scoring.md` — scoring rules: pair-count algorithm, formula-fit
  test, lifestyle-fit test, versatility threshold

## Common failure modes (avoid these)

1. **Fantasy-self wardrobing** — recommending the user keep / buy formal
   pieces when their pie chart says 0% formal events. Always check life
   ratios first.
2. **Ignoring laundry math** — generating a week that re-uses an item every
   2 days when its wear-cycle is 4. Always validate against `wear-cycles.md`.
3. **Pure combinatorics** — claiming "286 outfits from 21 items" using raw
   T × B × S × L. Real wearable count is ~15–20% of that. Use formula-fit
   to filter, not raw multiplication.
4. **Copying a generic capsule list** — the user's actual closet, climate,
   and lifestyle drive the answer. Templates in `methodologies.md` are
   inspiration only.
5. **Methodology evangelism** — don't push Project 333 just because it has
   the cleanest constraint. Match methodology to user type per
   `methodologies.md`.
6. **Burying the user in data** — dump all 60 inventory items in a wall of
   text instead of summarizing first. Always lead with a structural summary.
