# ---------------------------------------------------------------------------
# settings.py — Global constants for Battle City
# ---------------------------------------------------------------------------

# Display
FPS           = 60

# Sprite dimensions (from original C++ source)
TANK_FRAME_W  = 48
TANK_FRAME_H  = 48
GROUND_TILE_W = 128
GROUND_TILE_H = 128

# Direction system: 0-31 clockwise, matching original C++ Direction field
#   0 = North, 8 = West, 16 = South, 24 = East
#   Sprite column = direction // 2  (16 unique angles across 32 directions)
NUM_DIRECTIONS  = 32
NUM_SPRITE_COLS = 16  # spritesheet columns = NUM_DIRECTIONS // 2

# Movement (original C++ uses MOVEMENT_SPEED_PLAYER = 0.38 * TimePassed)
MOVEMENT_SPEED = 220.0  # pixels per second (forward / backward)
TURN_INTERVAL  = 0.05   # seconds per direction step (50 ms, matches original)

# Colors
DARK_BG     = (20,  20,  25)
GRAY        = (80,  80,  80)
GREEN_LIGHT = (80,  170, 80)
HUD_BORDER  = (60,  70,  60)

# Playing field geometry (viewport window on screen)
FIELD_COLS   = 13
FIELD_ROWS   = 10
FIELD_WIDTH  = FIELD_COLS * TANK_FRAME_W
FIELD_HEIGHT = FIELD_ROWS * TANK_FRAME_H
FIELD_X      = 4
FIELD_Y      = 4

# Control panel (imgInterface.bmp = 200x430)
PANEL_GAP    = 8
PANEL_X      = FIELD_X + FIELD_WIDTH + PANEL_GAP
PANEL_Y      = FIELD_Y
PANEL_W      = 200
PANEL_H      = 430

# Screen dimensions derived from field + panel
SCREEN_WIDTH  = PANEL_X + PANEL_W + 4
SCREEN_HEIGHT = FIELD_Y + FIELD_HEIGHT + 4

# World map (512×512 tiles of 48×48 px each)
MAP_SIZE       = 512           # tiles per axis
TILE_SIZE      = TANK_FRAME_W  # 48 px — same as tank sprite size
MAP_PIXEL_SIZE = MAP_SIZE * TILE_SIZE  # 24576 px

# Tile type IDs (matching original CConstants.h)
# MAP_SQUARE_LAVA = 1, MAP_SQUARE_ROCK = 2  (note: NOT the intuitive order)
MAP_TILE_EMPTY = 0
MAP_TILE_LAVA  = 1
MAP_TILE_ROCK  = 2
MAP_TILE_CITY  = 3

# --- Home Arrow (imgArrows.bmp) ---
ARROW_FRAME_W    = 40                      # each of the 8 frames is 40×40 px
ARROW_FRAME_H    = 40
ARROW_NUM_FRAMES = 8
ARROW_PANEL_X    = PANEL_X + 5            # C++ MaxMapX + 5
ARROW_PANEL_Y    = PANEL_Y + 160          # C++ absolute Y = 160

# --- Health Bar (imgHealth.bmp) ---
MAX_HEALTH       = 40                      # C++ MAX_HEALTH = 40
HEALTH_PANEL_X   = PANEL_X + 137          # C++ MaxMapX + 137
HEALTH_BASE_Y    = PANEL_Y + 250          # C++ absolute Y baseline = 250
HEALTH_MAX_H     = 87                      # max pixel height of bar
HEALTH_W         = 38                      # fixed pixel width

# Damage values per bullet type (for future use)
DAMAGE_LASER     = 5
DAMAGE_ROCKET    = 8
DAMAGE_MINE      = 19
