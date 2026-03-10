"""
src/building.py — City center buildings.

Every map.dat tile of type 3 spawns a city center (row 0 of imgBuildings.bmp).

Spritesheet layout (imgBuildings.bmp, 432×723 px):
  3 cols × 5 rows of 144×144 px frames.
  Row 0 (by=  0) = City Center   ← only row used here
  Row 1 (by=144) = Factory
  Row 2 (by=288) = House
  Row 3 (by=432) = Hospital
  Row 4 (by=576) = Research
  Animation: bX = (anim_step // 2) * 144  →  3 unique frames, each held 2 steps × 500 ms

World-space placement (Python standard coords, Y increases downward):
  Anchor tile = map.dat (tile_x, tile_y).
  Image top-left placed at ((tile_x-2)*48, (tile_y-2)*48).
  3×3 tile footprint covers tile_x-2 … tile_x  (X),  tile_y-2 … tile_y  (Y).

Collision (mirrors C++ CCollision.cpp city-center special case):
  Blocked  : top 2 rows of footprint  (tile_y-2, tile_y-1)  — full 3 cols each
  Walkable : bottom row               (tile_y)               — player can enter here
"""

import random
import pygame
import settings

# ------------------------------------------------------------------
# City names — verbatim from C++ Structs.cpp CityList[] (indices 0–63)
# ------------------------------------------------------------------
CITY_NAMES: list[str] = [
    "Balkh", "Iqaluit", "Reykjavik", "Jumarity", "Helsinki", "Copenhagen",
    "Kiev", "Barentsburg", "Nunivak", "Algiers", "Paga Pago", "St. Johns",
    "Parana", "San Salvador de Jujuy", "Tallinn", "Bergen", "Bangui",
    "Annaba", "Andorra-la-Vella", "Bahia Blanca", "Posadas", "Santa Fe",
    "Buckland", "Kabul", "Lahij", "Banta", "Benguela", "Buenos Aires",
    "Resistencia", "Santiago del Estero", "Armidale", "Harbin", "Fajardo",
    "Blida", "Huambo", "Cordoba", "Rio Cuarto", "Kumayari", "Kuala Lumpur",
    "Mango", "Arequipa", "Constantine", "Luanda", "Corrientes", "Rosario",
    "Kirovakan", "Jakarta", "Skopje", "Bogota", "Canberra", "Pretoria",
    "Maracay", "Cambridge", "Laketown", "Hanoi", "Bishkek", "Tirana",
    "Dakar", "Aquin", "Bismarck", "Albany", "Manukau", "Utrecht",
    "Admin Inn",
]  # 64 entries

_ANIM_INTERVAL  = 0.5   # seconds per animation step (500 ms, matches C++)
_NUM_ANIM_STEPS = 6     # internal steps; 3 unique frames (pairs 0-1, 2-3, 4-5)
_BSIZE          = 144   # building sprite size in pixels (3 × 48)


