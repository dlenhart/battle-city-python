"""
src/assets.py — Asset loading utilities.
"""

import os
import pygame
import settings

# Project root = one level above this file (src/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_asset(filename: str) -> str | None:
    """Return the absolute path to an asset file, or None if not found."""
    search_paths = [
        os.path.join(_PROJECT_ROOT, filename),
        os.path.join(_PROJECT_ROOT, "assets", "images", filename),
        os.path.join(_PROJECT_ROOT, "assets", "sfx", filename),
        os.path.join(_PROJECT_ROOT, "data", filename),
    ]
    for path in search_paths:
        if os.path.isfile(path):
            return path
    return None


def extract_frame(
    sheet: pygame.Surface, col: int, row: int, colorkey
) -> pygame.Surface:
    """Extract a single 48x48 frame from a spritesheet."""
    rect  = pygame.Rect(
        col * settings.TANK_FRAME_W,
        row * settings.TANK_FRAME_H,
        settings.TANK_FRAME_W,
        settings.TANK_FRAME_H,
    )
    frame = sheet.subsurface(rect).copy()
    frame.set_colorkey(colorkey)
    return frame


def load_tank_sprites(filepath: str, tank_row: int = 0) -> list[pygame.Surface]:
    """
    Load imgTanks.bmp and return one Surface per direction column.

    Spritesheet layout: 16 cols x 50 rows (768 x 2400 px).
      - Each column  = one of 16 direction angles (22.5° increments, clockwise).
      - Each row     = one tank type  (row 0 = player / friend commando).
      - Sprite col   = direction // 2   (direction is 0-31, matching C++).

    Cardinal column mapping:
      Col  0 = North (UP)
      Col  4 = West  (LEFT)
      Col  8 = South (DOWN)
      Col 12 = East  (RIGHT)

    Returns a list of pygame.Surface frames indexed by (direction // 2).
    """
    sheet    = pygame.image.load(filepath).convert()
    colorkey = sheet.get_at((0, 0))
    sheet.set_colorkey(colorkey)

    cols = sheet.get_width()  // settings.TANK_FRAME_W
    rows = sheet.get_height() // settings.TANK_FRAME_H
    print(f"[imgTanks] {sheet.get_width()}x{sheet.get_height()} — {cols} cols x {rows} rows")

    frames = [extract_frame(sheet, c, tank_row, colorkey) for c in range(cols)]
    print(f"[imgTanks] Loaded {len(frames)} direction frames from row {tank_row}")
    return frames


def load_ground_tile(filepath: str) -> pygame.Surface:
    """Load imgGround.bmp as a tileable surface."""
    tile = pygame.image.load(filepath).convert()
    print(f"[imgGround] {tile.get_width()}x{tile.get_height()}")
    return tile


def build_ground_surface(tile: pygame.Surface) -> pygame.Surface:
    """Pre-render the full playing field by tiling the ground image."""
    surf = pygame.Surface((settings.FIELD_WIDTH, settings.FIELD_HEIGHT))
    tw, th = tile.get_width(), tile.get_height()
    for y in range(0, settings.FIELD_HEIGHT, th):
        for x in range(0, settings.FIELD_WIDTH, tw):
            surf.blit(tile, (x, y))
    return surf


def load_engine_sound(filepath: str | None, volume: float = 0.6) -> pygame.mixer.Sound | None:
    """Load the tank engine WAV, set volume, and return it. Returns None on failure."""
    if filepath is None:
        return None
    sound = pygame.mixer.Sound(filepath)
    sound.set_volume(volume)
    return sound
