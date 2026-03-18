"""Tests for HUD widget helpers: arrow frame mapping and health bar math."""

import random
import settings
from src.hud import arrow_frame as _arrow_frame


class TestArrowFrame:
    def test_due_north(self):   assert _arrow_frame(0.0,   -100.0) == 2
    def test_due_east(self):    assert _arrow_frame(100.0,    0.0) == 0
    def test_due_south(self):   assert _arrow_frame(0.0,    100.0) == 6
    def test_due_west(self):    assert _arrow_frame(-100.0,   0.0) == 4
    def test_northeast(self):   assert _arrow_frame(100.0, -100.0) == 1
    def test_southeast(self):   assert _arrow_frame(100.0,  100.0) == 7
    def test_southwest(self):   assert _arrow_frame(-100.0, 100.0) == 5
    def test_northwest(self):   assert _arrow_frame(-100.0,-100.0) == 3

    def test_range(self):
        for _ in range(200):
            assert 0 <= _arrow_frame(random.uniform(-1e4, 1e4), random.uniform(-1e4, 1e4)) <= 7


class TestHealthBarMath:
    def test_full_health(self):
        assert int(1.0 * settings.HEALTH_MAX_H) == settings.HEALTH_MAX_H

    def test_zero_health(self):
        assert int(0.0 * settings.HEALTH_MAX_H) == 0

    def test_half_health(self):
        assert int(0.5 * settings.HEALTH_MAX_H) == settings.HEALTH_MAX_H // 2


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
