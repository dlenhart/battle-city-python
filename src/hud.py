"""
src/hud.py — Heads-up display rendering.

Also exports arrow_frame() — a pure math helper that was previously a
free function stranded in game.py.
"""

import math
import pygame
import settings


def arrow_frame(dif_x: float, dif_y: float) -> int:
    """Return the imgArrows.bmp frame index (0-7) for a home-city direction vector.

    Frame mapping (C++ convention): 0=East, 1=NE, 2=North, 3=NW,
                                    4=West, 5=SW, 6=South, 7=SE.
    dif_x / dif_y is the vector from the player to the home city.
    """
    angle_deg = math.degrees(math.atan2(dif_x, -dif_y)) % 360.0
    n = int((angle_deg + 22.5) / 45.0) % 8   # 0=North clockwise
    return (2 - n) % 8                         # remap to C++ frame order


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


def draw_inventory(
    screen: pygame.Surface,
    inventory,
    items_sheet: pygame.Surface,
    selection_sheet: pygame.Surface,
    font: pygame.font.Font,
) -> None:
    """Draw the 3×4 inventory grid on the right panel.

    Layout mirrors C++ CDrawing::DrawInventory():
      - 12 item types in a 4-row × 3-col grid
      - Each slot: 32×32 icon from imgItems.bmp at src_x=type*32, src_y=0
      - Selected slot: imgInventorySelection.bmp drawn underneath icon
      - Count > 1: yellow number at slot_x+22, slot_y+12

    `inventory` is duck-typed — must expose .counts (list[int]) and
    .selected_type (int).
    """
    yellow = (255, 215, 0)

    for row, row_y in enumerate(settings.INV_ROW_OFFSETS):
        for col, col_x in enumerate(settings.INV_COL_OFFSETS):
            item_type = row * 3 + col
            count = inventory.counts[item_type]
            if count <= 0:
                continue

            slot_x = settings.PANEL_X + col_x
            slot_y = settings.PANEL_Y + row_y

            # Selection highlight drawn under icon
            if item_type == inventory.selected_type:
                screen.blit(selection_sheet, (slot_x, slot_y),
                            pygame.Rect(0, 0, settings.INV_ICON_SIZE, settings.INV_ICON_SIZE))

            # Item icon: small 32×32 row (src_y=0)
            src_x = item_type * settings.INV_ICON_SIZE
            screen.blit(items_sheet, (slot_x, slot_y),
                        pygame.Rect(src_x, 0, settings.INV_ICON_SIZE, settings.INV_ICON_SIZE))

            # Count label if more than one
            if count > 1:
                label = font.render(str(count), True, yellow)
                screen.blit(label, (slot_x + 22, slot_y + 12))
