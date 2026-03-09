"""
src/player.py — Player tank logic.

Owns movement, turning, and input handling.
Contains no rendering code and no pygame display calls.
"""

import math
import pygame
import settings

# Fire cooldown matches original C++ TIMER_SHOOT_LASER = 650 ms
FIRE_COOLDOWN = 0.65


class Player:
    """
    Represents the player-controlled tank.

    Direction uses the original C++ convention:
      0-31 clockwise, where 0 = North.
      Sprite column = direction // 2.

    Controls:
      UP / DOWN    — move forward / backward along current heading
      LEFT / RIGHT — turn counter-clockwise / clockwise
      SHIFT        — fire cannon
    """

    def __init__(self, x: float, y: float, direction: int = 0) -> None:
        self.x          = x
        self.y          = y
        self.direction  = direction  # 0-31
        self.is_moving  = 0         # 1=forward, -1=backward, 0=stopped
        self.is_turning = 0         # 1=right (CW), -1=left (CCW), 0=stopped

        self._turn_timer   = 0.0
        self._fire_cooldown = 0.0   # seconds until next shot is allowed
        self._fire_requested = False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def handle_input(self, keys) -> None:
        """Read pressed keys and update movement / turning / fire intent."""
        self.is_moving = (
             1 if keys[pygame.K_UP]    else
            -1 if keys[pygame.K_DOWN]  else 0
        )
        self.is_turning = (
             1 if keys[pygame.K_RIGHT] else
            -1 if keys[pygame.K_LEFT]  else 0
        )
        self._fire_requested = bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])

    def update(self, dt: float) -> None:
        """Advance turn, position, and fire cooldown by dt seconds."""
        self._update_turning(dt)
        self._update_movement(dt)
        self._fire_cooldown = max(0.0, self._fire_cooldown - dt)

    def try_fire(self) -> tuple[float, float, int] | None:
        """
        If the player is pressing fire and the cooldown has expired, consume
        the shot and return (spawn_x, spawn_y, direction).  Otherwise None.

        Spawn position is the center of the tank, offset by half a bullet
        so the projectile appears centered on the barrel.
        """
        if not self._fire_requested or self._fire_cooldown > 0.0:
            return None

        self._fire_cooldown = FIRE_COOLDOWN

        from src.bullet import BULLET_SIZE
        spawn_x = self.x + settings.TANK_FRAME_W / 2 - BULLET_SIZE / 2
        spawn_y = self.y + settings.TANK_FRAME_H / 2 - BULLET_SIZE / 2
        return spawn_x, spawn_y, self.direction

    # ------------------------------------------------------------------
    # Derived properties (used by HUD and Game for rendering / sound)
    # ------------------------------------------------------------------

    @property
    def sprite_col(self) -> int:
        """Spritesheet column for the current direction (direction // 2)."""
        return (self.direction // 2) % settings.NUM_SPRITE_COLS

    @property
    def tile_position(self) -> tuple[int, int]:
        """(col, row) grid tile the tank occupies, for HUD display."""
        col = int((self.x - settings.FIELD_X) // settings.TANK_FRAME_W)
        row = int((self.y - settings.FIELD_Y) // settings.TANK_FRAME_H)
        return col, row

    @property
    def heading_degrees(self) -> int:
        """Current heading in degrees (0-359), clockwise from North."""
        return int(self.direction * (360 / settings.NUM_DIRECTIONS))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _update_turning(self, dt: float) -> None:
        """Advance direction by one step every TURN_INTERVAL seconds."""
        if self.is_turning:
            self._turn_timer += dt
            while self._turn_timer >= settings.TURN_INTERVAL:
                self._turn_timer -= settings.TURN_INTERVAL
                self.direction = (self.direction + self.is_turning) % settings.NUM_DIRECTIONS
        else:
            self._turn_timer = 0.0

    def _update_movement(self, dt: float) -> None:
        """Move forward or backward along the current heading using trig."""
        if not self.is_moving:
            return

        angle = self.direction * (2 * math.pi / settings.NUM_DIRECTIONS)
        vel_x = math.sin(angle) * settings.MOVEMENT_SPEED * self.is_moving * dt
        vel_y = -math.cos(angle) * settings.MOVEMENT_SPEED * self.is_moving * dt

        self.x = max(
            settings.FIELD_X,
            min(self.x + vel_x, settings.FIELD_X + settings.FIELD_WIDTH  - settings.TANK_FRAME_W),
        )
        self.y = max(
            settings.FIELD_Y,
            min(self.y + vel_y, settings.FIELD_Y + settings.FIELD_HEIGHT - settings.TANK_FRAME_H),
        )
