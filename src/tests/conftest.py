"""
Shared pytest fixtures for the Battle City test suite.

pygame requires at least a display mode to be set before surfaces can be
created (e.g. convert(), subsurface()).  This module initialises pygame once
per session using a headless SDL driver so no real window is opened.
"""

import os
import pytest

# Use headless SDL drivers so tests run without a display or audio device.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


@pytest.fixture(scope="session", autouse=True)
def pygame_session():
    """Initialize pygame once for the entire test session."""
    import pygame
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    pygame.display.set_mode((800, 600))
    yield
    pygame.quit()


import pygame


@pytest.fixture
def pygame_surface():
    """Return a 800x600 pygame Surface for testing HUD drawing."""
    return pygame.Surface((800, 600))
