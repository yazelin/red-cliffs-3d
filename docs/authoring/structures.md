# Authoring `data/structures.json`

This guide explains how to add and edit the map structures — cities, camps, passes, and
text-only markers — that the scene builds from `data/structures.json`. It is the single
source of truth for every walled city, tent camp, pass, and place label on the battlefield.

No rebuild step is needed: `index.html` fetches `data/structures.json` at load and builds
each structure from its `type`. Edit the JSON, reload the page.

---

## File shape

```json
{
  "structures": [
    { "id": "...", "type": "city", "x": 0, "z": 0, "label": "...", "labelPos": [0, 0], "labelClass": "big" }
  ]
}
```

The file is one object with a single required key, `structures`, whose value is an array of
structure entries. Order does not matter for rendering.

---

## Fields

Every field below is defined in `schema/structures.schema.json`. **Do not invent fields** —
anything not listed here is not read by the renderer and will not validate.

| Field        | Type            | Required            | Meaning |
|--------------|-----------------|---------------------|---------|
| `type`       | string enum     | **always**          | One of `city`, `camp`, `pass`, `marker`. Selects what gets built. |
| `x`          | number          | **always**          | World X position (east–west). |
| `z`          | number          | **always**          | World Z position (north–south). |
| `id`         | string          | optional            | Stable handle. Must be unique across the array. Required if other code references the structure by name (e.g. `campWulin`, `campChibi`). Markers usually omit it. |
| `faction`    | string enum     | **camps only**      | One of `cao`, `sun`, `liu`. Sets the banner colour on a camp. Validation **fails** if a `camp` has no faction. |
| `label`      | string          | optional            | Text drawn next to the structure. For `marker` this is the whole point of the entry. |
| `labelPos`   | `[number, number]` | optional         | Explicit `[x, z]` for the floating label. If omitted, the label sits at the structure's own `x, z`. Exactly two numbers. |
| `labelClass` | string          | optional            | CSS class for the label. Known values in use: `big` (large city/place names) and `water` (river/water labels, sits lower). Empty/omitted = default styling. |

### Notes per type

- **`city`** — builds a walled city (`makeCity`). Typically has `id`, `label`, `labelPos`,
  and `labelClass: "big"`. Has a real 3D footprint (~radius 13).
- **`camp`** — builds a tent camp with a faction banner (`makeCamp`). **Must** have
  `faction`. Camps are placed but start hidden; downstream code toggles visibility by `id`.
  Has a real 3D footprint (~radius 11).
- **`pass`** — builds a gate/pass tower pair (`makePass`). Has `id`, `label`, `x`, `z`.
- **`marker`** — **label only.** No geometry is built; only the text in `label` is drawn at
  `x, z` (or `labelPos`). Use for terrain place-names like 長坂坡, 烏林, 赤壁, 漢水. `faction`
  and `id` are not needed.

`faction` is limited to **`cao` / `sun` / `liu`** everywhere it appears.

---

## The river gotcha (read this before placing anything)

A structure's **footprint must sit clear of the river channel.** Cities and camps are solid
3D meshes anchored to the terrain height at their `x, z`. The two rivers in
`data/terrain.json` (長江 `changjiang`, halfWidth 34; 漢水 `hanshui`, halfWidth 13) carve the
ground **below sea level** inside their channel. If any part of a structure's footprint
overlaps that channel, the walls/tents render half-submerged — the city looks like it is
sinking into the water.

Keep solid structures on **dry land**, away from the river centerlines:

- **Cities** occupy roughly radius **13** around their `x, z`.
- **Camps** occupy roughly radius **11** around their `x, z`.

So a city must be far enough from a river that even its outer wall (≈13 units out) is still
on ground above the waterline. Markers are label-only and have no footprint, so they may be
placed over water freely (that is how 漢水 / 長江 water labels work — they use
`labelClass: "water"`).

Verify dry land before you commit (command below).

---

## Recipes

### Add a city

Pick a dry spot, give it a unique `id`, a `label`, and usually a `big` label class. Offset
`labelPos` slightly from `x, z` so the text clears the walls.

```json
{ "id": "wuchang", "type": "city", "x": 220, "z": -90, "label": "武昌", "labelPos": [220, -78], "labelClass": "big" }
```

### Add a camp

Camps **require** a `faction`. They are positioned here but shown/hidden by other code, so
give them an `id` if anything needs to toggle them.

```json
{ "id": "campLuxu", "type": "camp", "faction": "sun", "x": 100, "z": 60 }
```

### Add a pass

```json
{ "id": "yiling", "type": "pass", "x": -300, "z": -10, "label": "夷陵關" }
```

### Place a marker (label only)

No `id`, no `faction`, no geometry — just text at a point. Add `labelClass` only if you want
`big` or `water` styling.

```json
{ "type": "marker", "label": "巴丘", "x": 280, "z": 70 }
```

### Set / change a faction

`faction` applies to **camps only** and must be one of `cao`, `sun`, `liu`. To change a
camp's allegiance, edit its `faction` value:

```json
{ "id": "campWulin", "type": "camp", "faction": "liu", "x": -45, "z": -52 }
```

Removing `faction` from a camp will fail validation.

---

## Copy-paste entry example

A complete, schema-valid city entry on dry land:

```json
{ "id": "wuchang", "type": "city", "x": 220, "z": -90, "label": "武昌", "labelPos": [220, -78], "labelClass": "big" }
```

Add it as a new element of the `structures` array.

---

## Verification

After editing, run the data validator from the repo root:

```bash
node tools/validate-data.mjs
```

It checks: every `type` is legal, `x`/`z` are numbers, every `camp` has a faction in
`cao/sun/liu`, and `id`s are unique. A green run prints `PASS — ...`.

**Also confirm the structure is not in water.** The validator does not know about footprints,
so check that the terrain height stays above 0 (above the waterline) across the structure's
footprint — sample the center and a ring at the footprint radius (≈13 for a city, ≈11 for a
camp). Visually: reload `index.html` and confirm the new structure sits on land, with no
walls or tents poking up out of the river.

A quick numeric check is to confirm every existing solid structure already reports a positive
minimum footprint height while a point inside a river channel reports a negative one — your
new structure should look like the former, not the latter.
