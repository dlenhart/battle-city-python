"""
src/explosion.py — Small bullet-impact explosion animation.

Spritesheet layout (imgSExplosion.bmp, 480×48 px):
  10 frames of 48×48 px laid out horizontally.
  Frame index 0–9, left to right.
  Animation: 20 ms per frame (matches C++ CExplode.cpp), total 200 ms.
"""

import settings

EXPLOSION_SIZE    = 48      # sprite frame width and height in pixels
NUM_FRAMES        = 10      # total animation frames
FRAME_INTERVAL    = 0.020   # seconds per frame (20 ms, matches C++)


class Explosion:
    """A single small explosion anchored at a world pixel position."""

    def __init__(self, center_x: float, center_y: float) -> None:
        # Top-left world position so the sprite is centered on the impact point.
        self.x      = center_x - EXPLOSION_SIZE / 2
        self.y      = center_y - EXPLOSION_SIZE / 2
        self.active = True

        self._frame = 0
        self._timer = 0.0

    def update(self, dt: float) -> None:
        """Advance the animation; deactivate when the last frame finishes."""
        self._timer += dt
        if self._timer >= FRAME_INTERVAL:
            self._timer -= FRAME_INTERVAL
            self._frame += 1
            if self._frame >= NUM_FRAMES:
                self.active = False

    @property
    def sprite_rect(self) -> tuple[int, int, int, int]:
        """(src_x, src_y, width, height) into imgSExplosion.bmp for the current frame."""
        return (self._frame * EXPLOSION_SIZE, 0, EXPLOSION_SIZE, EXPLOSION_SIZE)
