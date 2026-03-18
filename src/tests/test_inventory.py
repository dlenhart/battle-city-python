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
        assert player._cloak_timer == settings.TIMER_CLOAK

    def test_rocket_sets_bullet_type(self):
        player = _FakePlayer()
        ItemEffects.use_rocket(player)
        assert player.bullet_type == 1
