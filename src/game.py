"""
src/game.py — Main game orchestration.

Owns the pygame window, clock, asset references, and the main loop.
The player and bullets operate in world coordinates (0 to MAP_PIXEL_SIZE).
A camera follows the player and maps world coords to screen coords within
the field viewport.
"""

import sys
import pygame

import settings
from src.assets import (
    find_asset,
    load_tank_sprites,
    load_ground_tile,
    load_engine_sound,
    load_bullet_sprites,
    load_map_data,
    load_tile_sheet,
)
from src.player import Player
from src.bullet import Bullet, BULLET_SIZE
from src.hud    import HUD
from src.map    import GameMap


class Game:
    """Initializes pygame, loads assets, and runs the game loop."""

    def __init__(self) -> None:
        self._init_pygame()
        self._load_assets()
        self._create_map()
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
        rocks_path  = find_asset("imgRocks.bmp")
        lava_path   = find_asset("imgLava.bmp")
        map_path    = find_asset("map.dat")
        engine_path = find_asset("engine.wav")

        for name, path in [
            ("imgTanks.bmp", tanks_path),
            ("imgGround.bmp", ground_path),
            ("imgRocks.bmp", rocks_path),
            ("imgLava.bmp", lava_path),
            ("map.dat", map_path),
        ]:
            if not path:
                sys.exit(f"ERROR: {name} not found.")
            print(f"Loading {name}: {path}")

        self._tank_frames  = load_tank_sprites(tanks_path, tank_row=0)
        self._ground_tile  = load_ground_tile(ground_path)
        self._rock_sheet   = load_tile_sheet(rocks_path)
        self._lava_sheet   = load_tile_sheet(lava_path)
        self._map_data     = load_map_data(map_path)

        self._engine_sound   = load_engine_sound(engine_path)
        self._engine_channel = None
        if engine_path:
            print(f"Loading engine sound: {engine_path}")
        else:
            print("WARNING: engine.wav not found — tank sounds disabled")

        bullets_path = find_asset("imgbullets.bmp")
        if not bullets_path:
            sys.exit("ERROR: imgbullets.bmp not found.")
        print(f"Loading bullets: {bullets_path}")
        self._bullet_sheet = load_bullet_sprites(bullets_path)

    def _create_map(self) -> None:
        self._game_map = GameMap(self._map_data, self._rock_sheet, self._lava_sheet)

    def _create_player(self) -> None:
        # Start near the center of the 512×512 world map
        start_x = float(settings.MAP_SIZE // 2 * settings.TILE_SIZE)
        start_y = float(settings.MAP_SIZE // 2 * settings.TILE_SIZE)
        self._player  = Player(start_x, start_y, direction=0)
        self._bullets: list[Bullet] = []

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
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
        return True

    def _update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        self._player.handle_input(keys)
        self._player.update(dt, get_tile=self._game_map.get_tile)
        self._update_engine_sound()
        self._update_bullets(dt)

    def _update_bullets(self, dt: float) -> None:
        shot = self._player.try_fire()
        if shot is not None:
            self._bullets.append(Bullet(*shot))

        for bullet in self._bullets:
            bullet.update(dt)

        self._bullets = [b for b in self._bullets if b.active]

    def _update_engine_sound(self) -> None:
        if not self._engine_sound:
            return

        if self._player.is_moving:
            if self._engine_channel is None or not self._engine_channel.get_busy():
                self._engine_channel = self._engine_sound.play(loops=-1)
        else:
            if self._engine_channel and self._engine_channel.get_busy():
                self._engine_channel.stop()
                self._engine_channel = None

    # ------------------------------------------------------------------
    # Camera
    # ------------------------------------------------------------------

    def _compute_camera(self) -> tuple[float, float]:
        """
        Return (cam_x, cam_y): world-pixel offset of the viewport top-left,
        clamped so the camera never shows outside the map.
        """
        cam_x = self._player.x - settings.FIELD_WIDTH  / 2 + settings.TANK_FRAME_W / 2
        cam_y = self._player.y - settings.FIELD_HEIGHT / 2 + settings.TANK_FRAME_H / 2
        max_cam = float(settings.MAP_PIXEL_SIZE)
        cam_x = max(0.0, min(cam_x, max_cam - settings.FIELD_WIDTH))
        cam_y = max(0.0, min(cam_y, max_cam - settings.FIELD_HEIGHT))
        return cam_x, cam_y

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw(self) -> None:
        cam_x, cam_y = self._compute_camera()
        field_rect = pygame.Rect(
            settings.FIELD_X, settings.FIELD_Y,
            settings.FIELD_WIDTH, settings.FIELD_HEIGHT,
        )

        self._screen.fill(settings.DARK_BG)

        # Clip all terrain + entity drawing to the field viewport
        self._screen.set_clip(field_rect)

        self._draw_ground(cam_x, cam_y)
        self._game_map.draw(self._screen, cam_x, cam_y, field_rect)
        self._draw_player(cam_x, cam_y)
        self._draw_bullets(cam_x, cam_y)

        self._screen.set_clip(None)

        self._hud.draw(self._screen, self._player)
        pygame.display.flip()

    def _draw_ground(self, cam_x: float, cam_y: float) -> None:
        """Tile the ground texture across the field, scrolling with the camera."""
        tw, th = self._ground_tile.get_width(), self._ground_tile.get_height()
        off_x  = int(cam_x) % tw
        off_y  = int(cam_y) % th
        y = settings.FIELD_Y - off_y
        while y < settings.FIELD_Y + settings.FIELD_HEIGHT:
            x = settings.FIELD_X - off_x
            while x < settings.FIELD_X + settings.FIELD_WIDTH:
                self._screen.blit(self._ground_tile, (x, y))
                x += tw
            y += th

    def _draw_player(self, cam_x: float, cam_y: float) -> None:
        screen_x = settings.FIELD_X + int(self._player.x - cam_x)
        screen_y = settings.FIELD_Y + int(self._player.y - cam_y)
        self._screen.blit(self._tank_frames[self._player.sprite_col], (screen_x, screen_y))

    def _draw_bullets(self, cam_x: float, cam_y: float) -> None:
        for bullet in self._bullets:
            src_x, src_y, w, h = bullet.sprite_rect
            src_rect = pygame.Rect(src_x, src_y, w, h)
            screen_x = settings.FIELD_X + int(bullet.x - cam_x)
            screen_y = settings.FIELD_Y + int(bullet.y - cam_y)
            self._screen.blit(self._bullet_sheet, (screen_x, screen_y), src_rect)

    def _quit(self) -> None:
        pygame.quit()
