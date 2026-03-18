"""
src/game.py — Main game orchestration.

Owns the pygame window, clock, asset references, and the main loop.
The player and bullets operate in world coordinates (0 to MAP_PIXEL_SIZE).
A camera follows the player and maps world coords to screen coords within
the field viewport.
"""

import pygame

import settings
from src.assets import (
    require_asset,
    optional_asset,
    load_tank_sprites,
    load_ground_tile,
    load_sound,
    load_bullet_sprites,
    load_map_data,
    load_tile_sheet,
    _load_colorkeyed_sheet,
)
from src.camera       import Camera
from src.collision    import CollisionMap
from src.player       import Player
from src.bullet       import Bullet
from src.explosion    import Explosion
from src.hud          import HUD, arrow_frame, draw_inventory
from src.map          import GameMap
from src.building     import BuildingManager
from src.minimap      import Minimap
from src.build_system import CityBuildState
from src.build_menu   import BuildMenu
from src.inventory import Inventory, WorldItem, ItemEffects


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
        self._screen = pygame.display.set_mode(
            (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT),
            pygame.DOUBLEBUF,
            vsync=1,
        )
        self._set_icon()
        pygame.display.set_caption("Battle City")
        self._clock      = pygame.time.Clock()
        self._camera     = Camera()
        # Built once — used in both _draw() and _try_place_building() (DRY)
        self._field_rect = pygame.Rect(
            settings.FIELD_X, settings.FIELD_Y,
            settings.FIELD_WIDTH, settings.FIELD_HEIGHT,
        )

    def _set_icon(self) -> None:
        icon_path = optional_asset("BC.ico")
        if icon_path:
            pygame.display.set_icon(pygame.image.load(icon_path))

    def _load_assets(self) -> None:
        self._tank_frames    = load_tank_sprites(require_asset("imgTanks.bmp"), tank_row=0)
        self._ground_tile    = load_ground_tile(require_asset("imgGround.bmp"))
        self._rock_sheet     = load_tile_sheet(require_asset("imgRocks.bmp"))
        self._lava_sheet     = load_tile_sheet(require_asset("imgLava.bmp"))
        self._building_sheet = load_tile_sheet(require_asset("imgBuildings.bmp"))
        self._map_data       = load_map_data(require_asset("map.dat"))
        self._ground_surf    = self._build_ground_surf()
        self._bullet_sheet   = load_bullet_sprites(require_asset("imgbullets.bmp"))

        interface_path = require_asset("imgInterface.bmp")
        self._interface_img  = pygame.image.load(interface_path).convert()

        self._engine_sound   = load_sound(
            optional_asset("engine.wav", "WARNING: engine.wav not found — tank sounds disabled"),
            volume=0.6,
        )
        self._engine_channel = None
        self._laser_sound    = load_sound(
            optional_asset("laser.wav", "WARNING: laser.wav not found — shoot sound disabled"),
            volume=0.7,
        )
        self._explode_sound  = load_sound(
            optional_asset("explode.wav", "WARNING: explode.wav not found — explosion sound disabled"),
            volume=0.8,
        )

        explosion_path = require_asset("imgSExplosion.bmp")
        self._explosion_sheet = _load_colorkeyed_sheet(explosion_path)
        print(f"[imgSExplosion] {self._explosion_sheet.get_width()}x{self._explosion_sheet.get_height()}")

        self._arrows_sheet     = _load_colorkeyed_sheet(require_asset("imgArrows.bmp"))
        self._arrows_red_sheet = _load_colorkeyed_sheet(require_asset("imgArrowsRed.bmp"))
        self._health_sheet     = _load_colorkeyed_sheet(require_asset("imgHealth.bmp"))

        build_icons_path = require_asset("imgBuildIcons.bmp")
        self._build_icons = pygame.image.load(build_icons_path).convert()
        self._build_icons.set_colorkey((255, 0, 255))

        self._items_sheet = _load_colorkeyed_sheet(require_asset("imgItems.bmp"))
        print(f"[imgItems] {self._items_sheet.get_width()}x{self._items_sheet.get_height()}")
        self._pop_sheet   = _load_colorkeyed_sheet(require_asset("imgPopulation.bmp"))
        print(f"[imgPopulation] {self._pop_sheet.get_width()}x{self._pop_sheet.get_height()}")
        self._inv_selection_sheet = _load_colorkeyed_sheet(
            require_asset("imgInventorySelection.bmp")
        )

    def _create_map(self) -> None:
        self._game_map      = GameMap(self._map_data, self._rock_sheet, self._lava_sheet)
        self._buildings     = BuildingManager(self._map_data)
        self._minimap       = Minimap(self._map_data, self._buildings)
        self._collision_map = CollisionMap(self._tile_check)

    def _create_player(self) -> None:
        start_x, start_y = self._buildings.random_spawn()
        self._player     = Player(start_x, start_y, direction=0,
                                  city_x=start_x, city_y=start_y)
        self._bullets:    list[Bullet]    = []
        self._explosions: list[Explosion] = []
        self._inventory:   Inventory        = Inventory()
        self._world_items: list[WorldItem]  = []

    def _create_hud(self) -> None:
        self._font        = pygame.font.SysFont("consolas", 14)
        self._hud         = HUD(self._font)
        self._build_state = CityBuildState()
        self._build_menu  = BuildMenu()

    # ------------------------------------------------------------------
    # Composite collision: terrain tiles + building blocked tiles
    # ------------------------------------------------------------------

    def _tile_check(self, tx: int, ty: int) -> int:
        """Return tile type, treating blocked building tiles as solid rock."""
        tile = self._game_map.get_tile(tx, ty)
        if tile != settings.MAP_TILE_EMPTY:
            return tile
        if self._buildings.is_tile_blocked(tx, ty):
            return settings.MAP_TILE_ROCK
        return settings.MAP_TILE_EMPTY

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
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
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self._build_menu.show_menu:
                        self._build_menu.close()
                    elif self._build_menu.is_placing != 0:
                        self._build_menu.cancel_placement()
                    else:
                        return False
                elif event.key == pygame.K_u:
                    self._try_pickup()
                elif event.key == pygame.K_d:
                    self._try_drop()
                elif event.key == pygame.K_LEFTBRACKET:
                    self._inventory.select_prev()
                elif event.key == pygame.K_RIGHTBRACKET:
                    self._inventory.select_next()
                elif event.key == pygame.K_h:
                    self._try_use_medkit()
                elif event.key == pygame.K_c:
                    self._try_use_cloak()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_mouse_click(event.pos)
        return True

    def _handle_mouse_click(self, pos: tuple[int, int]) -> None:
        x, y = pos

        # If the build menu popup is open, let it consume the click
        if self._build_menu.show_menu:
            self._build_menu.handle_click(pos, self._build_state.can_build)
            return

        # If in building-placement mode, try to place on the map
        if self._build_menu.is_placing > 0:
            self._try_place_building(pos)
            return

        # Check for click on the Build button on the control panel
        build_btn = pygame.Rect(
            settings.PANEL_X + settings.BUILD_BTN_REL_X,
            settings.PANEL_Y + settings.BUILD_BTN_REL_Y,
            settings.BUILD_BTN_W,
            settings.BUILD_BTN_H,
        )
        if build_btn.collidepoint(x, y):
            self._build_menu.open(
                settings.BUILD_MENU_ANCHOR_X,
                settings.BUILD_MENU_ANCHOR_Y,
            )

    def _try_place_building(self, pos: tuple[int, int]) -> None:
        """Convert a screen click to a tile position and place the selected building."""
        mx, my = pos
        if not self._field_rect.collidepoint(mx, my):
            return

        cam_x, cam_y = self._camera.x, self._camera.y
        world_x = mx - self._field_rect.x + int(cam_x)
        world_y = my - self._field_rect.y + int(cam_y)
        tile_x  = world_x // settings.TILE_SIZE
        tile_y  = world_y // settings.TILE_SIZE

        if not self._can_place_here(tile_x, tile_y):
            return

        menu_index = self._build_menu.is_placing - 1   # 1-indexed → 0-indexed
        if not self._build_state.try_place(menu_index):
            return

        self._buildings.add_placed(tile_x, tile_y, menu_index)
        self._build_menu.is_placing = 0

    def _can_place_here(self, tile_x: int, tile_y: int) -> bool:
        """Check that the 3×3 footprint is within bounds and free of obstacles."""
        ts = settings.TILE_SIZE
        if tile_x < 0 or tile_y < 0:
            return False
        if tile_x + 2 >= settings.MAP_SIZE or tile_y + 2 >= settings.MAP_SIZE:
            return False
        for dx in range(3):
            for dy in range(3):
                tx, ty = tile_x + dx, tile_y + dy
                if self._game_map.get_tile(tx, ty) != settings.MAP_TILE_EMPTY:
                    return False
                if self._buildings.is_tile_blocked(tx, ty):
                    return False
        return True

    def _update(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        self._player.handle_input(keys)
        self._player.update(dt, get_tile=self._collision_map)
        spawned = self._buildings.update(dt)
        self._world_items.extend(spawned)
        for wi in self._world_items:
            wi.update(dt)
        self._build_state.update(dt, self._buildings.placed_buildings)
        self._update_engine_sound()
        self._update_bullets(dt)

    def _update_bullets(self, dt: float) -> None:
        shot = self._player.try_fire()
        if shot is not None:
            self._bullets.append(Bullet(*shot))
            if self._laser_sound:
                self._laser_sound.play()

        for bullet in self._bullets:
            bullet.update(dt)
            if bullet.active and bullet.hits_terrain(self._tile_check):
                bullet.active = False
                self._spawn_explosion(bullet.x, bullet.y)

        self._bullets = [b for b in self._bullets if b.active]

        for explosion in self._explosions:
            explosion.update(dt)
        self._explosions = [e for e in self._explosions if e.active]

    def _spawn_explosion(self, bullet_x: float, bullet_y: float) -> None:
        """Create an explosion centred on the bullet's position and play the sound."""
        from src.bullet import BULLET_SIZE
        cx = bullet_x + BULLET_SIZE / 2
        cy = bullet_y + BULLET_SIZE / 2
        self._explosions.append(Explosion(cx, cy))
        if self._explode_sound:
            self._explode_sound.play()

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
    # Drawing
    # ------------------------------------------------------------------

    def _draw(self) -> None:
        self._camera.follow(self._player.x, self._player.y)
        cam_x, cam_y = self._camera.x, self._camera.y

        self._screen.fill(settings.DARK_BG)

        # --- clipped to field viewport ---
        self._screen.set_clip(self._field_rect)
        self._draw_ground(cam_x, cam_y)
        self._game_map.draw(self._screen, cam_x, cam_y, self._field_rect)
        self._buildings.draw_sprites(
            self._screen, cam_x, cam_y, self._field_rect, self._building_sheet,
            items_sheet=self._items_sheet,
            pop_sheet=self._pop_sheet,
        )
        self._draw_world_items(cam_x, cam_y)
        self._draw_player()
        self._draw_world_entity_list(self._bullets,    self._bullet_sheet)
        self._draw_world_entity_list(self._explosions, self._explosion_sheet)
        self._screen.set_clip(None)

        # --- unclipped ---
        self._buildings.draw_labels(self._screen, cam_x, cam_y, self._field_rect, self._font)
        self._hud.draw(self._screen, self._player)
        self._screen.blit(self._interface_img, (settings.PANEL_X, settings.PANEL_Y))
        self._minimap.draw(self._screen, self._player)
        self._draw_home_arrow()
        self._draw_health_bar()
        draw_inventory(
            self._screen, self._inventory,
            self._items_sheet, self._inv_selection_sheet, self._font,
        )
        self._draw_build_ui(cam_x, cam_y, self._field_rect)
        pygame.display.flip()

    def _build_ground_surf(self) -> pygame.Surface:
        """
        Pre-bake a surface one tile larger than the field in each axis so that
        any scroll offset [0, tile_w) × [0, tile_h) can be served with a single
        sub-rect blit instead of a nested loop of ~25 blits per frame.
        """
        tw  = self._ground_tile.get_width()
        th  = self._ground_tile.get_height()
        w   = settings.FIELD_WIDTH  + tw
        h   = settings.FIELD_HEIGHT + th
        surf = pygame.Surface((w, h)).convert()
        for y in range(0, h, th):
            for x in range(0, w, tw):
                surf.blit(self._ground_tile, (x, y))
        return surf

    def _draw_ground(self, cam_x: float, cam_y: float) -> None:
        tw     = self._ground_tile.get_width()
        th     = self._ground_tile.get_height()
        off_x  = round(cam_x) % tw
        off_y  = round(cam_y) % th
        self._screen.blit(
            self._ground_surf,
            (settings.FIELD_X, settings.FIELD_Y),
            pygame.Rect(off_x, off_y, settings.FIELD_WIDTH, settings.FIELD_HEIGHT),
        )

    def _draw_player(self) -> None:
        sx, sy = self._camera.to_screen(self._player.x, self._player.y)
        self._screen.blit(self._tank_frames[self._player.sprite_col], (sx, sy))

    def _draw_world_entity_list(
        self,
        entities: list,
        sheet:    pygame.Surface,
    ) -> None:
        """Blit all world entities that share a spritesheet.

        Entities must expose `.x`, `.y`, and `.sprite_rect` → (src_x, src_y, w, h).
        Replaces the former duplicated _draw_bullets / _draw_explosions methods.
        """
        for entity in entities:
            src_x, src_y, w, h = entity.sprite_rect
            sx, sy = self._camera.to_screen(entity.x, entity.y)
            self._screen.blit(sheet, (sx, sy), pygame.Rect(src_x, src_y, w, h))

    def _draw_home_arrow(self) -> None:
        dif_x = self._player.city_x - self._player.x
        dif_y = self._player.city_y - self._player.y
        frame = arrow_frame(dif_x, dif_y)
        self._screen.blit(
            self._arrows_sheet,
            (settings.ARROW_PANEL_X, settings.ARROW_PANEL_Y),
            pygame.Rect(frame * settings.ARROW_FRAME_W, 0,
                        settings.ARROW_FRAME_W, settings.ARROW_FRAME_H),
        )

    def _draw_health_bar(self) -> None:
        percent   = max(0.0, min(1.0, self._player.hp / float(settings.MAX_HEALTH)))
        height_px = int(percent * settings.HEALTH_MAX_H)
        if height_px <= 0:
            return
        dest_y = settings.HEALTH_BASE_Y - height_px
        self._screen.blit(
            self._health_sheet,
            (settings.HEALTH_PANEL_X, dest_y),
            pygame.Rect(0, 0, settings.HEALTH_W, height_px),
        )

    def _draw_build_ui(
        self,
        cam_x:      float,
        cam_y:      float,
        field_rect: pygame.Rect,
    ) -> None:
        """Draw build menu popup and placement ghost (both unclipped)."""
        self._build_menu.draw_placement_ghost(
            self._screen, cam_x, cam_y, field_rect,
            pygame.mouse.get_pos(), self._building_sheet,
        )
        self._build_menu.draw(
            self._screen, self._font,
            self._build_state.can_build,
            self._build_icons,
            self._build_state,
        )

    def _draw_world_items(self, cam_x: float, cam_y: float) -> None:
        """Draw all world items clipped to the field viewport."""
        for wi in self._world_items:
            cx, cy = wi.world_center
            sx = self._field_rect.x + int(cx - cam_x) - settings.ITEM_WORLD_SIZE // 2
            sy = self._field_rect.y + int(cy - cam_y) - settings.ITEM_WORLD_SIZE // 2

            src_x = wi.item_type * settings.ITEM_WORLD_SIZE
            src_y = settings.ITEM_WORLD_SRC_Y
            if wi.item_type == settings.ITEM_TYPE_ORB:
                src_y += wi.animation * settings.ITEM_WORLD_SIZE

            self._screen.blit(
                self._items_sheet,
                (sx, sy),
                pygame.Rect(src_x, src_y, settings.ITEM_WORLD_SIZE, settings.ITEM_WORLD_SIZE),
            )

    def _try_pickup(self) -> None:
        """Pick up the nearest world item within ITEM_PICKUP_RANGE tiles."""
        px = self._player.x + settings.TANK_FRAME_W / 2
        py = self._player.y + settings.TANK_FRAME_H / 2
        range_px = settings.ITEM_PICKUP_RANGE * settings.TILE_SIZE

        best = None
        best_dist = float("inf")
        for wi in self._world_items:
            cx, cy = wi.world_center
            dist = ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5
            if dist < range_px and dist < best_dist:
                best = wi
                best_dist = dist

        if best is None:
            return
        if self._inventory.pickup(best.item_type):
            if best.factory_ref is not None:
                best.factory_ref.world_item_count -= 1
            self._world_items.remove(best)
            if best.item_type == settings.ITEM_TYPE_ROCKET:
                self._player.bullet_type = 1

    def _try_drop(self) -> None:
        """Drop the currently selected item at the player's tile."""
        sel = self._inventory.selected_type
        if sel == -1 or self._inventory.counts[sel] <= 0:
            return
        if self._inventory.drop(sel):
            tx = int(self._player.x // settings.TILE_SIZE)
            ty = int(self._player.y // settings.TILE_SIZE)
            self._world_items.append(WorldItem(tile_x=tx, tile_y=ty, item_type=sel))
            if sel == settings.ITEM_TYPE_ROCKET and self._inventory.counts[sel] == 0:
                self._player.bullet_type = 0

    def _try_use_medkit(self) -> None:
        if self._inventory.counts[settings.ITEM_TYPE_MEDKIT] > 0:
            ItemEffects.use_medkit(self._player)
            self._inventory.drop(settings.ITEM_TYPE_MEDKIT)

    def _try_use_cloak(self) -> None:
        if self._inventory.counts[settings.ITEM_TYPE_CLOAK] > 0:
            ItemEffects.use_cloak(self._player)
            self._inventory.drop(settings.ITEM_TYPE_CLOAK)

    def _quit(self) -> None:
        pygame.quit()
