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

# ---------------------------------------------------------------------------
# Build system — mirrors client/CConstants.h + server/CCity.cpp resetToDefault
# ---------------------------------------------------------------------------

# 26 buildable types, each identified by a 3-digit code
#   1xx = Factory  |  2xx = Hospital  |  3xx = House  |  4xx = Research
BUILDING_TYPES: list[int] = [
    200,  # 0  Hospital
    300,  # 1  House
    401,  # 2  Bazooka Research
    101,  # 3  Bazooka Factory
    409,  # 4  Turret Research
    109,  # 5  Turret Factory
    400,  # 6  Cloak Research
    100,  # 7  Cloak Factory
    402,  # 8  MedKit Research
    102,  # 9  MedKit Factory
    411,  # 10 Plasma Turret Research
    111,  # 11 Plasma Turret Factory
    404,  # 12 Mine Research
    104,  # 13 Mine Factory
    405,  # 14 Orb Research
    105,  # 15 Orb Factory
    403,  # 16 Time Bomb Research
    103,  # 17 Time Bomb Factory
    410,  # 18 Sleeper Research
    110,  # 19 Sleeper Factory
    408,  # 20 Wall Research
    108,  # 21 Wall Factory
    407,  # 22 DFG Research
    107,  # 23 DFG Factory
    406,  # 24 Flare Gun Research
    106,  # 25 Flare Gun Factory
]
NUM_BUILD_TYPES  = 26  # len(BUILDING_TYPES)

# Display names for each slot (matches C++ buildNames[])
BUILD_NAMES: list[str] = [
    "Hospital",
    "House",
    "Bazooka Research",
    "Bazooka Factory",
    "Turret Research",
    "Turret Factory",
    "Cloak Research",
    "Cloak Factory",
    "MedKit Research",
    "MedKit Factory",
    "Plasma Turret Research",
    "Plasma Turret Factory",
    "Mine Research",
    "Mine Factory",
    "Orb Research",
    "Orb Factory",
    "Time Bomb Research",
    "Time Bomb Factory",
    "Sleeper Research",
    "Sleeper Factory",
    "Wall Research",
    "Wall Factory",
    "DFG Research",
    "DFG Factory",
    "Flare Gun Research",
    "Flare Gun Factory",
]

# Icon frame index into imgBuildIcons.bmp (14 frames × 16 px each = 224 px wide)
BUILD_BUTTON: list[int] = [
    12,  # Hospital
    0,   # House
    2,   # Bazooka Research
    2,   # Bazooka Factory
    9,   # Turret Research
    9,   # Turret Factory
    1,   # Cloak Research
    1,   # Cloak Factory
    3,   # MedKit Research
    3,   # MedKit Factory
    10,  # Plasma Turret Research
    10,  # Plasma Turret Factory
    5,   # Mine Research
    5,   # Mine Factory
    6,   # Orb Research
    6,   # Orb Factory
    4,   # Time Bomb Research
    4,   # Time Bomb Factory
    8,   # Sleeper Research
    8,   # Sleeper Factory
    11,  # Wall Research
    11,  # Wall Factory
    8,   # DFG Research
    8,   # DFG Factory
    7,   # Flare Gun Research
    7,   # Flare Gun Factory
]

# Build prerequisite tree — 12 item slots (k=0..11) each paired with a Research+Factory.
# BUILD_TREE[k] = prerequisite item slot index, or -1 (no prereq, available from start).
# Slot ordering: rocket(0), turret(1), cloak(2), medkit(3), plasma(4), mine(5),
#                orb(6), bomb(7), sleeper(8), wall(9), dfg(10), flare(11)
BUILD_TREE: list[int] = [-1, -1, 0, 0, 1, 1, 2, 2, 4, 4, 5, 6]

# Economy
COST_BUILDING    = 500_000
STARTING_CASH    = 95_000_000
RESEARCH_TIMER   = 10.0        # seconds until research completes

# Build-icon sheet (imgBuildIcons.bmp: 224×16 px, 14 icons of 16×16)
BUILD_ICON_W         = 16
BUILD_ICON_H         = 16
BUILD_ICON_DEMOLISH  = 13  # frame index for the Demolish icon

# Build button hit-area on imgInterface.bmp (relative to PANEL_X, PANEL_Y)
BUILD_BTN_REL_X  = 126
BUILD_BTN_REL_Y  = 396
BUILD_BTN_W      = 64
BUILD_BTN_H      = 22

# Build-menu popup anchor (opened by Build button)
BUILD_MENU_ANCHOR_X = FIELD_X + FIELD_WIDTH - 200   # left edge of popup
BUILD_MENU_ANCHOR_Y = FIELD_Y + FIELD_HEIGHT - 16   # bottom anchor (menu grows up)
