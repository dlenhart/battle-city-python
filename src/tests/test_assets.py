"""Tests for src/assets.py — Asset discovery and loading helpers."""

import os
import sys
import pytest
import settings
from src.assets import find_asset, require_asset, optional_asset


# ------------------------------------------------------------------
# find_asset
# ------------------------------------------------------------------

class TestFindAsset:
    def test_finds_known_image(self):
        path = find_asset("imgTanks.bmp")
        assert path is not None
        assert os.path.isfile(path)

    def test_finds_known_sound(self):
        path = find_asset("engine.wav")
        assert path is not None
        assert os.path.isfile(path)

    def test_finds_map_dat(self):
        path = find_asset("map.dat")
        assert path is not None
        assert os.path.isfile(path)

    def test_returns_none_for_missing_file(self):
        path = find_asset("does_not_exist_xyzzy.bmp")
        assert path is None

    def test_returned_path_ends_with_filename(self):
        path = find_asset("imgGround.bmp")
        assert path is not None
        assert path.endswith("imgGround.bmp")


# ------------------------------------------------------------------
# require_asset
# ------------------------------------------------------------------

class TestRequireAsset:
    def test_returns_path_for_existing_file(self):
        path = require_asset("imgTanks.bmp")
        assert path is not None
        assert os.path.isfile(path)

    def test_exits_on_missing_file(self):
        with pytest.raises(SystemExit):
            require_asset("totally_missing_asset_xyzzy.wav")

    def test_prints_loading_message(self, capsys):
        require_asset("imgTanks.bmp")
        out = capsys.readouterr().out
        assert "imgTanks.bmp" in out


# ------------------------------------------------------------------
# optional_asset
# ------------------------------------------------------------------

class TestOptionalAsset:
    def test_returns_path_for_existing_file(self):
        path = optional_asset("engine.wav")
        assert path is not None
        assert os.path.isfile(path)

    def test_returns_none_for_missing_file(self):
        path = optional_asset("missing_xyzzy.wav")
        assert path is None

    def test_does_not_exit_on_missing_file(self):
        # Should not raise SystemExit
        optional_asset("missing_xyzzy.wav")

    def test_prints_loading_message_on_success(self, capsys):
        optional_asset("engine.wav")
        out = capsys.readouterr().out
        assert "engine.wav" in out

    def test_prints_warning_on_missing_file(self, capsys):
        optional_asset("missing_xyzzy.wav")
        out = capsys.readouterr().out
        assert "WARNING" in out or "missing_xyzzy.wav" in out

    def test_custom_warning_printed_on_missing(self, capsys):
        optional_asset("missing_xyzzy.wav", warning="custom warning message")
        out = capsys.readouterr().out
        assert "custom warning message" in out


# ------------------------------------------------------------------
# load_map_data
# ------------------------------------------------------------------

class TestLoadMapData:
    def test_returns_correct_dimensions(self):
        from src.assets import load_map_data
        path = find_asset("map.dat")
        data = load_map_data(path)
        assert len(data) == settings.MAP_SIZE
        assert len(data[0]) == settings.MAP_SIZE

    def test_tile_values_in_valid_range(self):
        from src.assets import load_map_data
        path = find_asset("map.dat")
        data = load_map_data(path)
        valid = {settings.MAP_TILE_EMPTY, settings.MAP_TILE_LAVA,
                 settings.MAP_TILE_ROCK,  settings.MAP_TILE_CITY}
        for col in data:
            for val in col:
                assert val in valid, f"Unexpected tile value: {val}"

    def test_map_contains_cities(self):
        from src.assets import load_map_data
        path = find_asset("map.dat")
        data = load_map_data(path)
        cities = sum(1 for col in data for v in col if v == settings.MAP_TILE_CITY)
        assert cities > 0

    def test_map_contains_rocks(self):
        from src.assets import load_map_data
        path = find_asset("map.dat")
        data = load_map_data(path)
        rocks = sum(1 for col in data for v in col if v == settings.MAP_TILE_ROCK)
        assert rocks > 0


# ------------------------------------------------------------------
# load_tile_sheet (colorkey detection)
# ------------------------------------------------------------------

class TestLoadTileSheet:
    def test_lava_sheet_loads(self):
        from src.assets import load_tile_sheet
        import pygame
        sheet = load_tile_sheet(find_asset("imgLava.bmp"))
        assert isinstance(sheet, pygame.Surface)

    def test_rocks_sheet_loads(self):
        from src.assets import load_tile_sheet
        import pygame
        sheet = load_tile_sheet(find_asset("imgRocks.bmp"))
        assert isinstance(sheet, pygame.Surface)

    def test_lava_has_colorkey(self):
        from src.assets import load_tile_sheet
        sheet = load_tile_sheet(find_asset("imgLava.bmp"))
        assert sheet.get_colorkey() is not None

    def test_rocks_has_no_colorkey(self):
        from src.assets import load_tile_sheet
        sheet = load_tile_sheet(find_asset("imgRocks.bmp"))
        assert sheet.get_colorkey() is None


# ------------------------------------------------------------------
# load_sound
# ------------------------------------------------------------------

class TestLoadSound:
    def test_returns_none_for_none_path(self):
        from src.assets import load_sound
        assert load_sound(None) is None

    def test_loads_valid_wav(self):
        from src.assets import load_sound
        import pygame
        path = find_asset("engine.wav")
        sound = load_sound(path, volume=0.5)
        assert isinstance(sound, pygame.mixer.Sound)
