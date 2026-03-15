"""Tests for the build system (CityBuildState)."""

import pytest
import settings
from src.build_system import CityBuildState


# ---------------------------------------------------------------------------
# Stub: a minimal PlacedBuilding substitute for update() tests
# ---------------------------------------------------------------------------

class _FakePlaced:
    """Minimal PlacedBuilding stub for passing to CityBuildState.update()."""
    def __init__(self, menu_index: int, *, max_pop: bool = True):
        self.menu_index  = menu_index
        self.has_max_pop = max_pop


def _maxpop(menu_index: int) -> list:
    """Return a one-element placed-buildings list at max population."""
    return [_FakePlaced(menu_index, max_pop=True)]


def _nopop(menu_index: int) -> list:
    """Return a one-element placed-buildings list with no population."""
    return [_FakePlaced(menu_index, max_pop=False)]


# ---------------------------------------------------------------------------

class TestInitialState:
    def setup_method(self):
        self.state = CityBuildState()

    def test_starting_cash(self):
        assert self.state.cash == settings.STARTING_CASH

    def test_house_available(self):
        assert self.state.can_build[1] == 1

    def test_bazooka_research_available(self):
        assert self.state.can_build[2] == 1

    def test_turret_research_available(self):
        assert self.state.can_build[4] == 1

    def test_hospital_not_available(self):
        assert self.state.can_build[0] == 0

    def test_factories_not_available(self):
        # No factories should be buildable until research completes
        factory_indices = [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]
        for i in factory_indices:
            assert self.state.can_build[i] == 0, f"Factory at index {i} should be locked"

    def test_locked_research_not_available(self):
        # Cloak Research (index 6) requires Bazooka Research to complete first
        assert self.state.can_build[6] == 0


class TestCanAfford:
    def setup_method(self):
        self.state = CityBuildState()

    def test_can_afford_with_full_cash(self):
        assert self.state.can_afford()

    def test_cannot_afford_when_broke(self):
        self.state.cash = settings.COST_BUILDING - 1
        assert not self.state.can_afford()

    def test_can_afford_at_exact_cost(self):
        self.state.cash = settings.COST_BUILDING
        assert self.state.can_afford()


class TestTryPlace:
    def setup_method(self):
        self.state = CityBuildState()

    def test_place_house_deducts_cash(self):
        before = self.state.cash
        result = self.state.try_place(1)  # House
        assert result is True
        assert self.state.cash == before - settings.COST_BUILDING

    def test_place_house_stays_available(self):
        # Houses can be built multiple times
        self.state.try_place(1)
        assert self.state.can_build[1] == 1

    def test_place_research_marks_as_built(self):
        self.state.try_place(2)  # Bazooka Research
        assert self.state.can_build[2] == 2

    def test_cannot_place_locked_building(self):
        result = self.state.try_place(3)  # Bazooka Factory (locked)
        assert result is False

    def test_cannot_place_when_broke(self):
        self.state.cash = 0
        result = self.state.try_place(1)
        assert result is False

    def test_cannot_place_already_built(self):
        self.state.try_place(2)  # Bazooka Research → marks as 2
        result = self.state.try_place(2)
        assert result is False

    def test_place_out_of_range_index(self):
        assert self.state.try_place(-1) is False
        assert self.state.try_place(26) is False


