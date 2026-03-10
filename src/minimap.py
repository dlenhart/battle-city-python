"""
src/minimap.py — Scrolling mini-map overlay.

Toggled with the M key. Displayed in the bottom-left corner of the screen.

The minimap shows a window of VIEWPORT_TILES × VIEWPORT_TILES tiles centered
on the player. As the player moves, the viewport follows smoothly. The terrain
layer (rock / lava) is pre-rendered once to a 1-pixel-per-tile surface at init;
each frame only the visible crop is scaled to the minimap box.

Color key:
  Rock  → white
  Lava  → orange
  City  → blue dot
  Player→ white dot at the center of the minimap
"""

import pygame
import settings

# ------------------------------------------------------------------
# Layout constants
# ------------------------------------------------------------------
MINIMAP_SIZE   = 160    # on-screen width and height of the minimap box (px)
MINIMAP_MARGIN = 12     # gap from the bottom-left screen edges (px)
MINIMAP_X      = MINIMAP_MARGIN
MINIMAP_Y      = settings.SCREEN_HEIGHT - MINIMAP_SIZE - MINIMAP_MARGIN

# Viewport: how many tiles to show in each dimension.
# "screen × 5" ≈ FIELD_WIDTH * 5 / TILE_SIZE ≈ 65 tiles.
VIEWPORT_TILES = int(settings.FIELD_WIDTH * 5 / settings.TILE_SIZE)

# ------------------------------------------------------------------
# Color palette
# ------------------------------------------------------------------
_COLOR_BG     = (  0,   0,   0)
_COLOR_ROCK   = (210, 210, 210)
_COLOR_LAVA   = (210, 100,  20)
_COLOR_CITY   = ( 80, 160, 220)
_COLOR_PLAYER = (255, 255, 255)
_COLOR_BORDER = ( 80,  80,  80)

_CITY_DOT   = 3   # city marker side length in minimap pixels
_PLAYER_DOT = 3   # player marker side length in minimap pixels

# Scale: minimap pixels per tile (≈ 2.46 for 160 / 65)
_MM_SCALE = MINIMAP_SIZE / VIEWPORT_TILES


class Minimap:
    """Scrolling terrain mini-map that follows the player."""

    def __init__(
        self,
        map_data:  list[list[int]],
        buildings,                   # BuildingManager
    ) -> None:
        self.visible    = False
        self._buildings = buildings.buildings   # list[Building]
        self._terrain   = self._build_terrain(map_data)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def toggle(self) -> None:
        self.visible = not self.visible

    def draw(self, screen: pygame.Surface, player) -> None:
        """Draw the minimap centered on the player (call with no screen clip set)."""
        if not self.visible:
            return

        half = VIEWPORT_TILES // 2

        # Player tile position (integer)
        ptx = int(player.x / settings.TILE_SIZE)
        pty = int(player.y / settings.TILE_SIZE)

        # Viewport top-left in tile / terrain-surface coordinates
        left = ptx - half
        top  = pty - half

        # --- Crop the terrain surface to the viewport ---
        viewport = pygame.Surface((VIEWPORT_TILES, VIEWPORT_TILES))
        viewport.fill(_COLOR_BG)

        src_x = max(0, left)
        src_y = max(0, top)
        src_w = min(settings.MAP_SIZE - src_x,
                    VIEWPORT_TILES - max(0, -left))
        src_h = min(settings.MAP_SIZE - src_y,
                    VIEWPORT_TILES - max(0, -top))

        if src_w > 0 and src_h > 0:
            dst_x = max(0, -left)
            dst_y = max(0, -top)
            viewport.blit(
                self._terrain,
                (dst_x, dst_y),
                pygame.Rect(src_x, src_y, src_w, src_h),
            )

        # --- Scale viewport to the minimap box size ---
        scaled = pygame.transform.scale(viewport, (MINIMAP_SIZE, MINIMAP_SIZE))

        # --- Overlay city dots (only those inside the viewport) ---
        half_dot = _CITY_DOT // 2
        for b in self._buildings:
            rel_x = b.tile_x - left
            rel_y = b.tile_y - top
            if 0 <= rel_x < VIEWPORT_TILES and 0 <= rel_y < VIEWPORT_TILES:
                sx = int(rel_x * _MM_SCALE)
                sy = int(rel_y * _MM_SCALE)
                pygame.draw.rect(
                    scaled, _COLOR_CITY,
                    (sx - half_dot, sy - half_dot, _CITY_DOT, _CITY_DOT),
                )

        # --- Blit the finished minimap to the screen ---
        screen.blit(scaled, (MINIMAP_X, MINIMAP_Y))

        # --- Player dot: always at the center ---
        centre = MINIMAP_SIZE // 2
        half_p = _PLAYER_DOT // 2
        pygame.draw.rect(
            screen, _COLOR_PLAYER,
            (MINIMAP_X + centre - half_p,
             MINIMAP_Y + centre - half_p,
             _PLAYER_DOT, _PLAYER_DOT),
        )

        # --- Border ---
        pygame.draw.rect(
            screen, _COLOR_BORDER,
            (MINIMAP_X - 1, MINIMAP_Y - 1,
             MINIMAP_SIZE + 2, MINIMAP_SIZE + 2),
            1,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _world_to_minimap(world_x: float, world_y: float,
                          left: int, top: int) -> tuple[int, int]:
        """Convert a world pixel position to minimap pixel coordinates."""
        rel_x = world_x / settings.TILE_SIZE - left
        rel_y = world_y / settings.TILE_SIZE - top
        mx = max(0, min(int(rel_x * _MM_SCALE), MINIMAP_SIZE - 1))
        my = max(0, min(int(rel_y * _MM_SCALE), MINIMAP_SIZE - 1))
        return mx, my

    @staticmethod
    def _build_terrain(map_data: list[list[int]]) -> pygame.Surface:
        """
        Pre-render a MAP_SIZE × MAP_SIZE surface with 1 pixel per tile.

        Rock → white, Lava → orange, everything else → black (transparent background).
        Done once at startup; the per-frame cost is only a crop + scale.
        """
        size = settings.MAP_SIZE
        surf = pygame.Surface((size, size))
        surf.fill(_COLOR_BG)

        # PixelArray is faster than repeated set_at calls
        pxa        = pygame.PixelArray(surf)
        rock_px    = surf.map_rgb(_COLOR_ROCK)
        lava_px    = surf.map_rgb(_COLOR_LAVA)

        for tx in range(size):
            for ty in range(size):
                tile = map_data[tx][ty]
                if tile == settings.MAP_TILE_ROCK:
                    pxa[tx][ty] = rock_px
                elif tile == settings.MAP_TILE_LAVA:
                    pxa[tx][ty] = lava_px

        del pxa
        return surf
