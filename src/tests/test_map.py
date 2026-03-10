"""Tests for src/map.py — GameMap tile queries and tile connectivity."""

import pytest
import pygame
import settings
from src.map import GameMap


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _empty_surface():
    """Return a minimal opaque surface to pass as a tile sheet."""
    s = pygame.Surface((768, 48))
    s.fill((255, 255, 255))
    return s


def make_map(data: list[list[int]]) -> GameMap:
    return GameMap(data, _empty_surface(), _empty_surface())


def flat_map(tile_type: int) -> list[list[int]]:
    """Return a MAP_SIZE×MAP_SIZE map filled with a single tile type."""
    size = settings.MAP_SIZE
    return [[tile_type] * size for _ in range(size)]


def sparse_map(**coords) -> list[list[int]]:
    """
    Build an empty map with specific tiles set.
    kwargs: tile_x_tile_y=tile_type, e.g. t5_7=settings.MAP_TILE_ROCK
    Or pass a dict via the helper below.
    """
    size = settings.MAP_SIZE
    data = [[settings.MAP_TILE_EMPTY] * size for _ in range(size)]
    return data


def place_tile(data, tx, ty, tile_type):
    data[tx][ty] = tile_type
    return data


# ------------------------------------------------------------------
# get_tile
# ------------------------------------------------------------------

class TestGetTile:
    def test_returns_empty_for_empty_map(self):
        data = flat_map(settings.MAP_TILE_EMPTY)
        gm   = make_map(data)
        assert gm.get_tile(10, 10) == settings.MAP_TILE_EMPTY

    def test_returns_rock_for_rock_tile(self):
        size = settings.MAP_SIZE
        data = [[settings.MAP_TILE_EMPTY] * size for _ in range(size)]
        data[5][7] = settings.MAP_TILE_ROCK
        gm = make_map(data)
        assert gm.get_tile(5, 7) == settings.MAP_TILE_ROCK

    def test_returns_lava_for_lava_tile(self):
        size = settings.MAP_SIZE
        data = [[settings.MAP_TILE_EMPTY] * size for _ in range(size)]
        data[3][4] = settings.MAP_TILE_LAVA
        gm = make_map(data)
        assert gm.get_tile(3, 4) == settings.MAP_TILE_LAVA

    def test_out_of_bounds_negative_returns_rock(self):
        data = flat_map(settings.MAP_TILE_EMPTY)
        gm   = make_map(data)
        assert gm.get_tile(-1, 0)  == settings.MAP_TILE_ROCK
        assert gm.get_tile(0,  -1) == settings.MAP_TILE_ROCK

    def test_out_of_bounds_positive_returns_rock(self):
        data = flat_map(settings.MAP_TILE_EMPTY)
        gm   = make_map(data)
        assert gm.get_tile(settings.MAP_SIZE, 0)     == settings.MAP_TILE_ROCK
        assert gm.get_tile(0,     settings.MAP_SIZE) == settings.MAP_TILE_ROCK

    def test_last_valid_tile_not_out_of_bounds(self):
        last = settings.MAP_SIZE - 1
        size = settings.MAP_SIZE
        data = [[settings.MAP_TILE_EMPTY] * size for _ in range(size)]
        data[last][last] = settings.MAP_TILE_LAVA
        gm = make_map(data)
        assert gm.get_tile(last, last) == settings.MAP_TILE_LAVA


# ------------------------------------------------------------------
# _calculate_tiles — connectivity / spritesheet offsets
# ------------------------------------------------------------------

class TestCalculateTiles:
    """
    Tile connectivity: an isolated single tile is surrounded by different
    tiles on all four sides → all four bits set → index = 15.
    Spritesheet X = index * TILE_SIZE.
    """

    def _isolated_tile_offset(self, tile_type: int) -> int:
        size = settings.MAP_SIZE
        data = [[settings.MAP_TILE_EMPTY] * size for _ in range(size)]
        # Place a single solid tile at (5, 5) surrounded by empty
        data[5][5] = tile_type
        gm = make_map(data)
        return gm._tiles[5][5]

    def test_isolated_rock_has_all_edges(self):
        offset = self._isolated_tile_offset(settings.MAP_TILE_ROCK)
        assert offset == 15 * settings.TILE_SIZE

    def test_isolated_lava_has_all_edges(self):
        offset = self._isolated_tile_offset(settings.MAP_TILE_LAVA)
        assert offset == 15 * settings.TILE_SIZE

    def test_empty_tile_has_zero_offset(self):
        data = flat_map(settings.MAP_TILE_EMPTY)
        gm   = make_map(data)
        assert gm._tiles[5][5] == 0

    def test_full_rock_map_centre_has_no_edges(self):
        # A tile surrounded by identical tiles has no boundary → index 0
        data = flat_map(settings.MAP_TILE_ROCK)
        gm   = make_map(data)
        assert gm._tiles[256][256] == 0

    def test_horizontal_strip_has_left_and_right_edges_only(self):
        """A rock tile with rock neighbours above/below but empty left/right."""
        size = settings.MAP_SIZE
        data = [[settings.MAP_TILE_EMPTY] * size for _ in range(size)]
        # Fill a vertical strip at x=5 with rock
        for y in range(size):
            data[5][y] = settings.MAP_TILE_ROCK
        gm = make_map(data)
        # Centre tile (5, 256): neighbours left=empty, right=empty, up=rock, down=rock
        # west=1 (left edge), east=1 (right edge), north=0, south=0 → index = 1+2 = 3
        assert gm._tiles[5][256] == 3 * settings.TILE_SIZE

    def test_top_edge_rock_has_top_edge_bit(self):
        size = settings.MAP_SIZE
        data = [[settings.MAP_TILE_EMPTY] * size for _ in range(size)]
        # Single rock at the top row (y=0): no north neighbour → north bit set
        data[5][0] = settings.MAP_TILE_ROCK
        gm = make_map(data)
        # All four edges different (isolated + top of map) → bit 3 (top) = set
        offset = gm._tiles[5][0]
        assert (offset // settings.TILE_SIZE) & 0b1000  # bit 3 = top edge

    def test_tile_offset_is_multiple_of_tile_size(self):
        size = settings.MAP_SIZE
        data = [[settings.MAP_TILE_EMPTY] * size for _ in range(size)]
        data[10][10] = settings.MAP_TILE_ROCK
        gm = make_map(data)
        assert gm._tiles[10][10] % settings.TILE_SIZE == 0

    def test_lava_and_rock_are_treated_as_different_types(self):
        """A rock tile next to a lava tile has an edge between them."""
        size = settings.MAP_SIZE
        data = [[settings.MAP_TILE_EMPTY] * size for _ in range(size)]
        data[10][10] = settings.MAP_TILE_ROCK
        data[11][10] = settings.MAP_TILE_LAVA  # east neighbour is lava
        gm = make_map(data)
        # east neighbour differs → east bit set on the rock tile
        idx = gm._tiles[10][10] // settings.TILE_SIZE
        assert idx & 0b0010  # bit 1 = right/east edge
