"""
src/bullet.py — Bullet projectile logic.

Sprite layout of imgbullets.bmp (32x32, 8x8 frames):
  X axis: animation frame (0-3)  →  frame_x = animation * 8
  Y axis: bullet type   (0-3)  →  frame_y = type * 8
    Type 0 = Laser   (default player bullet)
    Type 1 = Rocket
    Type 2 = Plasma  (admin only)
    Type 3 = Flare
"""

import math
import pygame
import settings

BULLET_SIZE     = 8       # sprite width and height in pixels
BULLET_SPEED    = 300.0   # pixels per second (≈ 2× tank speed, matches C++ ratio)
ANIM_INTERVAL   = 0.08    # seconds between animation frames
NUM_ANIM_FRAMES = 4


class Bullet:
    """A single projectile fired by a tank."""

    def __init__(
        self,
        x: float,
        y: float,
        direction: int,
        bullet_type: int = 0,
    ) -> None:
        self.x           = x
        self.y           = y
        self.direction   = direction   # 0-31, matching player direction system
        self.bullet_type = bullet_type
        self.active      = True

        self._animation  = 0
        self._anim_timer = 0.0

    def update(self, dt: float) -> None:
        """Move and animate the bullet. Sets active=False when out of bounds."""
        self._move(dt)
        self._animate(dt)
        self._check_bounds()

    @property
    def sprite_rect(self) -> tuple[int, int, int, int]:
        """(src_x, src_y, width, height) into imgbullets.bmp for the current frame."""
        return (
            self._animation  * BULLET_SIZE,
            self.bullet_type * BULLET_SIZE,
            BULLET_SIZE,
            BULLET_SIZE,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _move(self, dt: float) -> None:
        angle     = self.direction * (2 * math.pi / settings.NUM_DIRECTIONS)
        self.x   += math.sin(angle) * BULLET_SPEED * dt
        self.y   -= math.cos(angle) * BULLET_SPEED * dt

    def _animate(self, dt: float) -> None:
        self._anim_timer += dt
        if self._anim_timer >= ANIM_INTERVAL:
            self._anim_timer -= ANIM_INTERVAL
            self._animation   = (self._animation + 1) % NUM_ANIM_FRAMES

    def _check_bounds(self) -> None:
        limit = float(settings.MAP_PIXEL_SIZE)
        if (
            self.x + BULLET_SIZE < 0
            or self.x > limit
            or self.y + BULLET_SIZE < 0
            or self.y > limit
        ):
            self.active = False
