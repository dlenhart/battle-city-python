"""Tests for src/camera.py — Camera world-to-screen coordinate conversion."""

import pytest
import settings
from src.camera import Camera


class TestCameraFollow:
    def test_initial_position_is_zero(self):
        cam = Camera()
        assert cam.x == 0.0
        assert cam.y == 0.0

    def test_centers_viewport_on_target(self):
        cam = Camera()
        # Put the target dead-center of the map.
        world_x = settings.MAP_PIXEL_SIZE / 2
        world_y = settings.MAP_PIXEL_SIZE / 2
        cam.follow(world_x, world_y)
        # Camera origin should be half the field size behind the tank center.
        expected_x = world_x - settings.FIELD_WIDTH  / 2 + settings.TANK_FRAME_W / 2
        expected_y = world_y - settings.FIELD_HEIGHT / 2 + settings.TANK_FRAME_H / 2
        assert cam.x == pytest.approx(expected_x)
        assert cam.y == pytest.approx(expected_y)

    def test_clamps_to_left_top_edge(self):
        cam = Camera()
        cam.follow(0.0, 0.0)
        assert cam.x == 0.0
        assert cam.y == 0.0

    def test_clamps_to_right_bottom_edge(self):
        cam = Camera()
        cam.follow(float(settings.MAP_PIXEL_SIZE), float(settings.MAP_PIXEL_SIZE))
        assert cam.x == settings.MAP_PIXEL_SIZE - settings.FIELD_WIDTH
        assert cam.y == settings.MAP_PIXEL_SIZE - settings.FIELD_HEIGHT

    def test_x_and_y_clamped_independently(self):
        cam = Camera()
        # X near right edge, Y near top.
        cam.follow(float(settings.MAP_PIXEL_SIZE), 0.0)
        assert cam.x == settings.MAP_PIXEL_SIZE - settings.FIELD_WIDTH
        assert cam.y == 0.0


class TestCameraToScreen:
    def test_world_origin_at_camera_origin_maps_to_field_origin(self):
        cam = Camera()
        cam.x = 0.0
        cam.y = 0.0
        sx, sy = cam.to_screen(0.0, 0.0)
        assert sx == settings.FIELD_X
        assert sy == settings.FIELD_Y

    def test_offset_matches_field_plus_delta(self):
        cam = Camera()
        cam.x = 100.0
        cam.y = 200.0
        sx, sy = cam.to_screen(150.0, 250.0)
        assert sx == settings.FIELD_X + 50
        assert sy == settings.FIELD_Y + 50

    def test_returns_integers(self):
        cam = Camera()
        cam.x = 0.7
        cam.y = 0.3
        sx, sy = cam.to_screen(1.9, 1.1)
        assert isinstance(sx, int)
        assert isinstance(sy, int)

    def test_fractional_world_coords_truncate(self):
        cam = Camera()
        cam.x = 0.0
        cam.y = 0.0
        # int(1.9) == 1, not 2
        sx, sy = cam.to_screen(1.9, 2.9)
        assert sx == settings.FIELD_X + 1
        assert sy == settings.FIELD_Y + 2

    def test_follow_then_to_screen_is_consistent(self):
        """Target should map to the center of the viewport after follow()."""
        cam = Camera()
        world_x = 5000.0
        world_y = 6000.0
        cam.follow(world_x, world_y)
        sx, sy = cam.to_screen(world_x, world_y)
        # Tank top-left should appear at FIELD center minus half a tank width
        expected_sx = settings.FIELD_X + settings.FIELD_WIDTH  // 2 - settings.TANK_FRAME_W // 2
        expected_sy = settings.FIELD_Y + settings.FIELD_HEIGHT // 2 - settings.TANK_FRAME_H // 2
        assert sx == expected_sx
        assert sy == expected_sy
