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
