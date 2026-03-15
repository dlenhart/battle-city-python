"""
src/collision.py — CollisionMap: Strategy pattern for tile-based collision.

Wraps the composite get_tile callable (terrain + placed buildings) and
exposes named solid-tile queries so the tile-type constants are defined
once rather than scattered across Player._solid_at and Bullet.hits_terrain.

The class is also callable as a plain get_tile function so it can be passed
to any existing code that expects a raw (tx, ty) -> int callable.
"""

import settings

__all__ = ["CollisionMap"]


class CollisionMap:
    """Centralises which tile types block tanks vs bullets (Strategy pattern).

    Attributes
    ----------
    TANK_SOLID   — frozenset of tile IDs that a tank cannot enter
    BULLET_SOLID — frozenset of tile IDs that stop a bullet
    """

    TANK_SOLID   = frozenset({settings.MAP_TILE_ROCK, settings.MAP_TILE_LAVA})
    BULLET_SOLID = frozenset({settings.MAP_TILE_ROCK})

    def __init__(self, get_tile) -> None:
        """
        Parameters
        ----------
        get_tile : callable(tile_x: int, tile_y: int) -> int
            The composite tile-query function, e.g. Game._tile_check.
        """
        self._get_tile = get_tile

    # ------------------------------------------------------------------
    # Callable interface — backward-compatible with raw get_tile usages
    # ------------------------------------------------------------------

    def __call__(self, tx: int, ty: int) -> int:
        """Delegate to the underlying get_tile so CollisionMap can be passed
        anywhere a plain callable is expected (e.g. legacy test helpers)."""
        return self._get_tile(tx, ty)

    # ------------------------------------------------------------------
    # Named queries
    # ------------------------------------------------------------------

    def is_tank_solid(self, tx: int, ty: int) -> bool:
        """True if a tank cannot enter tile (tx, ty)."""
        return self._get_tile(tx, ty) in self.TANK_SOLID

    def is_bullet_solid(self, tx: int, ty: int) -> bool:
        """True if a bullet is stopped by tile (tx, ty)."""
        return self._get_tile(tx, ty) in self.BULLET_SOLID
