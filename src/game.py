"""
src/game.py — Main game orchestration.

Owns the pygame window, clock, asset references, and the main loop.
"""

import sys
import pygame

import settings
from src.assets import (
    find_asset,
    load_tank_sprites,
    load_ground_tile,
    build_ground_surface,
    load_engine_sound,
)
from src.player import Player
from src.hud    import HUD


class Game:
    """Initializes pygame, loads assets, and runs the game loop."""

    def __init__(self) -> None:
        self._init_pygame()
        self._load_assets()
        self._create_player()
        self._create_hud()

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def _init_pygame(self) -> None:
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self._screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        pygame.display.set_caption("Battle City")
        self._clock = pygame.time.Clock()

    def _load_assets(self) -> None:
        tanks_path  = find_asset("imgTanks.bmp")
        ground_path = find_asset("imgGround.bmp")
        engine_path = find_asset("engine.wav")

        if not tanks_path:
            sys.exit("ERROR: imgTanks.bmp not found — place it in the project root.")
        if not ground_path:
            sys.exit("ERROR: imgGround.bmp not found — place it in the project root.")

        print(f"Loading tanks:  {tanks_path}")
        print(f"Loading ground: {ground_path}")

        self._tank_frames    = load_tank_sprites(tanks_path, tank_row=0)
        self._ground_surface = build_ground_surface(load_ground_tile(ground_path))

        self._engine_sound   = load_engine_sound(engine_path)
        self._engine_channel = None
        if engine_path:
            print(f"Loading engine sound: {engine_path}")
        else:
            print("WARNING: engine.wav not found — tank sounds disabled")

    def _create_player(self) -> None:
        start_x = float(settings.FIELD_X + settings.FIELD_WIDTH  // 2 - settings.TANK_FRAME_W // 2)
        start_y = float(settings.FIELD_Y + settings.FIELD_HEIGHT - settings.TANK_FRAME_H * 2)
        self._player = Player(start_x, start_y, direction=0)

    def _create_hud(self) -> None:
        font = pygame.font.SysFont("consolas", 16)
        self._hud = HUD(font)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start and run the game loop until the player quits."""
        running = True
        while running:
            dt = self._clock.tick(settings.FPS) / 1000.0
            running = self._handle_events()
            self._update(dt)
            self._draw()
        self._quit()

    # ------------------------------------------------------------------
    # Per-frame methods
    # ------------------------------------------------------------------

    def _handle_events(self) -> bool:
        """Process the event queue. Returns False when the game should quit."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
        return True

    def _update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        self._player.handle_input(keys)
        self._player.update(dt)
        self._update_engine_sound()

    def _update_engine_sound(self) -> None:
        """Loop engine sound while moving; stop it when the tank is idle."""
        if not self._engine_sound:
            return

        if self._player.is_moving:
            if self._engine_channel is None or not self._engine_channel.get_busy():
                self._engine_channel = self._engine_sound.play(loops=-1)
        else:
            if self._engine_channel and self._engine_channel.get_busy():
                self._engine_channel.stop()
                self._engine_channel = None

    def _draw(self) -> None:
        self._screen.fill(settings.DARK_BG)
        self._screen.blit(self._ground_surface, (settings.FIELD_X, settings.FIELD_Y))

        tank_img = self._tank_frames[self._player.sprite_col]
        self._screen.blit(tank_img, (int(self._player.x), int(self._player.y)))

        self._hud.draw(self._screen, self._player)
        pygame.display.flip()

    def _quit(self) -> None:
        pygame.quit()
