import os
import random
import zipfile
import requests
import platform

from pathlib import Path
from status import *
from config import *

DEFAULT_SONG_ARCHIVE_URLS = []


def close_running_selenium_instances() -> None:
    """
    Closes any running Selenium instances.

    Returns:
        None
    """
    try:
        info(" => Closing running Selenium instances...")

        # Kill all running Firefox instances
        if platform.system() == "Windows":
            os.system("taskkill /f /im firefox.exe")
        else:
            os.system("pkill firefox")

        success(" => Closed running Selenium instances.")

    except Exception as e:
        error(f"Error occurred while closing running Selenium instances: {str(e)}")


def build_url(youtube_video_id: str) -> str:
    """
    Builds the URL to the YouTube video.

    Args:
        youtube_video_id (str): The YouTube video ID.

    Returns:
        url (str): The URL to the YouTube video.
    """
    return f"https://www.youtube.com/watch?v={youtube_video_id}"


def rem_temp_files() -> None:
    """
    Removes temporary files in the `.mp` directory.

    Returns:
        None
    """
    mp_dir = Path(ROOT_DIR) / ".mp"

    if not mp_dir.exists():
        return

    for file in mp_dir.iterdir():
        if file.is_file() and not file.suffix == ".json":
            file.unlink()


def fetch_songs() -> None:
    """
    Downloads songs into songs/ directory to use with generated videos.

    Returns:
        None
    """
    try:
        info(f" => Fetching songs...")

        files_dir = Path(ROOT_DIR) / "Songs"
        if not files_dir.exists():
            files_dir.mkdir()
            if get_verbose():
                info(f" => Created directory: {files_dir}")
        else:
            existing_audio_files = [
                f
                for f in files_dir.iterdir()
                if f.is_file()
                and f.suffix.lower() in (".mp3", ".wav", ".m4a", ".aac", ".ogg")
            ]
            if len(existing_audio_files) > 0:
                return

        configured_url = get_zip_url().strip()
        download_urls = [configured_url] if configured_url else []
        download_urls.extend(DEFAULT_SONG_ARCHIVE_URLS)

        archive_path = files_dir / "songs.zip"
        downloaded = False

        for download_url in download_urls:
            try:
                response = requests.get(download_url, timeout=60)
                response.raise_for_status()

                archive_path.write_bytes(response.content)

                SAFE_EXTENSIONS = (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac")
                with zipfile.ZipFile(archive_path, "r") as zf:
                    for member in zf.namelist():
                        basename = os.path.basename(member)
                        if not basename or not basename.lower().endswith(SAFE_EXTENSIONS):
                            warning(f"Skipping non-audio file in archive: {member}")
                            continue
                        if ".." in member or member.startswith("/"):
                            warning(f"Skipping suspicious path in archive: {member}")
                            continue
                        zf.extract(member, files_dir)

                downloaded = True
                break
            except Exception as err:
                warning(f"Failed to fetch songs from {download_url}: {err}")

        if not downloaded:
            raise RuntimeError(
                "Could not download a valid songs archive from any configured URL"
            )

        # Remove the zip file
        if archive_path.exists():
            archive_path.unlink()

        success(" => Downloaded Songs to ../Songs.")

    except Exception as e:
        error(f"Error occurred while fetching songs: {str(e)}")


def choose_random_song() -> str:
    """
    Chooses a random song from the songs/ directory.

    Returns:
        str: The path to the chosen song.
    """
    try:
        songs_dir = Path(ROOT_DIR) / "Songs"
        songs = [
            f
            for f in songs_dir.iterdir()
            if f.is_file()
            and f.suffix.lower() in (".mp3", ".wav", ".m4a", ".aac", ".ogg")
        ]
        if len(songs) == 0:
            raise RuntimeError("No audio files found in Songs directory")
        song = random.choice(songs)
        success(f" => Chose song: {song.name}")
        return str(song)
    except Exception as e:
        error(f"Error occurred while choosing random song: {str(e)}")
        raise
