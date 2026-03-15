"""
src/animation.py — Reusable frame-cycling timer.

Composited into any sprite that needs a looping animation step counter,
eliminating copy-pasted timer/step logic across Building, PlacedBuilding,
and Bullet.
"""

__all__ = ["AnimationTimer"]


class AnimationTimer:
    """Advances a step counter by 1 every `interval` seconds, cycling at `num_steps`.

    Usage::

        self._anim = AnimationTimer(interval=0.5, num_steps=6, start_step=2)

        def update(self, dt):
            self._anim.tick(dt)

        @property
        def sprite_col(self):
            return self._anim.step // 2   # or whatever mapping the sheet needs
    """

    __slots__ = ("_interval", "_num_steps", "_step", "_timer")

    def __init__(
        self,
        interval:   float,
        num_steps:  int,
        start_step: int = 0,
    ) -> None:
        self._interval  = interval
        self._num_steps = num_steps
        self._step      = start_step % num_steps
        self._timer     = 0.0

    @property
    def step(self) -> int:
        """Current animation step index (0 … num_steps-1)."""
        return self._step

    def tick(self, dt: float) -> None:
        """Advance the timer by dt seconds, cycling the step when due."""
        self._timer += dt
        if self._timer >= self._interval:
            self._timer -= self._interval
            self._step = (self._step + 1) % self._num_steps
