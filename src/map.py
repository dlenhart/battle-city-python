"""
src/map.py — World map loading and tile rendering.

Loads the 512×512 binary map.dat and renders visible tiles into the viewport
using a scrolling camera.

Tile types (CConstants.h):
  0 = Empty / walkable ground
  1 = Rock
  2 = Lava
  3 = City center

Spritesheet layout (imgRocks.bmp / imgLava.bmp):
  768×48 px — 16 frames of 48 px wide.
  Frame index = neighbor connectivity (0–15):
    left  = 1 if right neighbor differs (or map edge)
    right = 1 if left  neighbor differs (or map edge)
    up    = 1 if lower neighbor differs (or map edge)
    down  = 1 if upper neighbor differs (or map edge)
    index = left + right*2 + down*4 + up*8
  Spritesheet X offset = index * TILE_SIZE
"""

import pygame
import settings


class GameMap:
    """Loads and renders the scrollable world map."""

    def __init__(
        self,
        map_data: list[list[int]],
        rock_sheet: pygame.Surface,
        lava_sheet: pygame.Surface,
    ) -> None:
        self._data       = map_data
        self._rock_sheet = rock_sheet
        self._lava_sheet = lava_sheet
        print("[GameMap] Pre-computing tile variants…")
        self._tiles = self._calculate_tiles()
        print("[GameMap] Ready.")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_tile(self, tile_x: int, tile_y: int) -> int:
        """Return tile type at world tile (tile_x, tile_y). Out-of-bounds = rock."""
        if 0 <= tile_x < settings.MAP_SIZE and 0 <= tile_y < settings.MAP_SIZE:
            return self._data[tile_x][tile_y]
        return settings.MAP_TILE_ROCK

    def draw(
        self,
        screen: pygame.Surface,
        camera_x: float,
        camera_y: float,
        field_rect: pygame.Rect,
    ) -> None:
        """
        Draw the terrain tiles visible in field_rect.

        camera_x / camera_y are world-pixel offsets of the viewport top-left.
        Empty tiles are transparent (ground texture shows through).
        """
        ts   = settings.TILE_SIZE
        size = settings.MAP_SIZE

        tx0 = max(0,        int(camera_x // ts))
        ty0 = max(0,        int(camera_y // ts))
        tx1 = min(size - 1, int((camera_x + field_rect.width)  // ts) + 1)
        ty1 = min(size - 1, int((camera_y + field_rect.height) // ts) + 1)

        src_rect = pygame.Rect(0, 0, ts, ts)  # reused each tile — avoids per-tile allocation
        for tx in range(tx0, tx1 + 1):
            for ty in range(ty0, ty1 + 1):
                tile_type = self._data[tx][ty]
                if tile_type == settings.MAP_TILE_EMPTY:
                    continue

                sheet      = self._rock_sheet if tile_type == settings.MAP_TILE_ROCK else self._lava_sheet
                src_rect.x = self._tiles[tx][ty]
                screen_x   = field_rect.x + tx * ts - round(camera_x)
                screen_y   = field_rect.y + ty * ts - round(camera_y)
                screen.blit(sheet, (screen_x, screen_y), src_rect)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _calculate_tiles(self) -> list[list[int]]:
        """
        Pre-compute the spritesheet X offset for every solid tile.

        The C++ source (CMap::CalculateTiles) uses confusingly named variables
        because its renderer had both axes inverted ((myX-tileX)*48 places high
        X to the LEFT). We use standard screen coordinates (high X = right,
        high Y = down), so the connectivity bits must be re-mapped to match the
        actual spritesheet layout verified by pixel scan:
          bit 0 (×1) = left edge, bit 1 (×2) = right edge,
          bit 2 (×4) = bottom edge, bit 3 (×8) = top edge.
        """
        size  = settings.MAP_SIZE
        tiles = [[0] * size for _ in range(size)]

        for i in range(size):
            for j in range(size):
                curr = self._data[i][j]
                if curr not in (settings.MAP_TILE_ROCK, settings.MAP_TILE_LAVA):
                    continue

                # Which neighbors are a different tile type?
                east  = 1 if (i == size - 1 or self._data[i + 1][j] != curr) else 0  # right on screen
                west  = 1 if (i == 0        or self._data[i - 1][j] != curr) else 0  # left on screen
                south = 1 if (j == size - 1 or self._data[i][j + 1] != curr) else 0  # bottom on screen
                north = 1 if (j == 0        or self._data[i][j - 1] != curr) else 0  # top on screen

                # Sprite frame bit layout (verified from spritesheet scan):
                #   bit 0 (×1) = left edge transparent
                #   bit 1 (×2) = right edge transparent
                #   bit 2 (×4) = bottom edge transparent
                #   bit 3 (×8) = top edge transparent
                # The C++ formula used inverted axes so its variable names are
                # misleading. Map correctly for standard screen coordinates:
                tiles[i][j] = (west + east * 2 + south * 4 + north * 8) * settings.TILE_SIZE

        return tiles
