"""Tests for src/player.py — Player movement, turning, collision, and firing."""

import math
import pytest
import settings
from src.player import Player, FIRE_COOLDOWN


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def make_player(x=500.0, y=500.0, direction=0):
    return Player(x, y, direction)


def solid_everywhere(tx, ty):
    """Tile callback that returns solid rock for every tile."""
    return settings.MAP_TILE_ROCK


def empty_everywhere(tx, ty):
    """Tile callback that returns empty for every tile."""
    return settings.MAP_TILE_EMPTY


# ------------------------------------------------------------------
# Initial state
# ------------------------------------------------------------------

class TestPlayerInit:
    def test_position_stored(self):
        p = make_player(100.0, 200.0, direction=4)
        assert p.x == 100.0
        assert p.y == 200.0

    def test_direction_stored(self):
        p = make_player(direction=8)
        assert p.direction == 8

    def test_default_not_moving(self):
        p = make_player()
        assert p.is_moving  == 0
        assert p.is_turning == 0


# ------------------------------------------------------------------
# Derived properties
# ------------------------------------------------------------------

class TestPlayerProperties:
    @pytest.mark.parametrize("direction, expected_col", [
        (0,  0),   # North
        (1,  0),   # North (same col as direction 0)
        (2,  1),
        (8,  4),   # West
        (16, 8),   # South
        (24, 12),  # East
        (31, 15),
    ])
    def test_sprite_col(self, direction, expected_col):
        p = make_player(direction=direction)
        assert p.sprite_col == expected_col

    def test_tile_position(self):
        ts = settings.TILE_SIZE
        p  = make_player(x=float(ts * 3), y=float(ts * 7))
        assert p.tile_position == (3, 7)

    def test_tile_position_fractional(self):
        ts = settings.TILE_SIZE
        p  = make_player(x=float(ts * 3 + ts // 2), y=float(ts * 7 + 5))
        assert p.tile_position == (3, 7)

    @pytest.mark.parametrize("direction, expected_deg", [
        (0,  0),
        (8,  90),   # 8 * (360/32) = 90°
        (16, 180),
        (24, 270),
    ])
    def test_heading_degrees(self, direction, expected_deg):
        p = make_player(direction=direction)
        assert p.heading_degrees == expected_deg


# ------------------------------------------------------------------
# Turning
# ------------------------------------------------------------------

class TestPlayerTurning:
    def test_turn_right_increments_direction(self):
        p = make_player(direction=0)
        p.is_turning = 1
        p._update_turning(settings.TURN_INTERVAL)
        assert p.direction == 1

    def test_turn_left_decrements_direction(self):
        p = make_player(direction=5)
        p.is_turning = -1
        p._update_turning(settings.TURN_INTERVAL)
        assert p.direction == 4

    def test_direction_wraps_at_max(self):
        p = make_player(direction=settings.NUM_DIRECTIONS - 1)
        p.is_turning = 1
        p._update_turning(settings.TURN_INTERVAL)
        assert p.direction == 0

    def test_direction_wraps_at_zero(self):
        p = make_player(direction=0)
        p.is_turning = -1
        p._update_turning(settings.TURN_INTERVAL)
        assert p.direction == settings.NUM_DIRECTIONS - 1

    def test_no_turn_when_is_turning_zero(self):
        p = make_player(direction=5)
        p.is_turning = 0
        p._update_turning(settings.TURN_INTERVAL * 10)
        assert p.direction == 5

    def test_turn_timer_resets_when_not_turning(self):
        p = make_player(direction=0)
        p.is_turning = 1
        p._update_turning(settings.TURN_INTERVAL / 2)
        p.is_turning = 0
        p._update_turning(0.0)
        assert p._turn_timer == 0.0

    def test_multiple_steps_in_one_large_dt(self):
        p = make_player(direction=0)
        p.is_turning = 1
        p._update_turning(settings.TURN_INTERVAL * 3)
        assert p.direction == 3


# ------------------------------------------------------------------
# Movement (no collision)
# ------------------------------------------------------------------

class TestPlayerMovement:
    def test_moves_north(self):
        p = make_player(direction=0)
        p.is_moving = 1
        old_y = p.y
        p._update_movement(0.1, get_tile=empty_everywhere)
        assert p.y < old_y        # North = decreasing Y
        assert p.x == pytest.approx(500.0)

    def test_moves_south(self):
        p = make_player(direction=16)
        p.is_moving = 1
        old_y = p.y
        p._update_movement(0.1, get_tile=empty_everywhere)
        assert p.y > old_y

    def test_moves_east(self):
        # direction 8: angle = π/2, sin(π/2) = +1 → positive x = East
        p = make_player(direction=8)
        p.is_moving = 1
        old_x = p.x
        p._update_movement(0.1, get_tile=empty_everywhere)
        assert p.x > old_x
        assert p.y == pytest.approx(500.0)

    def test_moves_west(self):
        # direction 24: angle = 3π/2, sin(3π/2) = -1 → negative x = West
        p = make_player(direction=24)
        p.is_moving = 1
        old_x = p.x
        p._update_movement(0.1, get_tile=empty_everywhere)
        assert p.x < old_x

    def test_backward_moves_opposite_direction(self):
        p = make_player(direction=0)   # facing North
        p.is_moving = -1
        old_y = p.y
        p._update_movement(0.1, get_tile=empty_everywhere)
        assert p.y > old_y             # backward = South = increasing Y

    def test_speed_proportional_to_dt(self):
        p1 = make_player(direction=0)
        p1.is_moving = 1
        p1._update_movement(0.1, get_tile=empty_everywhere)

        p2 = make_player(direction=0)
        p2.is_moving = 1
        p2._update_movement(0.2, get_tile=empty_everywhere)

        delta1 = 500.0 - p1.y
        delta2 = 500.0 - p2.y
        assert delta2 == pytest.approx(delta1 * 2, rel=1e-4)

    def test_clamps_to_map_left_edge(self):
        p = make_player(x=0.0, y=500.0, direction=24)  # direction 24 = West (−x)
        p.is_moving = 1
        p._update_movement(1.0, get_tile=empty_everywhere)
        assert p.x == 0.0

    def test_clamps_to_map_top_edge(self):
        p = make_player(x=500.0, y=0.0, direction=0)  # facing North
        p.is_moving = 1
        p._update_movement(1.0, get_tile=empty_everywhere)
        assert p.y == 0.0

    def test_clamps_to_map_right_edge(self):
        max_x = float(settings.MAP_PIXEL_SIZE - settings.TANK_FRAME_W)
        p = make_player(x=max_x, y=500.0, direction=8)  # direction 8 = East (+x)
        p.is_moving = 1
        p._update_movement(1.0, get_tile=empty_everywhere)
        assert p.x == max_x

    def test_clamps_to_map_bottom_edge(self):
        max_y = float(settings.MAP_PIXEL_SIZE - settings.TANK_FRAME_H)
        p = make_player(x=500.0, y=max_y, direction=16)  # facing South
        p.is_moving = 1
        p._update_movement(1.0, get_tile=empty_everywhere)
        assert p.y == max_y

    def test_no_movement_when_stopped(self):
        p = make_player(direction=0)
        p.is_moving = 0
        p._update_movement(1.0, get_tile=empty_everywhere)
        assert p.x == pytest.approx(500.0)
        assert p.y == pytest.approx(500.0)


# ------------------------------------------------------------------
# Collision (_solid_at)
# ------------------------------------------------------------------

class TestSolidAt:
    def test_solid_when_all_corners_on_rock(self):
        assert Player._solid_at(0.0, 0.0, solid_everywhere) is True

    def test_not_solid_on_empty_map(self):
        assert Player._solid_at(100.0, 100.0, empty_everywhere) is False

    def test_solid_detected_by_any_corner(self):
        ts = settings.TILE_SIZE
        # Put the tank mostly on empty, but one corner clips into a rock tile.
        def one_rock(tx, ty):
            return settings.MAP_TILE_ROCK if (tx == 1 and ty == 0) else settings.MAP_TILE_EMPTY

        # Tank at (0, 0): corners at (0,0) and (ts-1, ts-1).
        # Corner (ts-1, 0) lands on tile x=0 still; (ts, 0) would land on tile x=1.
        # Place tank such that right edge crosses into tile x=1.
        x = float(ts - 1)  # right corner pixel is at ts*2 - 2, tile = 1
        assert Player._solid_at(x, 0.0, one_rock) is True

    def test_lava_is_solid(self):
        def lava_everywhere(tx, ty):
            return settings.MAP_TILE_LAVA
        assert Player._solid_at(100.0, 100.0, lava_everywhere) is True

    def test_city_tile_not_treated_as_solid(self):
        def city_everywhere(tx, ty):
            return settings.MAP_TILE_CITY
        # City (type 3) is NOT in the solid tuple — building collision is handled
        # by the composite tile check in game.py, not here.
        assert Player._solid_at(100.0, 100.0, city_everywhere) is False

    def test_movement_blocked_by_solid_tile(self):
        p = make_player(direction=0, x=500.0, y=500.0)
        p.is_moving = 1
        original_y = p.y
        p._update_movement(0.1, get_tile=solid_everywhere)
        assert p.y == original_y


# ------------------------------------------------------------------
# Firing
# ------------------------------------------------------------------

class TestPlayerFiring:
    def test_no_shot_when_fire_not_requested(self):
        p = make_player()
        p._fire_requested = False
        p._fire_cooldown  = 0.0
        assert p.try_fire() is None

    def test_no_shot_during_cooldown(self):
        p = make_player()
        p._fire_requested = True
        p._fire_cooldown  = 0.5
        assert p.try_fire() is None

    def test_shot_when_ready(self):
        p = make_player()
        p._fire_requested = True
        p._fire_cooldown  = 0.0
        result = p.try_fire()
        assert result is not None

    def test_shot_returns_spawn_x_y_direction(self):
        p = make_player(x=100.0, y=100.0, direction=8)
        p._fire_requested = True
        p._fire_cooldown  = 0.0
        spawn_x, spawn_y, direction = p.try_fire()
        assert isinstance(spawn_x, float)
        assert isinstance(spawn_y, float)
        assert direction == 8

    def test_shot_spawn_centered_on_tank(self):
        from src.bullet import BULLET_SIZE
        p = make_player(x=0.0, y=0.0, direction=0)
        p._fire_requested = True
        p._fire_cooldown  = 0.0
        spawn_x, spawn_y, _ = p.try_fire()
        expected_x = settings.TANK_FRAME_W / 2 - BULLET_SIZE / 2
        expected_y = settings.TANK_FRAME_H / 2 - BULLET_SIZE / 2
        assert spawn_x == pytest.approx(expected_x)
        assert spawn_y == pytest.approx(expected_y)

    def test_cooldown_set_after_firing(self):
        p = make_player()
        p._fire_requested = True
        p._fire_cooldown  = 0.0
        p.try_fire()
        assert p._fire_cooldown == pytest.approx(FIRE_COOLDOWN)

    def test_cannot_fire_again_immediately(self):
        p = make_player()
        p._fire_requested = True
        p._fire_cooldown  = 0.0
        p.try_fire()
        assert p.try_fire() is None

    def test_can_fire_after_cooldown_expires(self):
        p = make_player()
        p._fire_requested = True
        p._fire_cooldown  = 0.0
        p.try_fire()
        p.update(FIRE_COOLDOWN + 0.01)   # advance past cooldown (no tile check)
        p._fire_requested = True
        assert p.try_fire() is not None


# ------------------------------------------------------------------
# Health and city spawn
# ------------------------------------------------------------------

class TestPlayerHealthAndCity:
    def test_hp_initialises_to_max_health(self):
        p = Player(0.0, 0.0, direction=0)
        assert p.hp == settings.MAX_HEALTH

    def test_city_coords_default_to_zero(self):
        p = Player(0.0, 0.0, direction=0)
        assert p.city_x == 0.0 and p.city_y == 0.0

    def test_city_coords_stored(self):
        p = Player(0.0, 0.0, direction=0, city_x=500.0, city_y=600.0)
        assert p.city_x == 500.0 and p.city_y == 600.0

    def test_hp_mutable(self):
        p = Player(0.0, 0.0, direction=0)
        p.hp = 20
        assert p.hp == 20


# ------------------------------------------------------------------
# Item state (cloak timer, bullet type)
# ------------------------------------------------------------------

class TestPlayerItemState:
    def _make_player(self):
        return Player(x=0.0, y=0.0)

    def test_player_starts_uncloaked(self):
        p = self._make_player()
        assert p.is_cloaked is False
        assert p._cloak_timer == 0.0
        assert p.bullet_type == 0

    def test_cloak_expires_after_timer(self):
        p = self._make_player()
        p.is_cloaked = True
        p._cloak_timer = settings.TIMER_CLOAK
        p.update(settings.TIMER_CLOAK + 0.1)
        assert p.is_cloaked is False

    def test_cloak_still_active_before_expiry(self):
        p = self._make_player()
        p.is_cloaked = True
        p._cloak_timer = settings.TIMER_CLOAK
        p.update(settings.TIMER_CLOAK - 0.1)
        assert p.is_cloaked is True