class Building:
    """One city center building."""

    def __init__(self, tile_x: int, tile_y: int, city_index: int) -> None:
        self.tile_x     = tile_x
        self.tile_y     = tile_y
        self.city_index = city_index
        self._anim_step  = random.randint(0, _NUM_ANIM_STEPS - 1)
        self._anim_timer = 0.0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        if 0 <= self.city_index < len(CITY_NAMES):
            return CITY_NAMES[self.city_index]
        return f"City {self.city_index}"

    @property
    def world_x(self) -> int:
        """World pixel X of the image top-left corner."""
        return (self.tile_x - 2) * settings.TILE_SIZE

    @property
    def world_y(self) -> int:
        """World pixel Y of the image top-left corner."""
        return (self.tile_y - 2) * settings.TILE_SIZE

    @property
    def sprite_src(self) -> pygame.Rect:
        """Source rect into imgBuildings.bmp for the current animation frame."""
        src_x = (self._anim_step // 2) * _BSIZE
        return pygame.Rect(src_x, 0, _BSIZE, _BSIZE)  # row 0 = City Center

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        self._anim_timer += dt
        if self._anim_timer >= _ANIM_INTERVAL:
            self._anim_timer -= _ANIM_INTERVAL
            self._anim_step   = (self._anim_step + 1) % _NUM_ANIM_STEPS


class BuildingManager:
    """Loads, animates, draws, and provides collision for all city centers."""

    def __init__(self, map_data: list[list[int]]) -> None:
        self._buildings: list[Building]          = []
        self._blocked:   set[tuple[int, int]]    = set()
        self._load(map_data)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        for b in self._buildings:
            b.update(dt)

    def draw_sprites(
        self,
        screen:     pygame.Surface,
        cam_x:      float,
        cam_y:      float,
        field_rect: pygame.Rect,
        sheet:      pygame.Surface,
    ) -> None:
        """Draw building sprites (call inside screen clip rect)."""
        for b, sx, sy in self._visible_buildings(cam_x, cam_y, field_rect):
            screen.blit(sheet, (sx, sy), b.sprite_src)

    def draw_labels(
        self,
        screen:     pygame.Surface,
        cam_x:      float,
        cam_y:      float,
        field_rect: pygame.Rect,
        font:       pygame.font.Font,
    ) -> None:
        """Draw city name labels above each visible building (call with no clip)."""
        for b, sx, sy in self._visible_buildings(cam_x, cam_y, field_rect):
            label = font.render(b.name, True, (255, 255, 160))
            lx = sx + (_BSIZE - label.get_width()) // 2
            ly = sy - label.get_height() - 2
            screen.blit(label, (lx, ly))

    def is_tile_blocked(self, tx: int, ty: int) -> bool:
        return (tx, ty) in self._blocked

    def random_spawn(self) -> tuple[float, float]:
        """World pixel position at the centre of a random city's walkable row."""
        b = random.choice(self._buildings)
        # Centre-X tile of walkable bottom row = tile_x-1; bottom row Y = tile_y
        return float((b.tile_x - 1) * settings.TILE_SIZE), float(b.tile_y * settings.TILE_SIZE)

    @property
    def buildings(self) -> list[Building]:
        return self._buildings

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _visible_buildings(
        self,
        cam_x:      float,
        cam_y:      float,
        field_rect: pygame.Rect,
    ):
        """Yield (building, screen_x, screen_y) for each building in the viewport."""
        for b in self._buildings:
            sx = field_rect.x + b.world_x - int(cam_x)
            sy = field_rect.y + b.world_y - int(cam_y)
            if sx + _BSIZE <= field_rect.x or sx >= field_rect.right:
                continue
            if sy + _BSIZE <= field_rect.y or sy >= field_rect.bottom:
                continue
            yield b, sx, sy

    def _load(self, map_data: list[list[int]]) -> None:
        size      = settings.MAP_SIZE
        cit_index = 63  # C++ scan: outer j=Y, inner i=X, citIndex starts at 63

        for j in range(size):       # Y (outer, matches C++)
            for i in range(size):   # X (inner, matches C++)
                if map_data[i][j] == settings.MAP_TILE_CITY:
                    b = Building(i, j, cit_index)
                    self._buildings.append(b)
                    self._register_blocked(b)
                    cit_index -= 1
                    if cit_index < 0:
                        break
            if cit_index < 0:
                break

        print(f"[BuildingManager] Loaded {len(self._buildings)} city centers")

    def _register_blocked(self, b: Building) -> None:
        """
        Block the top 2 tile rows of the 3×3 footprint.
        Footprint X: tile_x-2, tile_x-1, tile_x  (dx = -2 … 0)
        Footprint Y: tile_y-2, tile_y-1, tile_y
          Blocked  → dy = -2, -1  (top 2 rows in Python screen space)
          Walkable → dy =  0      (bottom row = entrance)
        """
        for dx in range(-2, 1):    # -2, -1, 0
            for dy in range(-2, 0):  # -2, -1  (NOT 0)
                self._blocked.add((b.tile_x + dx, b.tile_y + dy))
