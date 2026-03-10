"""
src/camera.py — Camera / viewport coordinate conversion.

Tracks a world-pixel scroll offset and converts world coordinates to
screen coordinates within the field viewport.
"""

import settings


class Camera:
    """Follows a target in world space and converts world coords to screen coords."""

    def __init__(self) -> None:
        self.x = 0.0
        self.y = 0.0

    def follow(self, world_x: float, world_y: float) -> None:
        """Re-center the viewport on (world_x, world_y), clamped to map bounds."""
        max_cam = float(settings.MAP_PIXEL_SIZE)
        self.x = max(0.0, min(
            world_x - settings.FIELD_WIDTH  / 2 + settings.TANK_FRAME_W / 2,
            max_cam - settings.FIELD_WIDTH,
        ))
        self.y = max(0.0, min(
            world_y - settings.FIELD_HEIGHT / 2 + settings.TANK_FRAME_H / 2,
            max_cam - settings.FIELD_HEIGHT,
        ))

    def to_screen(self, world_x: float, world_y: float) -> tuple[int, int]:
        """Convert world pixel coordinates to screen pixel coordinates in the field viewport."""
        return (
            settings.FIELD_X + int(world_x - self.x),
            settings.FIELD_Y + int(world_y - self.y),
        )