class TestResearch:
    def setup_method(self):
        self.state = CityBuildState()

    def test_research_not_active_before_placement(self):
        # Timer starts only once the building has max population, not at placement
        self.state.try_place(2)  # Bazooka Research placed but no population yet
        assert not self.state.is_researching(2)

    def test_research_starts_when_max_pop_reached(self):
        # After update with a max-pop building, is_researching should be True
        self.state.try_place(2)
        self.state.update(0.1, _maxpop(2))
        assert self.state.is_researching(2)

    def test_research_stalls_without_population(self):
        # Building placed, ticked once to start, then pop drops → timer freezes
        self.state.try_place(2)
        self.state.update(0.1, _maxpop(2))          # start timer
        progress_before = self.state.research_progress(2)
        self.state.update(1.0, _nopop(2))           # no pop → frozen
        progress_after = self.state.research_progress(2)
        assert progress_after == progress_before    # timer did not move

    def test_house_does_not_start_research(self):
        self.state.try_place(1)
        self.state.update(1.0, [])
        assert not self.state.is_researching(1)

    def test_research_progress_decreases(self):
        self.state.try_place(2)
        self.state.update(0.1, _maxpop(2))          # start timer
        p1 = self.state.research_progress(2)
        self.state.update(1.0, _maxpop(2))
        p2 = self.state.research_progress(2)
        assert p2 < p1

    def test_research_completes_and_unlocks_factory(self):
        self.state.try_place(2)  # Bazooka Research
        self.state.update(settings.RESEARCH_TIMER + 0.1, _maxpop(2))
        assert self.state.can_build[3] == 1  # Bazooka Factory unlocked

    def test_research_unlocks_dependent_research(self):
        # Bazooka Research (k=0) completion unlocks Cloak Research (k=2) and MedKit (k=3)
        self.state.try_place(2)
        self.state.update(settings.RESEARCH_TIMER + 0.1, _maxpop(2))
        assert self.state.can_build[6] == 1  # Cloak Research
        assert self.state.can_build[8] == 1  # MedKit Research

    def test_turret_research_unlocks_plasma_and_mine(self):
        self.state.try_place(4)  # Turret Research (k=1)
        self.state.update(settings.RESEARCH_TIMER + 0.1, _maxpop(4))
        assert self.state.can_build[10] == 1  # Plasma Turret Research
        assert self.state.can_build[12] == 1  # Mine Research

    def test_medkit_research_unlocks_hospital(self):
        self.state.can_build[8] = 1  # manually unlock MedKit Research
        self.state.try_place(8)
        self.state.update(settings.RESEARCH_TIMER + 0.1, _maxpop(8))
        assert self.state.can_build[0] == 1  # Hospital

    def test_no_double_unlock(self):
        # Already-built research (value=2) should not be reset to 1 by a dependent unlock
        self.state.try_place(4)  # Turret Research — marks it 2
        self.state.update(settings.RESEARCH_TIMER + 0.1, _maxpop(4))
        self.state.can_build[5] = 1
        self.state.try_place(5)  # Turret Factory
        # Turret Research should still be 2 (not reset)
        assert self.state.can_build[4] == 2

    def test_research_does_not_restart_after_completion(self):
        # After research completes, further updates should not restart the timer
        self.state.try_place(2)
        self.state.update(settings.RESEARCH_TIMER + 0.1, _maxpop(2))
        assert not self.state.is_researching(2)
        self.state.update(1.0, _maxpop(2))
        assert not self.state.is_researching(2)


class TestBuildTree:
    """Verify BUILD_TREE array lengths and values are self-consistent."""

    def test_build_tree_length(self):
        assert len(settings.BUILD_TREE) == 12

    def test_prereq_indices_in_range(self):
        for i, prereq in enumerate(settings.BUILD_TREE):
            assert prereq == -1 or 0 <= prereq < 12, \
                f"BUILD_TREE[{i}]={prereq} is out of range"

    def test_building_types_length(self):
        assert len(settings.BUILDING_TYPES) == settings.NUM_BUILD_TYPES

    def test_build_names_length(self):
        assert len(settings.BUILD_NAMES) == settings.NUM_BUILD_TYPES

    def test_build_button_length(self):
        assert len(settings.BUILD_BUTTON) == settings.NUM_BUILD_TYPES

    def test_build_button_values_in_range(self):
        for i, v in enumerate(settings.BUILD_BUTTON):
            assert 0 <= v <= 13, f"BUILD_BUTTON[{i}]={v} exceeds icon sheet range"
