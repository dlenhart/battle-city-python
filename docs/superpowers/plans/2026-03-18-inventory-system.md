# Inventory System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a complete item inventory system — factories produce world items, player picks up with `U` and drops with `D`, inventory panel shows a 3×4 grid with counts, and solo-playable items (MedKit, Cloak, Rocket) have real effects.

**Architecture:** Single new module `src/inventory.py` owns `WorldItem` (on-map item) and `Inventory` (held items). Factory production timer is added to `PlacedBuilding` in `building.py`, which returns newly spawned `WorldItem`s each frame. `game.py` orchestrates pickup/drop input and delegates rendering to `hud.py`.

**Tech Stack:** Python 3.11+, pygame 2.x

---

## File Map

| Action | File | What changes |
|--------|------|--------------|
| Copy asset | `assets/images/imgInventorySelection.bmp` | Copy from C++ data/ |
| Modify | `settings.py` | Add item constants, inventory panel layout constants |
| **Create** | `src/inventory.py` | `WorldItem`, `Inventory`, `ItemEffects` |
| Modify | `src/building.py` | `PlacedBuilding`: add `item_type`, `_produce_timer`, `world_item_count`; `BuildingManager.update()` returns `list[WorldItem]` |
| Modify | `src/player.py` | Add `is_cloaked`, `_cloak_timer`, `bullet_type` |
| Modify | `src/hud.py` | Add `draw_inventory()` function |
| Modify | `src/game.py` | Load selection sheet, create `Inventory`, handle U/D/[/]/H/C keys, draw world items, call `draw_inventory()` |
| **Create** | `src/tests/test_inventory.py` | Unit tests for all inventory logic |

---

## Task 1: Copy asset and add settings constants

**Files:**
- Copy: `assets/images/imgInventorySelection.bmp`
- Modify: `settings.py` (append after line 216)

- [ ] **Step 1: Copy the inventory selection asset**

```bash
cp "/Users/drewlenhart/Desktop/current_programs/Battle-City/data/imgInventorySelection.bmp" \
   "/Users/drewlenhart/Desktop/current_programs/battle-city-python/assets/images/imgInventorySelection.bmp"
```

Verify it exists:
```bash
ls assets/images/imgInventorySelection.bmp
```

- [ ] **Step 2: Append item system constants to `settings.py`**

Add at the end of `settings.py`:

```python
# ---------------------------------------------------------------------------
# Item system — mirrors server/CConstants.h maxItems[] and itemTypes[]
# ---------------------------------------------------------------------------

# Item type IDs (matching C++ ITEM_TYPE_* constants)
ITEM_TYPE_CLOAK   = 0
ITEM_TYPE_ROCKET  = 1
ITEM_TYPE_MEDKIT  = 2
ITEM_TYPE_BOMB    = 3
ITEM_TYPE_MINE    = 4
ITEM_TYPE_ORB     = 5
ITEM_TYPE_FLARE   = 6
ITEM_TYPE_DFG     = 7
ITEM_TYPE_WALL    = 8
ITEM_TYPE_TURRET  = 9
ITEM_TYPE_SLEEPER = 10
ITEM_TYPE_PLASMA  = 11
NUM_ITEM_TYPES    = 12

# Human-readable names (index = item type)
ITEM_NAMES: list[str] = [
    "Cloak", "Rocket", "MedKit", "Bomb", "Mine", "Orb",
    "Flare", "DFG", "Wall", "Turret", "Sleeper", "Plasma",
]

# World cap per item type — factory stops producing when this many exist on ground
# Mirrors C++ server maxItems[] = {4,4,5,20,10,1,4,5,20,10,5,5}
ITEM_MAX_COUNTS: list[int] = [4, 4, 5, 20, 10, 1, 4, 5, 20, 10, 5, 5]

# Factory production interval in seconds (C++ ProduceTick + 7000 ms)
FACTORY_PRODUCE_INTERVAL: float = 7.0

# Pickup range in tiles (player must be within this distance of the item)
ITEM_PICKUP_RANGE: float = 1.5

# Cloak duration in seconds (C++ TIMER_CLOAK = 5000 ms)
TIMER_CLOAK: float = 5.0

# ---------------------------------------------------------------------------
# Inventory panel grid — relative to PANEL_X, PANEL_Y
# (mirrors C++ CDrawing::DrawInventory absolute positions minus MaxMapX=600)
# ---------------------------------------------------------------------------
INV_COL_OFFSETS: list[int] = [7, 42, 77]        # x offsets for cols 0–2
INV_ROW_OFFSETS: list[int] = [267, 302, 337, 372]  # y offsets for rows 0–3
INV_ICON_SIZE: int = 32                          # each slot icon is 32×32 px

# World item sprite layout in imgItems.bmp
# Small icons (used in inventory panel): src_y=0, src_x=type*32, size=32×32
# Large icons (used in world): src_y=42, src_x=type*48, size=48×48
ITEM_WORLD_SRC_Y: int = 42
ITEM_WORLD_SIZE:  int = 48
```

