"""Tests for src/bullet.py — Bullet movement, animation, bounds, and sprite rect."""

import math
import pytest
import settings
from src.bullet import Bullet, BULLET_SIZE, BULLET_SPEED, ANIM_INTERVAL, NUM_ANIM_FRAMES


def make_bullet(x=500.0, y=500.0, direction=0, bullet_type=0):
    return Bullet(x, y, direction, bullet_type)


# ------------------------------------------------------------------
# Initial state
# ------------------------------------------------------------------

class TestBulletInit:
    def test_position_stored(self):
        b = make_bullet(x=10.0, y=20.0)
        assert b.x == 10.0
        assert b.y == 20.0

    def test_direction_stored(self):
        b = make_bullet(direction=16)
        assert b.direction == 16

    def test_active_on_creation(self):
        b = make_bullet()
        assert b.active is True

    def test_default_bullet_type_zero(self):
        b = make_bullet()
        assert b.bullet_type == 0


# ------------------------------------------------------------------
# Movement
# ------------------------------------------------------------------

class TestBulletMovement:
    def test_moves_north(self):
        b = make_bullet(direction=0)
        old_y = b.y
        b._move(0.1)
        assert b.y < old_y
        assert b.x == pytest.approx(500.0)

    def test_moves_south(self):
        b = make_bullet(direction=16)
        old_y = b.y
        b._move(0.1)
        assert b.y > old_y

    def test_moves_east(self):
        # direction 8: angle = π/2, sin(π/2) = +1 → East
        b = make_bullet(direction=8)
        old_x = b.x
        b._move(0.1)
        assert b.x > old_x
        assert b.y == pytest.approx(500.0)

    def test_moves_west(self):
        # direction 24: angle = 3π/2, sin(3π/2) = -1 → West
        b = make_bullet(direction=24)
        old_x = b.x
        b._move(0.1)
        assert b.x < old_x

    def test_speed_matches_constant(self):
        b = make_bullet(direction=0)
        dt = 0.1
        b._move(dt)
        expected_dist = BULLET_SPEED * dt
        assert (500.0 - b.y) == pytest.approx(expected_dist, rel=1e-4)

    def test_diagonal_speed_correct(self):
        # direction=4 is 45° (NE quadrant), sin(45°)*speed = cos(45°)*speed
        b = make_bullet(direction=4)
        dt = 0.1
        b._move(dt)
        angle = 4 * (2 * math.pi / settings.NUM_DIRECTIONS)
        assert (b.x - 500.0) == pytest.approx(math.sin(angle) * BULLET_SPEED * dt, rel=1e-4)
        assert (500.0 - b.y) == pytest.approx(math.cos(angle) * BULLET_SPEED * dt, rel=1e-4)


# ------------------------------------------------------------------
# Animation
# ------------------------------------------------------------------

class TestBulletAnimation:
    def test_animation_starts_at_zero(self):
        b = make_bullet()
        assert b._animation == 0

    def test_animation_advances_after_interval(self):
        b = make_bullet()
        b._animate(ANIM_INTERVAL)
        assert b._animation == 1

    def test_animation_wraps_after_max_frames(self):
        # _animate uses 'if' not 'while': one step per call.
        # Cycle through all frames one call at a time.
        b = make_bullet()
        for _ in range(NUM_ANIM_FRAMES):
            b._animate(ANIM_INTERVAL)
        assert b._animation == 0

    def test_animation_does_not_advance_before_interval(self):
        b = make_bullet()
        b._animate(ANIM_INTERVAL * 0.9)
        assert b._animation == 0

    def test_large_dt_still_only_one_step(self):
        # _animate uses 'if', so a single call with 2.5x the interval
        # only advances one frame (timer keeps the remainder).
        b = make_bullet()
        b._animate(ANIM_INTERVAL * 2.5)
        assert b._animation == 1


# ------------------------------------------------------------------
# Bounds checking
# ------------------------------------------------------------------

class TestBulletBounds:
    def test_active_within_map(self):
        b = make_bullet(x=500.0, y=500.0)
        b._check_bounds()
        assert b.active is True

    def test_inactive_when_off_left(self):
        b = make_bullet(x=-BULLET_SIZE - 1.0, y=500.0)
        b._check_bounds()
        assert b.active is False

    def test_inactive_when_off_right(self):
        b = make_bullet(x=float(settings.MAP_PIXEL_SIZE) + 1.0, y=500.0)
        b._check_bounds()
        assert b.active is False

    def test_inactive_when_off_top(self):
        b = make_bullet(x=500.0, y=-BULLET_SIZE - 1.0)
        b._check_bounds()
        assert b.active is False

    def test_inactive_when_off_bottom(self):
        b = make_bullet(x=500.0, y=float(settings.MAP_PIXEL_SIZE) + 1.0)
        b._check_bounds()
        assert b.active is False

    def test_still_active_at_map_edge(self):
        # Exactly at the map boundary — still partially inside
        b = make_bullet(x=0.0, y=0.0)
        b._check_bounds()
        assert b.active is True

    def test_update_deactivates_out_of_bounds(self):
        b = make_bullet(x=-100.0, y=-100.0)
        b.update(0.0)
        assert b.active is False


# ------------------------------------------------------------------
# Sprite rect
# ------------------------------------------------------------------

class TestBulletSpriteRect:
    @pytest.mark.parametrize("bullet_type", [0, 1, 2, 3])
    def test_sprite_rect_y_per_type(self, bullet_type):
        b = make_bullet(bullet_type=bullet_type)
        _, src_y, _, _ = b.sprite_rect
        assert src_y == bullet_type * BULLET_SIZE

    def test_sprite_rect_size(self):
        b = make_bullet()
        _, _, w, h = b.sprite_rect
        assert w == BULLET_SIZE
        assert h == BULLET_SIZE

    def test_sprite_rect_x_advances_with_animation(self):
        b = make_bullet()
        b._animation = 2
        src_x, _, _, _ = b.sprite_rect
        assert src_x == 2 * BULLET_SIZE
