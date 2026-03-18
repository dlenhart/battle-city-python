"""Tests for src/building.py — Building properties, animation, and collision."""

import pytest
import settings
from src.building import Building, BuildingManager, CITY_NAMES, _ANIM_INTERVAL, _NUM_ANIM_STEPS, _BSIZE


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def make_building(tile_x=10, tile_y=10, city_index=0):
    return Building(tile_x, tile_y, city_index)


def make_map_with_city(tile_x=10, tile_y=10) -> list[list[int]]:
    """Return a minimal MAP_SIZE × MAP_SIZE map with one city at (tile_x, tile_y)."""
    size = settings.MAP_SIZE
    data = [[settings.MAP_TILE_EMPTY] * size for _ in range(size)]
    data[tile_x][tile_y] = settings.MAP_TILE_CITY
    return data


# ------------------------------------------------------------------
# Building properties
# ------------------------------------------------------------------

class TestBuildingProperties:
    def test_name_from_city_names(self):
        b = make_building(city_index=0)
        assert b.name == CITY_NAMES[0]

    def test_name_fallback_out_of_range(self):
        b = make_building(city_index=999)
        assert b.name == "City 999"

    def test_world_x(self):
        b = make_building(tile_x=10)
        assert b.world_x == (10 - 2) * settings.TILE_SIZE

    def test_world_y(self):
        b = make_building(tile_y=10)
        assert b.world_y == (10 - 2) * settings.TILE_SIZE

    def test_sprite_src_is_row_zero(self):
        b = make_building()
        src = b.sprite_src
        # Row 0 of imgBuildings.bmp starts at y=0
        assert src.y == 0
        assert src.width  == _BSIZE
        assert src.height == _BSIZE

    def test_sprite_src_x_cycles_through_three_frames(self):
        b = make_building()
        seen_xs = set()
        for step in range(_NUM_ANIM_STEPS):
            b._anim._step = step
            seen_xs.add(b.sprite_src.x)
        # 6 steps → 3 unique source X offsets (0, 144, 288)
        assert seen_xs == {0, _BSIZE, _BSIZE * 2}


# ------------------------------------------------------------------
# Building animation (now delegated to AnimationTimer)
# ------------------------------------------------------------------

class TestBuildingAnimation:
    def test_anim_step_advances_after_interval(self):
        b = make_building()
        b._anim._step  = 0
        b._anim._timer = 0.0
        b.update(_ANIM_INTERVAL)
        assert b._anim.step == 1

    def test_anim_step_wraps_at_num_steps(self):
        b = make_building()
        b._anim._step  = _NUM_ANIM_STEPS - 1
        b._anim._timer = 0.0
        b.update(_ANIM_INTERVAL)
        assert b._anim.step == 0

    def test_anim_does_not_advance_before_interval(self):
        b = make_building()
        b._anim._step  = 0
        b._anim._timer = 0.0
        b.update(_ANIM_INTERVAL * 0.9)
        assert b._anim.step == 0

    def test_large_dt_still_only_one_step(self):
        # AnimationTimer.tick uses 'if' not 'while': one step per call.
        b = make_building()
        b._anim._step  = 0
        b._anim._timer = 0.0
        b.update(_ANIM_INTERVAL * 3)
        assert b._anim.step == 1


# ------------------------------------------------------------------
# BuildingManager — loading and city names
# ------------------------------------------------------------------

