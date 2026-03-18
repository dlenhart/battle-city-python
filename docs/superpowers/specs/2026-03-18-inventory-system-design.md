# Inventory System Design
**Date:** 2026-03-18
**Project:** Battle City Python
**Status:** Approved

---

## Overview

Add a complete item inventory system to the Python port, matching the original C++ Battle City gameplay:

1. Factories produce world items on a timer
2. Player picks up items with `U`, drops with `D`
3. Inventory panel (3×4 grid) displays held items with counts and selection highlight
4. Item effects for solo-playable items (MedKit, Cloak, Rocket)
5. Enemy-targeting items (Turret, Sleeper, Plasma, Mine, DFG, Wall, Bomb, Orb, Flare) are fully pickup/drop/renderable but inert (no combat AI — enemies not yet implemented)

**Reference:** `client/CItem.cpp`, `client/CDrawing.cpp`, `server/CBuilding.cpp`, `server/CConstants.h`

---

## Item Types

12 item types, matching C++ `ITEM_TYPE_*` constants:

| ID | Name         | Max World Count |
|----|--------------|-----------------|
| 0  | Cloak        | 4               |
| 1  | Rocket       | 4               |
| 2  | MedKit       | 5               |
| 3  | Bomb         | 20              |
| 4  | Mine         | 10              |
| 5  | Orb          | 1               |
| 6  | Flare        | 4               |
| 7  | DFG          | 5               |
| 8  | Wall         | 20              |
| 9  | Turret       | 10              |
| 10 | Sleeper      | 5               |
| 11 | Plasma       | 5               |

`ITEM_MAX_COUNTS` mirrors the C++ server `maxItems[]` array and caps how many of each type a factory can have in the world simultaneously. The player may hold up to that many in inventory.

---

## Architecture

### New file: `src/inventory.py`

Contains three classes:

**`WorldItem`** — an item on the ground:
```
tile_x: int
tile_y: int
item_type: int          # 0–11
animation: int          # Orb cycles 0–2; others unused
_anim_timer: float
factory_ref: PlacedBuilding | None   # back-reference to decrement factory count on pickup
```

**`Inventory`** — the player's held items:
```
counts: list[int]       # 12 slots, count per type
selected_type: int      # currently highlighted slot for drop/use
```
Methods: `pickup(item_type)`, `drop(item_type)`, `select_next()`, `select_prev()`, `count_total()`

**`ItemEffects`** — stateless functions triggered on use:
- `use_medkit(player)` → restore HP to MAX_HEALTH
- `use_cloak(player)` → set `player.is_cloaked = True`, start 5s timer
- `use_rocket(player)` → set `player.bullet_type = 1`

### Changes to `src/building.py`

Add to `PlacedBuilding`:
```
_produce_timer: float   # countdown; 0.0 = not yet started
world_item_count: int   # items currently on the ground from this factory
item_type: int          # computed from BUILDING_TYPES[menu_index] % 100
```

`PlacedBuilding.update()` returns a `WorldItem | None` each frame — caller (`BuildingManager`) collects them. `BuildingManager.update()` returns `list[WorldItem]` of newly spawned items so `game.py` can add them to the world list.

Item spawn position: `tile_x + 1, tile_y + 1` (center of the 3×3 footprint, adapted from C++ `bld->x-1, bld->y-2`).

### Changes to `settings.py`

```python
# Item system
ITEM_MAX_COUNTS          = [4, 4, 5, 20, 10, 1, 4, 5, 20, 10, 5, 5]
ITEM_NAMES               = ["Cloak","Rocket","MedKit","Bomb","Mine","Orb",
                             "Flare","DFG","Wall","Turret","Sleeper","Plasma"]
FACTORY_PRODUCE_INTERVAL = 7.0       # seconds (C++ ProduceTick + 7000 ms)
ITEM_PICKUP_RANGE        = 1.5       # tiles — max distance to pick up

# Inventory panel grid (relative to PANEL_X, PANEL_Y)
INV_COL_OFFSETS = [7, 42, 77]        # x offsets for cols 0–2
INV_ROW_OFFSETS = [267, 302, 337, 372]   # y offsets for rows 0–3
INV_ICON_SIZE   = 32                 # icon draw size in panel (px)

# World item sprite source in imgItems.bmp
ITEM_WORLD_SRC_Y = 42                # row offset for world-size icons
ITEM_WORLD_SIZE  = 48                # world item draw size (px)
```

