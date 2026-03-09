"""
src/hud.py — Heads-up display rendering.
"""

import pygame
import settings


class HUD:
    """Renders the field border, title, position/heading info, and control hint."""

    def __init__(self, font: pygame.font.Font) -> None:
        self._font = font

    def draw(self, screen: pygame.Surface, player) -> None:
        """
        Draw all HUD elements for the current frame.

        `player` is duck-typed — any object with .tile_position and
        .heading_degrees properties works.
        """
        self._draw_border(screen)
        self._draw_title(screen)
        self._draw_player_info(screen, player)
        self._draw_hint(screen)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _draw_border(self, screen: pygame.Surface) -> None:
        border = pygame.Rect(
            settings.FIELD_X - 3,
            settings.FIELD_Y - 3,
            settings.FIELD_WIDTH  + 6,
            settings.FIELD_HEIGHT + 6,
        )
        pygame.draw.rect(screen, settings.HUD_BORDER, border, 2)

    def _draw_title(self, screen: pygame.Surface) -> None:
        title = self._font.render("BATTLE CITY", True, settings.GREEN_LIGHT)
        screen.blit(title, (settings.FIELD_X, settings.FIELD_Y - 26))

    def _draw_player_info(self, screen: pygame.Surface, player) -> None:
        col, row = player.tile_position
        text = self._font.render(
            f"POS ({col},{row})  HDG {player.heading_degrees:03d}°",
            True,
            settings.GRAY,
        )
        x = settings.FIELD_X + settings.FIELD_WIDTH - text.get_width()
        screen.blit(text, (x, settings.FIELD_Y - 26))

    def _draw_hint(self, screen: pygame.Surface) -> None:
        hint = self._font.render(
            "UP/DN: Move    LT/RT: Turn    ESC: Quit",
            True,
            settings.GRAY,
        )
        screen.blit(hint, (settings.FIELD_X, settings.FIELD_Y + settings.FIELD_HEIGHT + 10))