class TestBuildingManagerLoad:
    def test_loads_single_city(self):
        data = make_map_with_city(tile_x=10, tile_y=10)
        bm = BuildingManager(data)
        assert len(bm.buildings) == 1

    def test_empty_map_has_no_buildings(self):
        size = settings.MAP_SIZE
        data = [[settings.MAP_TILE_EMPTY] * size for _ in range(size)]
        bm = BuildingManager(data)
        assert len(bm.buildings) == 0

    def test_city_index_assigned(self):
        data = make_map_with_city(tile_x=10, tile_y=10)
        bm = BuildingManager(data)
        # Only one city — citIndex starts at 63, first city gets 63
        assert bm.buildings[0].city_index == 63

    def test_multiple_cities_get_descending_indices(self):
        size = settings.MAP_SIZE
        data = [[settings.MAP_TILE_EMPTY] * size for _ in range(size)]
        # Place three cities; scan order is outer j (Y) then inner i (X)
        # so smallest j first → cities at (5,5), (6,5), (5,6)
        data[5][5] = settings.MAP_TILE_CITY
        data[6][5] = settings.MAP_TILE_CITY
        data[5][6] = settings.MAP_TILE_CITY
        bm = BuildingManager(data)
        indices = [b.city_index for b in bm.buildings]
        assert indices == sorted(indices, reverse=True)  # descending

    def test_city_tile_position_stored(self):
        data = make_map_with_city(tile_x=20, tile_y=30)
        bm = BuildingManager(data)
        b = bm.buildings[0]
        assert b.tile_x == 20
        assert b.tile_y == 30


# ------------------------------------------------------------------
# BuildingManager — collision (blocked tiles)
# ------------------------------------------------------------------

class TestBuildingManagerCollision:
    def test_top_two_rows_of_footprint_are_blocked(self):
        data = make_map_with_city(tile_x=10, tile_y=10)
        bm = BuildingManager(data)
        # Footprint: X = tile_x-2 .. tile_x, Y = tile_y-2 .. tile_y-1 blocked
        for dx in range(-2, 1):       # -2, -1, 0
            for dy in range(-2, 0):   # -2, -1
                assert bm.is_tile_blocked(10 + dx, 10 + dy), \
                    f"Expected ({10+dx},{10+dy}) to be blocked"

    def test_bottom_row_of_footprint_is_walkable(self):
        data = make_map_with_city(tile_x=10, tile_y=10)
        bm = BuildingManager(data)
        for dx in range(-2, 1):
            assert not bm.is_tile_blocked(10 + dx, 10), \
                f"Expected ({10+dx},10) to be walkable"

    def test_tiles_outside_footprint_not_blocked(self):
        data = make_map_with_city(tile_x=10, tile_y=10)
        bm = BuildingManager(data)
        assert not bm.is_tile_blocked(10 + 1, 10 - 1)   # right of footprint
        assert not bm.is_tile_blocked(10 - 3, 10 - 1)   # left of footprint
        assert not bm.is_tile_blocked(10,     10 - 3)   # above footprint

    def test_is_tile_blocked_returns_false_for_arbitrary_tile(self):
        size = settings.MAP_SIZE
        data = [[settings.MAP_TILE_EMPTY] * size for _ in range(size)]
        bm = BuildingManager(data)
        assert not bm.is_tile_blocked(50, 50)


# ------------------------------------------------------------------
# BuildingManager — random_spawn
# ------------------------------------------------------------------

class TestBuildingManagerSpawn:
    def test_spawn_returns_two_floats(self):
        data = make_map_with_city(tile_x=10, tile_y=10)
        bm = BuildingManager(data)
        result = bm.random_spawn()
        assert len(result) == 2
        assert all(isinstance(v, float) for v in result)

    def test_spawn_x_in_walkable_row_centre(self):
        data = make_map_with_city(tile_x=10, tile_y=10)
        bm = BuildingManager(data)
        sx, _ = bm.random_spawn()
        # Centre-X of walkable row = (tile_x - 1) * TILE_SIZE
        expected_x = float((10 - 1) * settings.TILE_SIZE)
        assert sx == expected_x

    def test_spawn_y_at_walkable_row(self):
        data = make_map_with_city(tile_x=10, tile_y=10)
        bm = BuildingManager(data)
        _, sy = bm.random_spawn()
        expected_y = float(10 * settings.TILE_SIZE)
        assert sy == expected_y


# ------------------------------------------------------------------
# CITY_NAMES list
# ------------------------------------------------------------------

class TestCityNames:
    def test_exactly_64_names(self):
        assert len(CITY_NAMES) == 64

    def test_no_empty_names(self):
        assert all(name for name in CITY_NAMES)


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
