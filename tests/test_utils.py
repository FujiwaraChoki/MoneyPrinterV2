import os
import pytest

import utils
import config


@pytest.fixture
def utils_env(patch_root_dir):
    """Patches ROOT_DIR in utils module."""
    original = utils.ROOT_DIR
    utils.ROOT_DIR = str(patch_root_dir)
    yield patch_root_dir
    utils.ROOT_DIR = original


class TestBuildUrl:
    def test_build_url(self):
        url = utils.build_url("abc123")
        assert url == "https://www.youtube.com/watch?v=abc123"

    def test_build_url_with_special_chars(self):
        url = utils.build_url("a-B_c")
        assert url == "https://www.youtube.com/watch?v=a-B_c"


class TestRemTempFiles:
    def test_removes_non_json_files(self, utils_env):
        mp_dir = os.path.join(str(utils_env), ".mp")

        # Create test files
        (open(os.path.join(mp_dir, "temp.wav"), "w")).close()
        (open(os.path.join(mp_dir, "temp.png"), "w")).close()
        (open(os.path.join(mp_dir, "cache.json"), "w")).close()

        utils.rem_temp_files()

        remaining = os.listdir(mp_dir)
        assert "cache.json" in remaining
        assert "temp.wav" not in remaining
        assert "temp.png" not in remaining

    def test_keeps_json_files(self, utils_env):
        mp_dir = os.path.join(str(utils_env), ".mp")
        (open(os.path.join(mp_dir, "youtube.json"), "w")).close()
        (open(os.path.join(mp_dir, "twitter.json"), "w")).close()

        utils.rem_temp_files()

        remaining = os.listdir(mp_dir)
        assert "youtube.json" in remaining
        assert "twitter.json" in remaining


class TestChooseRandomSong:
    def test_raises_when_no_songs(self, utils_env):
        songs_dir = os.path.join(str(utils_env), "Songs")
        os.makedirs(songs_dir, exist_ok=True)

        with pytest.raises(RuntimeError, match="No audio files found"):
            utils.choose_random_song()

    def test_returns_song_path(self, utils_env):
        songs_dir = os.path.join(str(utils_env), "Songs")
        os.makedirs(songs_dir, exist_ok=True)
        song_path = os.path.join(songs_dir, "test.mp3")
        with open(song_path, "w") as f:
            f.write("fake audio")

        result = utils.choose_random_song()
        assert result.endswith("test.mp3")
        assert os.path.isabs(result)
