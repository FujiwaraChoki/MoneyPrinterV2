import os
import random
import zipfile
import requests
import platform

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
        info(" => Cerrando instancias de Selenium en ejecución...")

        # Kill all running Firefox instances
        if platform.system() == "Windows":
            os.system("taskkill /f /im firefox.exe")
        else:
            os.system("pkill firefox")

        success(" => Instancias de Selenium cerradas.")

    except Exception as e:
        error(f"Error al cerrar instancias de Selenium en ejecución: {str(e)}")


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
    # Path to the `.mp` directory
    mp_dir = os.path.join(ROOT_DIR, ".mp")

    files = os.listdir(mp_dir)

    for file in files:
        if not file.endswith(".json"):
            os.remove(os.path.join(mp_dir, file))


def fetch_songs() -> None:
    """
    Downloads songs into songs/ directory to use with geneated videos.

    Returns:
        None
    """
    try:
        info(f" => Descargando canciones...")

        files_dir = os.path.join(ROOT_DIR, "Songs")
        if not os.path.exists(files_dir):
            os.mkdir(files_dir)
            if get_verbose():
                info(f" => Directorio creado: {files_dir}")
        else:
            existing_audio_files = [
                name
                for name in os.listdir(files_dir)
                if os.path.isfile(os.path.join(files_dir, name))
                and name.lower().endswith((".mp3", ".wav", ".m4a", ".aac", ".ogg"))
            ]
            if len(existing_audio_files) > 0:
                return

        configured_url = get_zip_url().strip()
        download_urls = [configured_url] if configured_url else []
        download_urls.extend(DEFAULT_SONG_ARCHIVE_URLS)

        archive_path = os.path.join(files_dir, "songs.zip")
        downloaded = False

        for download_url in download_urls:
            try:
                response = requests.get(download_url, timeout=60)
                response.raise_for_status()

                with open(archive_path, "wb") as file:
                    file.write(response.content)

                SAFE_EXTENSIONS = (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac")
                with zipfile.ZipFile(archive_path, "r") as zf:
                    for member in zf.namelist():
                        basename = os.path.basename(member)
                        if not basename or not basename.lower().endswith(SAFE_EXTENSIONS):
                            warning(f"Omitiendo archivo no-audio en el paquete: {member}")
                            continue
                        if ".." in member or member.startswith("/"):
                            warning(f"Omitiendo ruta sospechosa en el paquete: {member}")
                            continue
                        zf.extract(member, files_dir)

                downloaded = True
                break
            except Exception as err:
                warning(f"Error al descargar canciones desde {download_url}: {err}")

        if not downloaded:
            raise RuntimeError(
                "No se pudo descargar un paquete válido de canciones desde ninguna URL configurada"
            )

        # Remove the zip file
        if os.path.exists(archive_path):
            os.remove(archive_path)

        success(" => Canciones descargadas en ../Songs.")

    except Exception as e:
        error(f"Error al descargar canciones: {str(e)}")


def choose_random_song() -> str:
    """
    Chooses a random song from the songs/ directory.

    Returns:
        str: The path to the chosen song.
    """
    try:
        songs_dir = os.path.join(ROOT_DIR, "Songs")
        songs = [
            name
            for name in os.listdir(songs_dir)
            if os.path.isfile(os.path.join(songs_dir, name))
            and name.lower().endswith((".mp3", ".wav", ".m4a", ".aac", ".ogg"))
        ]
        if len(songs) == 0:
            raise RuntimeError("No se encontraron archivos de audio en el directorio Songs")
        song = random.choice(songs)
        success(f" => Canción elegida: {song}")
        return os.path.join(ROOT_DIR, "Songs", song)
    except Exception as e:
        error(f"Error al elegir canción aleatoria: {str(e)}")
        raise
