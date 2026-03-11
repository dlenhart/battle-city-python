"""Tests for src/minimap.py — Scrolling minimap toggle and coordinate logic."""

import pytest
import settings
from src.minimap import (
    Minimap, MINIMAP_W, MINIMAP_H, VIEWPORT_TILES, _MM_SCALE_X, _MM_SCALE_Y,
    _COLOR_ROCK, _COLOR_LAVA, _COLOR_BG, _PLAYER_DOT,
)


# ------------------------------------------------------------------
# Minimal stubs — no real asset files needed
# ------------------------------------------------------------------

def _make_map_data():
    """Return a sparse map with tiles at positions that will be sampled."""
    size = settings.MAP_SIZE
    data = [[settings.MAP_TILE_EMPTY] * size for _ in range(size)]
    # Place tiles at coordinates derived from known minimap pixels so the
    # sampler (tx = int(mx * _SCALE)) hits them exactly.
    _rock_tile = int(3 * (settings.MAP_SIZE / VIEWPORT_TILES))
    _lava_tile = int(8 * (settings.MAP_SIZE / VIEWPORT_TILES))
    data[_rock_tile][_rock_tile] = settings.MAP_TILE_ROCK
    data[_lava_tile][_lava_tile] = settings.MAP_TILE_LAVA
    return data


def _fake_buildings(tile_x=50, tile_y=50):
    class _B:
        pass
    b = _B()
    b.tile_x = tile_x
    b.tile_y = tile_y

    class _BM:
        buildings = [b]
    return _BM()


def _make_minimap(**kwargs):
    return Minimap(_make_map_data(), _fake_buildings(**kwargs))


# ------------------------------------------------------------------
# Toggle behaviour
# ------------------------------------------------------------------

class TestMinimapToggle:
    def test_visible_by_default(self):
        # Minimap is always shown in the interface panel radar slot
        mm = _make_minimap()
        assert mm.visible is True

    def test_toggle_once_hides(self):
        mm = _make_minimap()
        mm.toggle()
        assert mm.visible is False

    def test_toggle_twice_restores(self):
        mm = _make_minimap()
        mm.toggle()
        mm.toggle()
        assert mm.visible is True


# ------------------------------------------------------------------
# Viewport constants
# ------------------------------------------------------------------

class TestViewportConstants:
    def test_viewport_tiles_is_five_field_widths(self):
        expected = int(settings.FIELD_WIDTH * 5 / settings.TILE_SIZE)
        assert VIEWPORT_TILES == expected

    def test_mm_scale_matches_ratio(self):
        assert _MM_SCALE_X == pytest.approx(MINIMAP_W / VIEWPORT_TILES)
        assert _MM_SCALE_Y == pytest.approx(MINIMAP_H / VIEWPORT_TILES)


# ------------------------------------------------------------------
# _world_to_minimap helper
# ------------------------------------------------------------------

class TestWorldToMinimap:
    """The static helper converts world coords relative to a viewport offset."""

    def _call(self, world_x, world_y, left=0, top=0):
        return Minimap._world_to_minimap(world_x, world_y, left, top)

    def test_world_origin_with_zero_offset(self):
        mx, my = self._call(0.0, 0.0, left=0, top=0)
        assert mx == 0
        assert my == 0

    def test_position_one_tile_in(self):
        mx, my = self._call(
            float(settings.TILE_SIZE), float(settings.TILE_SIZE),
            left=0, top=0,
        )
        assert mx == pytest.approx(int(_MM_SCALE_X), abs=1)
        assert my == pytest.approx(int(_MM_SCALE_Y), abs=1)

    def test_left_top_offset_shifts_result(self):
        # Viewport starts at tile (10, 10); player at tile (15, 15)
        wx = 15 * settings.TILE_SIZE
        wy = 15 * settings.TILE_SIZE
        mx, my = self._call(wx, wy, left=10, top=10)
        assert mx == pytest.approx(int(5 * _MM_SCALE_X), abs=1)
        assert my == pytest.approx(int(5 * _MM_SCALE_Y), abs=1)

    def test_clamped_to_minimap_bounds(self):
        # Way off screen — should clamp to MINIMAP_W/H - 1
        mx, my = self._call(999999.0, 999999.0, left=0, top=0)
        assert mx == MINIMAP_W - 1
        assert my == MINIMAP_H - 1

    def test_returns_integers(self):
        mx, my = self._call(1234.5, 6789.1, left=5, top=5)
        assert isinstance(mx, int)
        assert isinstance(my, int)


# ------------------------------------------------------------------
# Terrain surface
# ------------------------------------------------------------------

class TestBuildTerrain:
    def test_surface_is_map_size(self):
        surf = Minimap._build_terrain(_make_map_data())
        assert surf.get_width()  == settings.MAP_SIZE
        assert surf.get_height() == settings.MAP_SIZE

    def test_empty_tile_is_black(self):
        data = [[settings.MAP_TILE_EMPTY] * settings.MAP_SIZE
                for _ in range(settings.MAP_SIZE)]
        surf = Minimap._build_terrain(data)
        assert surf.get_at((0, 0))[:3] == _COLOR_BG

    def test_rock_tile_is_white(self):
        size = settings.MAP_SIZE
        data = [[settings.MAP_TILE_EMPTY] * size for _ in range(size)]
        data[5][5] = settings.MAP_TILE_ROCK
        surf = Minimap._build_terrain(data)
        assert surf.get_at((5, 5))[:3] == _COLOR_ROCK

    def test_lava_tile_is_orange(self):
        size = settings.MAP_SIZE
        data = [[settings.MAP_TILE_EMPTY] * size for _ in range(size)]
        data[7][3] = settings.MAP_TILE_LAVA
        surf = Minimap._build_terrain(data)
        assert surf.get_at((7, 3))[:3] == _COLOR_LAVA

    def test_city_tile_is_background(self):
        # City centers are drawn dynamically, not baked into the terrain surface
        size = settings.MAP_SIZE
        data = [[settings.MAP_TILE_EMPTY] * size for _ in range(size)]
        data[4][4] = settings.MAP_TILE_CITY
        surf = Minimap._build_terrain(data)
        assert surf.get_at((4, 4))[:3] == _COLOR_BG
