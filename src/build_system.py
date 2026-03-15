"""
src/build_system.py — City build state: canBuild array, cash, research timers.

Adapts the server-side CCity logic (server/CCity.cpp) for single-player.

canBuild[i] values  (matches C++ server):
  0 = cannot build (locked or prereq not met)
  1 = available to build
  2 = already built (one of this type exists; most types limited to one)

Build tree (settings.BUILD_TREE, 12 item slots k=0..11):
  Research building for slot k lives at buildingTypes index 2 + 2*k.
  Factory building for slot k lives at buildingTypes index 3 + 2*k.
  BUILD_TREE[k] = prerequisite slot index, or -1.
  When research for slot k completes → unlock factory[k] + any research[j]
  whose BUILD_TREE[j] == k.

Initial unlocks (from C++ CCity::resetToDefault):
  can_build[1] = 1  (House)
  can_build[2] = 1  (Bazooka Research, slot k=0, BUILD_TREE[0]=-1)
  can_build[4] = 1  (Turret Research,  slot k=1, BUILD_TREE[1]=-1)
"""

import settings

_N = settings.NUM_BUILD_TYPES   # 26


class CityBuildState:
    """Tracks what the player can build, available cash, and in-progress research."""

    def __init__(self) -> None:
        self.can_build: list[int] = [0] * _N
        self.cash: int = settings.STARTING_CASH
        self._research_timer: list[float] = [0.0] * _N

        # Initial unlocks — mirrors CCity::resetToDefault()
        self.can_build[1] = 1  # House (always available, multiple allowed)
        self.can_build[2] = 1  # Bazooka Research
        self.can_build[4] = 1  # Turret Research

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        """Tick research timers; fire unlock callbacks on completion."""
        for i in range(_N):
            if self._research_timer[i] > 0.0:
                self._research_timer[i] -= dt
                if self._research_timer[i] <= 0.0:
                    self._research_timer[i] = 0.0
                    self._on_research_complete(i)

    def can_afford(self) -> bool:
        return self.cash >= settings.COST_BUILDING

    def try_place(self, menu_index: int) -> bool:
        """
        Attempt to place the building at menu_index (0-25).
        Deducts cash and updates can_build on success.
        Returns True if accepted.
        """
        if not (0 <= menu_index < _N):
            return False
        if self.can_build[menu_index] != 1:
            return False
        if not self.can_afford():
            return False

        self.cash -= settings.COST_BUILDING

        btype = settings.BUILDING_TYPES[menu_index]
        bclass = btype // 100  # 1=Factory 2=Hospital 3=House 4=Research

        # Houses can be built multiple times; all other types are one-of-a-kind
        if bclass != 3:
            self.can_build[menu_index] = 2  # "already has"

        # Research buildings start a completion timer
        if bclass == 4:
            self._research_timer[menu_index] = settings.RESEARCH_TIMER

        return True

    def is_researching(self, menu_index: int) -> bool:
        return self._research_timer[menu_index] > 0.0

    def research_progress(self, menu_index: int) -> float:
        """Fraction of research remaining [0=done, 1=just started]."""
        if self._research_timer[menu_index] <= 0.0:
            return 0.0
        return self._research_timer[menu_index] / settings.RESEARCH_TIMER

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _item_slot(self, research_menu_index: int) -> int:
        """Map research menu index (2, 4, 6, …, 24) → item slot k (0-11)."""
        return (research_menu_index - 2) // 2

    def _on_research_complete(self, research_menu_index: int) -> None:
        """Unlock the matching factory and any newly-unlocked research tiers."""
        k = self._item_slot(research_menu_index)
        factory_idx = research_menu_index + 1

        # Unlock the paired factory (if not already built)
        if factory_idx < _N and self.can_build[factory_idx] == 0:
            self.can_build[factory_idx] = 1

        # Unlock any dependent research whose prereq just became satisfied
        for j, prereq in enumerate(settings.BUILD_TREE):
            if prereq == k:
                dep_idx = 2 + 2 * j
                if dep_idx < _N and self.can_build[dep_idx] == 0:
                    self.can_build[dep_idx] = 1

        # MedKit Research (k=3) also unlocks Hospital
        if k == 3 and self.can_build[0] == 0:
            self.can_build[0] = 1
