"""
src/build_menu.py — Build-menu popup and building-placement mode.

Mirrors client/CDrawing.cpp DrawBuildMenu() + client/CInput.cpp click handling.

Menu layout (bottom → top):
  [Demolish]
  [building index 0  if can_build[0] != 0]
  [building index 1  if can_build[1] != 0]
  ...
  [building index 25 if can_build[25] != 0]

is_placing values:
   0  = idle (no placement in progress)
  -1  = demolish mode
  1-26 = building (1-indexed menu_index + 1, matching C++ IsBuilding)
"""

import pygame
import settings

_ENTRY_H    = 16                  # px per menu row
_MENU_W     = 196                 # popup box width
_BG         = (20, 20, 20)
_BORDER     = (60, 100, 60)
_YELLOW     = (255, 215, 0)       # available building
_GREY       = (80, 80, 80)        # already-built / unavailable
_CASH_COL   = (100, 220, 100)
_RESEARCH_COL = (80, 160, 255)    # research in progress


class BuildMenu:
    """Manages the build popup menu and in-flight building placement."""

    def __init__(self) -> None:
        self.show_menu: bool = False
        self.is_placing: int = 0       # 0=none  -1=demolish  1-26=building

        self._menu_x: int = 0          # left edge of popup
        self._menu_y: int = 0          # bottom of popup (menu grows upward)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def open(self, anchor_x: int, anchor_y: int) -> None:
        """Show the menu with its bottom edge at (anchor_x, anchor_y)."""
        self._menu_x = anchor_x
        self._menu_y = anchor_y
        self.show_menu = True
        self.is_placing = 0

    def close(self) -> None:
        self.show_menu = False

    def cancel_placement(self) -> None:
        self.is_placing = 0

    def handle_click(
        self,
        pos: tuple[int, int],
        can_build: list[int],
    ) -> bool:
        """
        Handle a left-click while the menu is open.
        Closes the menu; sets is_placing if the click hit a valid entry.
        Returns True (event consumed).
        """
        self.show_menu = False
        x, y = pos

        visible = [i for i in range(settings.NUM_BUILD_TYPES) if can_build[i] != 0]
        n_rows  = len(visible) + 1  # +1 for Demolish
        box_top = self._menu_y - n_rows * _ENTRY_H

        # Click outside the popup → just close, no selection
        if not (self._menu_x - 20 <= x <= self._menu_x + _MENU_W
                and box_top <= y <= self._menu_y):
            return True

        # Which row was clicked? (0 = bottom/Demolish)
        row = (self._menu_y - 1 - y) // _ENTRY_H

        if row == 0:
            self.is_placing = -1
            return True

        # row 1 → visible[0], row 2 → visible[1], …
        idx = row - 1
        if 0 <= idx < len(visible):
            menu_index = visible[idx]
            if can_build[menu_index] == 1:        # only allow if actually buildable
                self.is_placing = menu_index + 1  # 1-indexed (C++ IsBuilding)

        return True

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(
        self,
        screen:     pygame.Surface,
        font:       pygame.font.Font,
        can_build:  list[int],
        icon_sheet: pygame.Surface,
        build_state,                   # CityBuildState — for research progress
    ) -> None:
        """Draw the popup menu.  Call with no clip set."""
        if not self.show_menu:
            return

        visible = [i for i in range(settings.NUM_BUILD_TYPES) if can_build[i] != 0]
        n_rows  = len(visible) + 1
        box_h   = n_rows * _ENTRY_H
        box_top = self._menu_y - box_h

        # Background + border
        box_rect = pygame.Rect(self._menu_x - 20, box_top, _MENU_W + 20, box_h)
        pygame.draw.rect(screen, _BG, box_rect)
        pygame.draw.rect(screen, _BORDER, box_rect, 1)

        # Cash display above the popup
        cash_surf = font.render(f"Cash: ${build_state.cash:,}", True, _CASH_COL)
        screen.blit(cash_surf, (self._menu_x - 20, box_top - cash_surf.get_height() - 2))

        # Draw rows bottom → top
        # Row 0 (bottom): Demolish
        draw_y = self._menu_y - _ENTRY_H
        self._draw_icon(screen, icon_sheet, settings.BUILD_ICON_DEMOLISH,
                        self._menu_x - 16, draw_y)
        screen.blit(font.render("Demolish", True, _YELLOW), (self._menu_x, draw_y))

        # Remaining rows: buildings in index order
        for menu_index in visible:
            draw_y -= _ENTRY_H
            state = can_build[menu_index]

            if build_state.is_researching(menu_index):
                # Show research progress bar and blue text
                pct = 1.0 - build_state.research_progress(menu_index)
                bar_rect = pygame.Rect(self._menu_x - 16, draw_y + 1,
                                       int((_MENU_W + 16) * pct), _ENTRY_H - 2)
                pygame.draw.rect(screen, (0, 40, 80), bar_rect)
                color = _RESEARCH_COL
            elif state == 2:
                color = _GREY          # already built
            else:
                color = _YELLOW        # available

            self._draw_icon(screen, icon_sheet,
                            settings.BUILD_BUTTON[menu_index], self._menu_x - 16, draw_y)
            screen.blit(font.render(settings.BUILD_NAMES[menu_index], True, color),
                        (self._menu_x, draw_y))

    def draw_placement_ghost(
        self,
        screen:         pygame.Surface,
        cam_x:          float,
        cam_y:          float,
        field_rect:     pygame.Rect,
        mouse_pos:      tuple[int, int],
        building_sheet: pygame.Surface,
    ) -> None:
        """Draw a semi-transparent building preview snapped to the tile grid."""
        if self.is_placing <= 0:
            return

        mx, my = mouse_pos
        if not field_rect.collidepoint(mx, my):
            return

        ts = settings.TILE_SIZE

        # Snap to tile grid in world space
        world_x = mx - field_rect.x + int(cam_x)
        world_y = my - field_rect.y + int(cam_y)
        snapped_wx = (world_x // ts) * ts
        snapped_wy = (world_y // ts) * ts

        # Convert back to screen
        sx = field_rect.x + snapped_wx - int(cam_x)
        sy = field_rect.y + snapped_wy - int(cam_y)

        btype    = settings.BUILDING_TYPES[self.is_placing - 1]
        row      = btype // 100           # 1=Factory 2=Hospital 3=House 4=Research
        src_rect = pygame.Rect(0, row * 144, 144, 144)

        ghost = building_sheet.subsurface(src_rect).copy()
        ghost.set_alpha(140)
        screen.blit(ghost, (sx, sy))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _draw_icon(
        self,
        screen:     pygame.Surface,
        sheet:      pygame.Surface,
        frame:      int,
        x:          int,
        y:          int,
    ) -> None:
        w = settings.BUILD_ICON_W
        h = settings.BUILD_ICON_H
        screen.blit(sheet, (x, y), pygame.Rect(frame * w, 0, w, h))