### Changes to `src/game.py`

- Load `imgInventorySelection.bmp` (colorkeyed, magenta)
- Create `Inventory` instance
- Maintain `world_items: list[WorldItem]`
- Each frame: collect new items from `BuildingManager.update()`, tick Orb animation
- Key handlers:
  - `U` → attempt pickup of nearest world item within `ITEM_PICKUP_RANGE`
  - `D` → drop selected item at player tile
  - `[` / `]` → cycle `inventory.selected_type`
  - `H` → use MedKit (if held)
  - `C` → use Cloak (if held)
- Draw world items after buildings, before player
- Call `draw_inventory()` after panel background draw

### Changes to `src/player.py`

Add state:
```
is_cloaked: bool = False
_cloak_timer: float = 0.0
bullet_type: int = 0          # 0=laser default, 1=rocket when rocket held
```
`update()` ticks `_cloak_timer`; sets `is_cloaked = False` when expired.

### Changes to `src/hud.py`

Add `draw_inventory(screen, inventory, items_sheet, selection_sheet, font)`:
- Iterates 12 slots using `INV_COL_OFFSETS` × `INV_ROW_OFFSETS`
- Draws selection highlight, icon, count number

---

## Asset Requirements

| File | Source | Status |
|------|--------|--------|
| `assets/images/imgItems.bmp` | C++ `data/imgItems.bmp` | Already present |
| `assets/images/imgInventorySelection.bmp` | C++ `data/imgInventorySelection.bmp` | **Needs copy** |

`imgInventorySelection.bmp` colorkey: magenta (255, 0, 255).

---

## World Item Rendering

Drawn in `game.py` draw loop (after buildings, before player), clipped to `field_rect`:

```python
src_x = item.item_type * ITEM_WORLD_SIZE
src_y = ITEM_WORLD_SRC_Y
if item.item_type == 5:   # Orb
    src_y += item.animation * ITEM_WORLD_SIZE
screen.blit(items_sheet, (screen_x, screen_y), pygame.Rect(src_x, src_y, 48, 48))
```

---

## Inventory Panel Rendering

The 3×4 grid occupies rows Y=267–404 of the panel. Each of the 12 slots:

1. If `counts[type] > 0` and `type == selected_type`: blit selection highlight (32×32)
2. If `counts[type] > 0`: blit icon from `imgItems.bmp` at `src=(type*32, 0)`, size 32×32
3. If `counts[type] > 1`: render yellow count string at `(slot_x+22, slot_y+12)`

---

## Item Effects (solo-playable)

| Key | Item     | Effect |
|-----|----------|--------|
| `H` | MedKit   | `player.hp = MAX_HEALTH`, consume 1 |
| `C` | Cloak    | `player.is_cloaked = True` for 5s, consume 1 |
| Passive | Rocket | `player.bullet_type = 1` while held; reverts to 0 when count hits 0 |

All other items: pickup/drop renders correctly; no active effect until enemies are implemented.

---

## Key Controls Summary

| Key | Action |
|-----|--------|
| `U` | Pick up nearest world item |
| `D` | Drop selected inventory item at player position |
| `[` | Cycle selected item left |
| `]` | Cycle selected item right |
| `H` | Use MedKit |
| `C` | Use Cloak |

---

## Item Count Limits

- **World cap:** `ITEM_MAX_COUNTS[type]` — factory stops producing when this many items of that type exist on the ground
- **Inventory cap:** Same value — player cannot pick up more than `ITEM_MAX_COUNTS[type]` of any single item type
- Factory `world_item_count` tracks how many it has spawned that haven't been picked up; decrements on player pickup

---

## Testing

New tests in `src/tests/test_inventory.py`:
- Factory produces item after 7s at full pop
- Factory respects `ITEM_MAX_COUNTS` cap
- Pickup increments inventory count
- Pickup fails when inventory at cap
- Drop decrements count and creates WorldItem
- `select_next()` skips empty slots
- MedKit use restores HP
- Cloak use sets `is_cloaked` and timer

---

## Import Dependency Order (no circular imports)

```
settings ← inventory ← building, player, hud ← game ← battle_city.py
```

`inventory.py` imports only `settings` and `pygame` — no imports from other `src/` modules. `PlacedBuilding` in `building.py` returns `WorldItem` objects (defined in `inventory.py`), so `building.py` imports from `inventory.py`.
