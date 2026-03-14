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

    def __init__(
        self,
        x: float,
        y: float,
        direction: int = 0,
        city_x: float = 0.0,
        city_y: float = 0.0,
    ) -> None:
        self.x          = x
        self.y          = y
        self.direction  = direction  # 0-31
        self.is_moving  = 0         # 1=forward, -1=backward, 0=stopped
        self.is_turning = 0         # 1=right (CW), -1=left (CCW), 0=stopped
        self.hp         = settings.MAX_HEALTH
        self.city_x     = city_x
        self.city_y     = city_y

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

    def update(self, dt: float, get_tile=None) -> None:
        """Advance turn, position, and fire cooldown by dt seconds.

        get_tile: optional callable(tile_x, tile_y) -> int from GameMap.
        When provided, solid tiles (rock/lava) block movement.
        """
        self._update_turning(dt)
        self._update_movement(dt, get_tile)
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
        """(tile_x, tile_y) world tile the tank occupies, for HUD display."""
        return int(self.x // settings.TILE_SIZE), int(self.y // settings.TILE_SIZE)

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

    def _update_movement(self, dt: float, get_tile=None) -> None:
        """Move forward or backward along the current heading using trig.

        Axes are tested independently so the tank slides along walls instead
        of stopping dead when clipping a corner.
        """
        if not self.is_moving:
            return

        angle = self.direction * (2 * math.pi / settings.NUM_DIRECTIONS)
        vel_x = math.sin(angle) * settings.MOVEMENT_SPEED * self.is_moving * dt
        vel_y = -math.cos(angle) * settings.MOVEMENT_SPEED * self.is_moving * dt

        max_x = float(settings.MAP_PIXEL_SIZE - settings.TANK_FRAME_W)
        max_y = float(settings.MAP_PIXEL_SIZE - settings.TANK_FRAME_H)

        new_x = max(0.0, min(self.x + vel_x, max_x))
        new_y = max(0.0, min(self.y + vel_y, max_y))

        if get_tile is None or not self._solid_at(new_x, self.y, get_tile):
            self.x = new_x
        if get_tile is None or not self._solid_at(self.x, new_y, get_tile):
            self.y = new_y

    @staticmethod
    def _solid_at(px: float, py: float, get_tile) -> bool:
        """Return True if the tank bounding box at (px, py) overlaps a solid tile."""
        ts   = settings.TILE_SIZE
        size = ts - 1  # inset 1px so flush alignment doesn't bleed into neighbour
        solid = (settings.MAP_TILE_ROCK, settings.MAP_TILE_LAVA)
        for cx in (int(px), int(px + size)):
            for cy in (int(py), int(py + size)):
                if get_tile(cx // ts, cy // ts) in solid:
                    return True
        return False