- [ ] **Step 3: Verify settings loads cleanly**

```bash
python3 -c "import settings; print(settings.ITEM_MAX_COUNTS)"
```

Expected: `[4, 4, 5, 20, 10, 1, 4, 5, 20, 10, 5, 5]`

- [ ] **Step 4: Commit**

```bash
git add assets/images/imgInventorySelection.bmp settings.py
git commit -m "feat: add inventory asset and settings constants"
```

---

## Task 2: Create `src/inventory.py`

**Files:**
- Create: `src/inventory.py`
- Create: `src/tests/test_inventory.py` (written in this task for `WorldItem` and `Inventory`)

- [ ] **Step 1: Write failing tests for `WorldItem`**

Create `src/tests/test_inventory.py`:

```python
"""Tests for WorldItem and Inventory in src/inventory.py."""
import pytest
import settings
from src.inventory import WorldItem, Inventory, ItemEffects


# ---------------------------------------------------------------------------
# WorldItem
# ---------------------------------------------------------------------------

class TestWorldItem:
    def test_init_sets_fields(self):
        item = WorldItem(tile_x=10, tile_y=20, item_type=2)
        assert item.tile_x == 10
        assert item.tile_y == 20
        assert item.item_type == 2
        assert item.animation == 0
        assert item.factory_ref is None

    def test_orb_animation_cycles_on_update(self):
        item = WorldItem(tile_x=0, tile_y=0, item_type=settings.ITEM_TYPE_ORB)
        # Default anim_interval is 1.0s; advance past it
        item.update(1.1)
        assert item.animation == 1

    def test_orb_animation_wraps_at_3(self):
        item = WorldItem(tile_x=0, tile_y=0, item_type=settings.ITEM_TYPE_ORB)
        item.update(3.1)
        assert item.animation == 0  # wraps: 3 % 3 == 0

    def test_non_orb_animation_does_not_advance(self):
        item = WorldItem(tile_x=0, tile_y=0, item_type=settings.ITEM_TYPE_MEDKIT)
        item.update(5.0)
        assert item.animation == 0

    def test_world_pixel_center(self):
        item = WorldItem(tile_x=3, tile_y=5, item_type=0)
        cx, cy = item.world_center
        assert cx == 3 * settings.TILE_SIZE + settings.TILE_SIZE // 2
        assert cy == 5 * settings.TILE_SIZE + settings.TILE_SIZE // 2


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

class TestInventory:
    def test_starts_empty(self):
        inv = Inventory()
        assert all(c == 0 for c in inv.counts)
        assert inv.count_total() == 0

    def test_pickup_increments_count(self):
        inv = Inventory()
        result = inv.pickup(settings.ITEM_TYPE_MEDKIT)
        assert result is True
        assert inv.counts[settings.ITEM_TYPE_MEDKIT] == 1

    def test_pickup_fails_at_cap(self):
        inv = Inventory()
        cap = settings.ITEM_MAX_COUNTS[settings.ITEM_TYPE_CLOAK]  # 4
        for _ in range(cap):
            inv.pickup(settings.ITEM_TYPE_CLOAK)
        result = inv.pickup(settings.ITEM_TYPE_CLOAK)
        assert result is False
        assert inv.counts[settings.ITEM_TYPE_CLOAK] == cap

    def test_drop_decrements_count(self):
        inv = Inventory()
        inv.pickup(settings.ITEM_TYPE_ROCKET)
        result = inv.drop(settings.ITEM_TYPE_ROCKET)
        assert result is True
        assert inv.counts[settings.ITEM_TYPE_ROCKET] == 0

    def test_drop_fails_when_empty(self):
        inv = Inventory()
        result = inv.drop(settings.ITEM_TYPE_ROCKET)
        assert result is False

    def test_select_next_skips_empty_slots(self):
        inv = Inventory()
        inv.pickup(settings.ITEM_TYPE_MEDKIT)   # type 2
        inv.selected_type = 0
        inv.select_next()
        assert inv.selected_type == settings.ITEM_TYPE_MEDKIT

    def test_select_prev_wraps(self):
        inv = Inventory()
        inv.pickup(settings.ITEM_TYPE_PLASMA)   # type 11
        inv.selected_type = 0
        inv.select_prev()
        assert inv.selected_type == settings.ITEM_TYPE_PLASMA

    def test_selected_type_auto_clears_when_count_zero(self):
        inv = Inventory()
        inv.pickup(settings.ITEM_TYPE_MEDKIT)
        inv.selected_type = settings.ITEM_TYPE_MEDKIT
        inv.drop(settings.ITEM_TYPE_MEDKIT)
        # after drop, selected_type should move to next available or -1
        assert inv.counts[inv.selected_type] > 0 or inv.selected_type == -1

    def test_count_total(self):
        inv = Inventory()
        inv.pickup(settings.ITEM_TYPE_CLOAK)
        inv.pickup(settings.ITEM_TYPE_CLOAK)
        inv.pickup(settings.ITEM_TYPE_MEDKIT)
        assert inv.count_total() == 3


# ---------------------------------------------------------------------------
# ItemEffects
# ---------------------------------------------------------------------------

class _FakePlayer:
    hp = 10
    is_cloaked = False
    _cloak_timer = 0.0
    bullet_type = 0


class TestItemEffects:
    def test_medkit_restores_hp(self):
        player = _FakePlayer()
        ItemEffects.use_medkit(player)
        assert player.hp == settings.MAX_HEALTH

    def test_cloak_sets_flag_and_timer(self):
        player = _FakePlayer()
        ItemEffects.use_cloak(player)
        assert player.is_cloaked is True
        assert player.is_cloaked == True

    def test_rocket_sets_bullet_type(self):
        player = _FakePlayer()
        ItemEffects.use_rocket(player)
        assert player.bullet_type == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest src/tests/test_inventory.py -v 2>&1 | head -30
```

