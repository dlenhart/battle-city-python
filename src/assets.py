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
        os.path.join(_PROJECT_ROOT, "assets", filename),
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


def load_bullet_sprites(filepath: str) -> pygame.Surface:
    """
    Load imgbullets.bmp and return the surface with colorkey set.

    Layout: 32x32px, 8x8 frames.
      X axis: animation frame (0-3)  →  src_x = frame * 8
      Y axis: bullet type    (0-3)  →  src_y = type  * 8

    The surface is returned as-is; callers blit sub-rects from it each frame
    using Bullet.sprite_rect so no pre-extraction is needed.
    """
    sheet    = pygame.image.load(filepath).convert()
    colorkey = sheet.get_at((0, 0))
    sheet.set_colorkey(colorkey)
    print(f"[imgBullets] {sheet.get_width()}x{sheet.get_height()}")
    return sheet


def load_map_data(filepath: str) -> list[list[int]]:
    """
    Load map.dat binary file into a 512×512 list indexed as data[x][y].

    File layout: row-major in C order (map[x][0..511] then map[x+1][0..511]).
    Tile types: 0=empty, 1=rock, 2=lava, 3=city.
    """
    size = settings.MAP_SIZE
    with open(filepath, "rb") as f:
        raw = f.read()
    data = [[raw[x * size + y] for y in range(size)] for x in range(size)]
    print(f"[map.dat] Loaded {size}×{size} world map ({len(raw)} bytes)")
    return data


_MAGENTA = (255, 0, 255)

def load_tile_sheet(filepath: str) -> pygame.Surface:
    """
    Load a terrain tile spritesheet (imgRocks.bmp or imgLava.bmp).

    Layout: 768×48 px — 16 frames of 48 px wide, each a connectivity variant.

    Colorkey handling:
      imgLava.bmp  — uses magenta (255,0,255) as transparency; set it explicitly.
      imgRocks.bmp — fully opaque; no colorkey needed.
    Sampling pixel (0,0) is wrong for lava because that pixel is blue texture.
    Instead we scan a small sample; if any magenta pixel exists, use magenta.
    """
    raw   = pygame.image.load(filepath)
    sheet = raw.convert()

    w, h = sheet.get_width(), sheet.get_height()
    has_magenta = any(
        sheet.get_at((x, y))[:3] == _MAGENTA
        for x in range(0, w, 8)
        for y in range(0, h, 8)
    )
    if has_magenta:
        sheet.set_colorkey(_MAGENTA)
        print(f"[tile sheet] {w}x{h}, colorkey=magenta — {filepath}")
    else:
        print(f"[tile sheet] {w}x{h}, no colorkey — {filepath}")
    return sheet


def load_sound(filepath: str | None, volume: float = 1.0) -> pygame.mixer.Sound | None:
    """Load a WAV file, set volume, and return it. Returns None if path is None."""
    if filepath is None:
        return None
    sound = pygame.mixer.Sound(filepath)
    sound.set_volume(volume)
    return sound


def load_engine_sound(filepath: str | None, volume: float = 0.6) -> pygame.mixer.Sound | None:
    """Load the tank engine WAV, set volume, and return it. Returns None on failure."""
    return load_sound(filepath, volume)
