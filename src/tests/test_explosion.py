"""Tests for src/explosion.py — Explosion animation and lifecycle."""

import pytest
from src.explosion import Explosion, EXPLOSION_SIZE, NUM_FRAMES, FRAME_INTERVAL


def make_explosion(cx=500.0, cy=500.0):
    return Explosion(cx, cy)


class TestExplosionInit:
    def test_active_on_creation(self):
        e = make_explosion()
        assert e.active is True

    def test_position_centered_on_impact(self):
        e = make_explosion(cx=100.0, cy=200.0)
        assert e.x == pytest.approx(100.0 - EXPLOSION_SIZE / 2)
        assert e.y == pytest.approx(200.0 - EXPLOSION_SIZE / 2)

    def test_starts_on_first_frame(self):
        e = make_explosion()
        src_x, src_y, w, h = e.sprite_rect
        assert src_x == 0


class TestExplosionAnimation:
    def test_frame_advances_after_interval(self):
        e = make_explosion()
        e.update(FRAME_INTERVAL)
        src_x, _, _, _ = e.sprite_rect
        assert src_x == EXPLOSION_SIZE

    def test_frame_does_not_advance_before_interval(self):
        e = make_explosion()
        e.update(FRAME_INTERVAL * 0.9)
        src_x, _, _, _ = e.sprite_rect
        assert src_x == 0

    def test_deactivates_after_all_frames(self):
        e = make_explosion()
        for _ in range(NUM_FRAMES):
            e.update(FRAME_INTERVAL)
        assert e.active is False

    def test_still_active_on_last_frame(self):
        e = make_explosion()
        for _ in range(NUM_FRAMES - 1):
            e.update(FRAME_INTERVAL)
        assert e.active is True

    def test_sprite_rect_size_constant(self):
        e = make_explosion()
        _, _, w, h = e.sprite_rect
        assert w == EXPLOSION_SIZE
        assert h == EXPLOSION_SIZE

    def test_sprite_rect_y_always_zero(self):
        # Single row spritesheet — src_y is always 0
        e = make_explosion()
        for _ in range(NUM_FRAMES - 1):
            _, src_y, _, _ = e.sprite_rect
            assert src_y == 0
            e.update(FRAME_INTERVAL)


class TestBulletHitsTerrain:
    def test_bullet_hits_rock(self):
        from src.bullet import Bullet
        import settings
        b = Bullet(500.0, 500.0, direction=0)

        def rock_everywhere(tx, ty):
            return settings.MAP_TILE_ROCK

        assert b.hits_terrain(rock_everywhere) is True

    def test_bullet_passes_through_lava(self):
        from src.bullet import Bullet
        import settings
        b = Bullet(500.0, 500.0, direction=0)

        def lava_everywhere(tx, ty):
            return settings.MAP_TILE_LAVA

        assert b.hits_terrain(lava_everywhere) is False

    def test_bullet_passes_through_empty(self):
        from src.bullet import Bullet
        import settings
        b = Bullet(500.0, 500.0, direction=0)

        def empty_everywhere(tx, ty):
            return settings.MAP_TILE_EMPTY

        assert b.hits_terrain(empty_everywhere) is False

    def test_bullet_hits_blocked_building_tile(self):
        from src.bullet import Bullet
        import settings
        b = Bullet(500.0, 500.0, direction=0)

        # Simulate the composite tile_check returning rock for a blocked building tile
        def blocked_building(tx, ty):
            return settings.MAP_TILE_ROCK

        assert b.hits_terrain(blocked_building) is True