Expected: `ImportError: cannot import name 'WorldItem' from 'src.inventory'` (module doesn't exist yet)

- [ ] **Step 3: Implement `src/inventory.py`**

Create `src/inventory.py`:

```python
"""
src/inventory.py — Item world objects and player inventory.

WorldItem  : an item sitting on the map, produced by a factory.
Inventory  : the player's held items (counts per type, selection state).
ItemEffects: stateless helper functions that apply item effects to the player.

Import rule: this module imports only `settings` and `pygame`.
No imports from other src/ modules — avoids circular imports.
Factory references on WorldItem are stored as plain `object` and
dereferenced by game.py (which imports both modules).
"""

import settings

# Orb animation cycles every second (matches C++ Animationtick + 1000 ms)
_ORB_ANIM_INTERVAL = 1.0
_ORB_ANIM_FRAMES   = 3


class WorldItem:
    """An item sitting on the map at a tile position.

    Produced by a factory (PlacedBuilding) and consumed by player pickup.
    `factory_ref` is an opaque reference back to the producing factory;
    game.py decrements factory.world_item_count on pickup.
    """

    def __init__(
        self,
        tile_x: int,
        tile_y: int,
        item_type: int,
        factory_ref: object = None,
    ) -> None:
        self.tile_x      = tile_x
        self.tile_y      = tile_y
        self.item_type   = item_type
        self.factory_ref = factory_ref   # PlacedBuilding | None (no import needed)
        self.animation   = 0
        self._anim_timer = 0.0

    @property
    def world_center(self) -> tuple[int, int]:
        """World-pixel center of this item's tile."""
        half = settings.TILE_SIZE // 2
        return (
            self.tile_x * settings.TILE_SIZE + half,
            self.tile_y * settings.TILE_SIZE + half,
        )

    def update(self, dt: float) -> None:
        """Advance animation (Orb only)."""
        if self.item_type != settings.ITEM_TYPE_ORB:
            return
        self._anim_timer += dt
        while self._anim_timer >= _ORB_ANIM_INTERVAL:
            self._anim_timer -= _ORB_ANIM_INTERVAL
            self.animation = (self.animation + 1) % _ORB_ANIM_FRAMES


class Inventory:
    """The player's held items.

    counts[type] = number of items of that type currently held.
    selected_type = item type currently highlighted for drop/use (-1 = none).
    """

    def __init__(self) -> None:
        self.counts: list[int] = [0] * settings.NUM_ITEM_TYPES
        self.selected_type: int = -1   # -1 = nothing selected

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def pickup(self, item_type: int) -> bool:
        """Try to add one of item_type to inventory.

        Returns True on success, False if at cap.
        Automatically selects this type if nothing was selected.
        """
        if self.counts[item_type] >= settings.ITEM_MAX_COUNTS[item_type]:
            return False
        self.counts[item_type] += 1
        if self.selected_type == -1:
            self.selected_type = item_type
        return True

    def drop(self, item_type: int) -> bool:
        """Remove one of item_type from inventory.

        Returns True on success, False if none held.
        If this empties the selected slot, advances to the next available type.
        """
        if self.counts[item_type] <= 0:
            return False
        self.counts[item_type] -= 1
        if self.counts[item_type] == 0 and self.selected_type == item_type:
            self._advance_selection()
        return True

    def select_next(self) -> None:
        """Cycle selected_type forward through types with count > 0."""
        self._cycle(+1)

    def select_prev(self) -> None:
        """Cycle selected_type backward through types with count > 0."""
        self._cycle(-1)

    def count_total(self) -> int:
        return sum(self.counts)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _advance_selection(self) -> None:
        """After emptying a slot, move selection to next available type."""
        self._cycle(+1)

    def _cycle(self, direction: int) -> None:
        """Move selected_type by `direction` (+1 or -1), skipping empty slots."""
        n = settings.NUM_ITEM_TYPES
        start = self.selected_type if self.selected_type != -1 else 0
        for i in range(1, n + 1):
            candidate = (start + i * direction) % n
            if self.counts[candidate] > 0:
                self.selected_type = candidate
                return
        self.selected_type = -1   # nothing in inventory


class ItemEffects:
    """Stateless item-use effects applied to the player object.

    Each method mutates the player duck-typed object directly.
    Player must expose: hp, is_cloaked, _cloak_timer, bullet_type.
    """

    @staticmethod
    def use_medkit(player) -> None:
        """Restore player HP to full (C++ MAX_HEALTH = 40)."""
        player.hp = settings.MAX_HEALTH

    @staticmethod
    def use_cloak(player) -> None:
        """Activate cloak for TIMER_CLOAK seconds."""
        player.is_cloaked  = True
        player._cloak_timer = settings.TIMER_CLOAK

    @staticmethod
    def use_rocket(player) -> None:
        """Upgrade bullet type to Rocket (type 1)."""
        player.bullet_type = 1
```

- [ ] **Step 4: Run tests and confirm they pass**

```bash
python3 -m pytest src/tests/test_inventory.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/inventory.py src/tests/test_inventory.py
git commit -m "feat: add WorldItem, Inventory, ItemEffects classes"
```

---

## Task 3: Add factory production to `building.py`

**Files:**
- Modify: `src/building.py` — `PlacedBuilding.__init__`, `PlacedBuilding.update`, `BuildingManager.update`
- Modify: `src/tests/test_building.py` — add factory production tests

- [ ] **Step 1: Write failing factory production tests**

Append to `src/tests/test_building.py`:

```python
# ---------------------------------------------------------------------------
# Factory production tests
# ---------------------------------------------------------------------------
import settings
from src.inventory import WorldItem


class TestFactoryProduction:
    """PlacedBuilding produces WorldItems when at full pop after 7s."""

    def _make_factory(self, menu_index: int = 3) -> "PlacedBuilding":
        """menu_index=3 → Bazooka Factory (type 101, item_type=1=Rocket)."""
        from src.building import PlacedBuilding
        pb = PlacedBuilding(tile_x=10, tile_y=10, menu_index=menu_index)
        pb.pop = settings.POP_MAX   # force full population
        return pb

    def test_factory_has_item_type(self):
        pb = self._make_factory(menu_index=3)   # type 101 → item 1
        assert pb.item_type == 1

    def test_non_factory_has_no_item_type(self):
        from src.building import PlacedBuilding
        pb = PlacedBuilding(tile_x=0, tile_y=0, menu_index=0)   # Hospital
        assert pb.item_type is None

    def test_factory_produces_item_after_interval(self):
        pb = self._make_factory()
        result = pb.update(settings.FACTORY_PRODUCE_INTERVAL + 0.1)
        assert isinstance(result, WorldItem)
        assert result.item_type == pb.item_type

    def test_factory_sets_spawn_position(self):
        pb = self._make_factory()
        item = pb.update(settings.FACTORY_PRODUCE_INTERVAL + 0.1)
        assert item.tile_x == pb.tile_x + 1
        assert item.tile_y == pb.tile_y + 1

    def test_factory_respects_world_cap(self):
        pb = self._make_factory()
        cap = settings.ITEM_MAX_COUNTS[pb.item_type]
        pb.world_item_count = cap   # already at cap
        result = pb.update(settings.FACTORY_PRODUCE_INTERVAL + 0.1)
        assert result is None

    def test_factory_increments_world_item_count(self):
        pb = self._make_factory()
        pb.update(settings.FACTORY_PRODUCE_INTERVAL + 0.1)
        assert pb.world_item_count == 1

    def test_factory_no_produce_before_interval(self):
        pb = self._make_factory()
        result = pb.update(settings.FACTORY_PRODUCE_INTERVAL - 0.1)
        assert result is None

    def test_non_factory_update_returns_none(self):
        from src.building import PlacedBuilding
        pb = PlacedBuilding(tile_x=0, tile_y=0, menu_index=0)   # Hospital
        pb.pop = settings.POP_MAX
        result = pb.update(100.0)
        assert result is None

    def test_factory_no_produce_without_full_pop(self):
        pb = self._make_factory()
        pb.pop = settings.POP_MAX - 1   # not full
        result = pb.update(settings.FACTORY_PRODUCE_INTERVAL + 0.1)
        assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest src/tests/test_building.py::TestFactoryProduction -v 2>&1 | head -20
```

Expected: failures on missing `item_type`, `world_item_count` attributes.

- [ ] **Step 3: Modify `PlacedBuilding.__init__` in `src/building.py`**

At the top of `building.py`, add the import:
```python
from src.inventory import WorldItem
```

In `PlacedBuilding.__init__`, after `self._pop_timer: float = settings.POP_TICK`, add:

```python
        # Factory production
        btype = settings.BUILDING_TYPES[menu_index]
        bclass_local = btype // 100
        self.item_type: int | None = (btype % 100) if bclass_local == 1 else None
        self._produce_timer: float = 0.0
        self.world_item_count: int = 0
```

- [ ] **Step 4: Modify `PlacedBuilding.update` to return `WorldItem | None`**

The current `update` method only calls `_anim.tick(dt)`. Replace it:

```python
    def update(self, dt: float) -> "WorldItem | None":
        """Advance animation and factory production. Returns a new WorldItem or None."""
        self._anim.tick(dt)
        return self._update_production(dt)

    def _update_production(self, dt: float) -> "WorldItem | None":
        """Tick factory timer; produce a WorldItem when ready."""
        if self.item_type is None:
            return None                       # not a factory
        if not self.has_max_pop:
            return None                       # needs full population
        cap = settings.ITEM_MAX_COUNTS[self.item_type]
        if self.world_item_count >= cap:
            return None                       # world is full of this item type

        self._produce_timer += dt
        if self._produce_timer < settings.FACTORY_PRODUCE_INTERVAL:
            return None

        self._produce_timer -= settings.FACTORY_PRODUCE_INTERVAL
        self.world_item_count += 1
        return WorldItem(
            tile_x=self.tile_x + 1,
            tile_y=self.tile_y + 1,
            item_type=self.item_type,
            factory_ref=self,
        )
```

- [ ] **Step 5: Modify `BuildingManager.update` to collect and return spawned items**

Current `update` in `BuildingManager`:
```python
    def update(self, dt: float) -> None:
        for b in self._buildings:
            b.update(dt)
        for p in self._placed:
            p.update(dt)
            p.update_population(dt)
```

Replace with:
```python
    def update(self, dt: float) -> list:
        """Tick all buildings. Returns list of newly spawned WorldItems."""
        for b in self._buildings:
            b.update(dt)
        spawned = []
        for pb in self._placed:
            item = pb.update(dt)
            pb.update_population(dt)
            if item is not None:
                spawned.append(item)
        return spawned
```

- [ ] **Step 6: Run factory tests**

```bash
python3 -m pytest src/tests/test_building.py -v
```

Expected: all tests pass (existing + new factory tests).

- [ ] **Step 7: Commit**

```bash
git add src/building.py src/tests/test_building.py
git commit -m "feat: factory production timer spawns WorldItems"
```

---

## Task 4: Add player state for item effects

**Files:**
- Modify: `src/player.py`
- Modify: `src/tests/test_player.py` — add cloak timer tests

- [ ] **Step 1: Write failing cloak timer tests**

Append to `src/tests/test_player.py`:

```python
class TestPlayerItemState:
    def _make_player(self):
        from src.player import Player
        return Player(x=0.0, y=0.0)

    def test_player_starts_uncloaked(self):
        p = self._make_player()
        assert p.is_cloaked is False
        assert p._cloak_timer == 0.0
        assert p.bullet_type == 0

    def test_cloak_expires_after_timer(self):
        p = self._make_player()
        import settings
        p.is_cloaked = True
        p._cloak_timer = settings.TIMER_CLOAK
        p.update(settings.TIMER_CLOAK + 0.1)
        assert p.is_cloaked is False

    def test_cloak_still_active_before_expiry(self):
        p = self._make_player()
        import settings
        p.is_cloaked = True
        p._cloak_timer = settings.TIMER_CLOAK
        p.update(settings.TIMER_CLOAK - 0.1)
        assert p.is_cloaked is True
```

- [ ] **Step 2: Run to verify they fail**

```bash
python3 -m pytest src/tests/test_player.py::TestPlayerItemState -v 2>&1 | head -20
```

Expected: `AttributeError: 'Player' object has no attribute 'is_cloaked'`

- [ ] **Step 3: Add state to `Player.__init__` in `src/player.py`**

After `self._fire_requested = False` (line 50), add:

```python
        # Item state
        self.is_cloaked:   bool  = False
        self._cloak_timer: float = 0.0
        self.bullet_type:  int   = 0    # 0=laser, 1=rocket
```

- [ ] **Step 4: Tick cloak timer in `Player.update`**

In `Player.update()`, after `self._fire_cooldown = max(0.0, self._fire_cooldown - dt)`, add:

```python
        if self.is_cloaked:
            self._cloak_timer -= dt
            if self._cloak_timer <= 0.0:
                self._cloak_timer = 0.0
                self.is_cloaked   = False
```

- [ ] **Step 5: Run player tests**

```bash
python3 -m pytest src/tests/test_player.py -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/player.py src/tests/test_player.py
git commit -m "feat: add player cloak timer and bullet_type state"
```

---

## Task 5: Add `draw_inventory` to `hud.py`

**Files:**
- Modify: `src/hud.py`
- Modify: `src/tests/test_hud_widgets.py` — add draw_inventory smoke test

- [ ] **Step 1: Write a smoke test for `draw_inventory`**

Append to `src/tests/test_hud_widgets.py`:

```python
class TestDrawInventory:
    """Smoke test — verifies draw_inventory runs without error."""

    def test_draw_inventory_no_crash(self, pygame_surface):
        """draw_inventory must not raise with an empty inventory."""
        import pygame
        import settings
        from src.hud import draw_inventory
        from src.inventory import Inventory

        inv = Inventory()
        font = pygame.font.SysFont("consolas", 14)
        # Minimal 32x32 sheets
        items_sheet = pygame.Surface((32 * 12, 96))
        sel_sheet   = pygame.Surface((32, 32))
        draw_inventory(pygame_surface, inv, items_sheet, sel_sheet, font)
        # No assertion needed — just must not raise

    def test_draw_inventory_with_items(self, pygame_surface):
        import pygame
        import settings
        from src.hud import draw_inventory
        from src.inventory import Inventory

        inv = Inventory()
        inv.pickup(settings.ITEM_TYPE_MEDKIT)
        inv.pickup(settings.ITEM_TYPE_MEDKIT)
        font = pygame.font.SysFont("consolas", 14)
        items_sheet = pygame.Surface((32 * 12, 96))
        sel_sheet   = pygame.Surface((32, 32))
        draw_inventory(pygame_surface, inv, items_sheet, sel_sheet, font)
```

Check `src/tests/conftest.py` for the `pygame_surface` fixture — the session already has `pygame_session` (autouse init), so add only the surface fixture if it's missing:

```python
# In conftest.py — add ONLY this fixture (pygame_session already exists)
import pygame

@pytest.fixture
def pygame_surface():
    return pygame.Surface((800, 600))
```

- [ ] **Step 2: Run to verify they fail**

```bash
python3 -m pytest src/tests/test_hud_widgets.py::TestDrawInventory -v 2>&1 | head -20
```

Expected: `ImportError: cannot import name 'draw_inventory' from 'src.hud'`

- [ ] **Step 3: Add `draw_inventory` function to `src/hud.py`**

Add the following import at the top of `hud.py` (after existing imports):
```python
import settings
```
(It's already there — skip if present.)

Append at the bottom of `hud.py`:

```python

def draw_inventory(
    screen: pygame.Surface,
    inventory,
    items_sheet: pygame.Surface,
    selection_sheet: pygame.Surface,
    font: pygame.font.Font,
) -> None:
    """Draw the 3×4 inventory grid on the right panel.

    Layout mirrors C++ CDrawing::DrawInventory():
      - 12 item types in a 4-row × 3-col grid
      - Each slot: 32×32 icon from imgItems.bmp at src_x=type*32, src_y=0
      - Selected slot: imgInventorySelection.bmp drawn underneath icon
      - Count > 1: yellow number at slot_x+22, slot_y+12

    `inventory` is duck-typed — must expose .counts (list[int]) and
    .selected_type (int).
    """
    yellow = (255, 215, 0)

    for row, row_y in enumerate(settings.INV_ROW_OFFSETS):
        for col, col_x in enumerate(settings.INV_COL_OFFSETS):
            item_type = row * 3 + col
            count = inventory.counts[item_type]
            if count <= 0:
                continue

            slot_x = settings.PANEL_X + col_x
            slot_y = settings.PANEL_Y + row_y

            # Selection highlight drawn under icon
            if item_type == inventory.selected_type:
                screen.blit(selection_sheet, (slot_x, slot_y),
                            pygame.Rect(0, 0, settings.INV_ICON_SIZE, settings.INV_ICON_SIZE))

            # Item icon: small 32×32 row (src_y=0)
            src_x = item_type * settings.INV_ICON_SIZE
            screen.blit(items_sheet, (slot_x, slot_y),
                        pygame.Rect(src_x, 0, settings.INV_ICON_SIZE, settings.INV_ICON_SIZE))

            # Count label if more than one
            if count > 1:
                label = font.render(str(count), True, yellow)
                screen.blit(label, (slot_x + 22, slot_y + 12))
```

- [ ] **Step 4: Run hud tests**

```bash
python3 -m pytest src/tests/test_hud_widgets.py -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/hud.py src/tests/test_hud_widgets.py src/tests/conftest.py
git commit -m "feat: add draw_inventory to hud"
```

---

## Task 6: Wire everything into `game.py`

**Files:**
- Modify: `src/game.py`

This task is integration — no new unit tests (integration is verified by running the game). Each step is small and isolated.

- [ ] **Step 1: Add imports to `game.py`**

After the existing imports block (around line 34), add:

```python
from src.inventory import Inventory, WorldItem, ItemEffects
from src.hud       import draw_inventory
```

- [ ] **Step 2: Load `imgInventorySelection.bmp` in `_load_assets`**

In `_load_assets`, after the `self._items_sheet` line (around line 113), add:

```python
        self._inv_selection_sheet = _load_colorkeyed_sheet(
            require_asset("imgInventorySelection.bmp")
        )
```

- [ ] **Step 3: Create `Inventory` and `world_items` list in `_create_player`**

In `_create_player`, after `self._explosions: list[Explosion] = []`, add:

```python
        self._inventory:   Inventory        = Inventory()
        self._world_items: list[WorldItem]  = []
```

- [ ] **Step 4: Collect spawned items and tick world items in `_update`**

Replace the `self._buildings.update(dt)` line in `_update` with:

```python
        spawned = self._buildings.update(dt)
        self._world_items.extend(spawned)
        for wi in self._world_items:
            wi.update(dt)
```

Also update the `_build_state.update` call — it passes `placed_buildings` which is unchanged:
```python
        self._build_state.update(dt, self._buildings.placed_buildings)
```
(No change needed here — just confirming it stays the same.)

- [ ] **Step 5: Add key handlers for U, D, [, ], H, C in `_handle_events`**

In `_handle_events`, inside the `if event.type == pygame.KEYDOWN:` block, append after the ESC handler:

```python
                elif event.key == pygame.K_u:
                    self._try_pickup()
                elif event.key == pygame.K_d:
                    self._try_drop()
                elif event.key == pygame.K_LEFTBRACKET:
                    self._inventory.select_prev()
                elif event.key == pygame.K_RIGHTBRACKET:
                    self._inventory.select_next()
                elif event.key == pygame.K_h:
                    self._try_use_medkit()
                elif event.key == pygame.K_c:
                    self._try_use_cloak()
```

- [ ] **Step 6: Add pickup/drop/use helper methods to `Game`**

Add these private methods before `_quit`:

```python
    def _try_pickup(self) -> None:
        """Pick up the nearest world item within ITEM_PICKUP_RANGE tiles."""
        px = self._player.x + settings.TANK_FRAME_W / 2
        py = self._player.y + settings.TANK_FRAME_H / 2
        range_px = settings.ITEM_PICKUP_RANGE * settings.TILE_SIZE

        best = None
        best_dist = float("inf")
        for wi in self._world_items:
            cx, cy = wi.world_center
            dist = ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5
            if dist < range_px and dist < best_dist:
                best = wi
                best_dist = dist

        if best is None:
            return
        if self._inventory.pickup(best.item_type):
            # Decrement factory count so it can produce more
            if best.factory_ref is not None:
                best.factory_ref.world_item_count -= 1
            self._world_items.remove(best)
            # Passive rocket effect: upgrade bullet type while held
            if best.item_type == settings.ITEM_TYPE_ROCKET:
                self._player.bullet_type = 1

    def _try_drop(self) -> None:
        """Drop the currently selected item at the player's tile."""
        sel = self._inventory.selected_type
        if sel == -1 or self._inventory.counts[sel] <= 0:
            return
        if self._inventory.drop(sel):
            tx = int(self._player.x // settings.TILE_SIZE)
            ty = int(self._player.y // settings.TILE_SIZE)
            self._world_items.append(WorldItem(tile_x=tx, tile_y=ty, item_type=sel))
            # Revert rocket bullet type if no more rockets
            if sel == settings.ITEM_TYPE_ROCKET and self._inventory.counts[sel] == 0:
                self._player.bullet_type = 0

    def _try_use_medkit(self) -> None:
        if self._inventory.counts[settings.ITEM_TYPE_MEDKIT] > 0:
            ItemEffects.use_medkit(self._player)
            self._inventory.drop(settings.ITEM_TYPE_MEDKIT)

    def _try_use_cloak(self) -> None:
        if self._inventory.counts[settings.ITEM_TYPE_CLOAK] > 0:
            ItemEffects.use_cloak(self._player)
            self._inventory.drop(settings.ITEM_TYPE_CLOAK)
```

- [ ] **Step 7: Draw world items in `_draw`**

In `_draw`, inside the `set_clip(field_rect)` block, after `self._buildings.draw_sprites(...)` and before `self._draw_player()`, add:

```python
        self._draw_world_items(cam_x, cam_y)
```

Add the method:

```python
    def _draw_world_items(self, cam_x: float, cam_y: float) -> None:
        """Draw all world items clipped to the field viewport."""
        for wi in self._world_items:
            cx, cy = wi.world_center
            sx = self._field_rect.x + int(cx - cam_x) - settings.ITEM_WORLD_SIZE // 2
            sy = self._field_rect.y + int(cy - cam_y) - settings.ITEM_WORLD_SIZE // 2

            src_x = wi.item_type * settings.ITEM_WORLD_SIZE
            src_y = settings.ITEM_WORLD_SRC_Y
            if wi.item_type == settings.ITEM_TYPE_ORB:
                src_y += wi.animation * settings.ITEM_WORLD_SIZE

            self._screen.blit(
                self._items_sheet,
                (sx, sy),
                pygame.Rect(src_x, src_y, settings.ITEM_WORLD_SIZE, settings.ITEM_WORLD_SIZE),
            )
```

- [ ] **Step 8: Call `draw_inventory` in `_draw`**

In `_draw`, after `self._draw_health_bar()`, add:

```python
        draw_inventory(
            self._screen, self._inventory,
            self._items_sheet, self._inv_selection_sheet, self._font,
        )
```

- [ ] **Step 9: Run the unit test suite**

```bash
python3 -m pytest src/tests/ -v
```

Expected: all tests pass.

- [ ] **Step 10: Run the game and verify manually**

```bash
python3 battle_city.py
```

Manual checklist:
- [ ] Game starts without errors
- [ ] Build a House → Research → Factory (takes ~10s each for research + production)
- [ ] Drive near a factory; after 7s a world item sprite appears at tile (factory+1, factory+1)
- [ ] Press `U` near the item — it disappears from the world and appears in inventory panel
- [ ] Press `[` / `]` to cycle selection; selected item shows highlight
- [ ] Press `D` — item reappears on the map at player position
- [ ] Pick up a MedKit, take some bullet damage (shoot a wall to confirm hp tracking works), press `H` — HP restores to 40
- [ ] Pick up a Cloak, press `C` — `is_cloaked` set (no visual effect yet, confirm via print if desired)

- [ ] **Step 11: Commit**

```bash
git add src/game.py
git commit -m "feat: wire inventory pickup/drop/use and world item rendering into game"
```

---

## Task 7: Final test run and cleanup

- [ ] **Step 1: Run full test suite**

```bash
python3 -m pytest src/tests/ -v
```

Expected: all tests pass, zero failures.

- [ ] **Step 2: Update CLAUDE.md "What's Not Yet Implemented" section**

Remove from the list:
- ~~Bullet hit detection~~ (still pending)

Add to completed features (or update the comment):
```
- Item inventory: factory production, pickup (U), drop (D), inventory panel, MedKit/Cloak/Rocket effects
```

- [ ] **Step 3: Final commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md — inventory system implemented"
```
