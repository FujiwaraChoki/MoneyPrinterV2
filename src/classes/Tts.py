import os
import asyncio
import tempfile
import soundfile as sf
import numpy as np

import edge_tts

from config import ROOT_DIR, get_tts_voice, get_tts_rate, get_tts_pitch

# ---------------------------------------------------------------------------
# Voice mapping: short name in config → Edge TTS voice name
# Add a new line here to register a new voice.
# ---------------------------------------------------------------------------
VOICE_MAP = {
    # English — High Quality
    "Ava":    "en-US-AvaMultilingualNeural",      # female, most natural
    "Andrew": "en-US-AndrewMultilingualNeural",    # male, deep & natural
    "Guy":    "en-US-GuyNeural",                   # male, classic
    "Aria":   "en-US-AriaNeural",                  # female
    "Jenny":  "en-US-JennyNeural",                 # female
    "Ryan":   "en-GB-RyanNeural",                  # male, British
    # Turkish
    "Ahmet":  "tr-TR-AhmetNeural",                 # male
    "Emel":   "tr-TR-EmelNeural",                  # female
    # Legacy fallbacks
    "Jasper": "en-US-GuyNeural",
    "default": "en-US-AndrewMultilingualNeural",
}


def _resolve_voice(voice_name: str) -> str:
    """Resolves short name to Edge TTS voice name.
    Full name (e.g. 'tr-TR-AhmetNeural') is used directly."""
    if "-" in voice_name:          # zaten tam format
        return voice_name
    return VOICE_MAP.get(voice_name, VOICE_MAP["default"])


class TTS:
    def __init__(self, rate: str = None, pitch: str = None) -> None:
        self._voice = _resolve_voice(get_tts_voice())
        self._rate = rate or get_tts_rate()
        self._pitch = pitch or get_tts_pitch()

    def synthesize(self, text: str, output_file: str = os.path.join(ROOT_DIR, ".mp", "audio.wav")) -> str:
        """
        Synthesizes high-quality speech using Edge TTS and saves as WAV.

        Args:
            text (str): Text to synthesize
            output_file (str): Output WAV path

        Returns:
            output_file (str): Path to saved file
        """
        async def _run():
            communicate = edge_tts.Communicate(
                text, self._voice,
                rate=self._rate, pitch=self._pitch
            )
            # First write to temp MP3, then convert to WAV
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name

            await communicate.save(tmp_path)
            return tmp_path

        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError
            tmp_path = loop.run_until_complete(_run())
        except RuntimeError:
            tmp_path = asyncio.run(_run())

        # MP3 → WAV conversion (high quality: 44100 Hz, 16-bit)
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_mp3(tmp_path)
            audio = audio.set_frame_rate(44100).set_sample_width(2)  # 16-bit
            audio.export(output_file, format="wav")
        except Exception:
            # Fallback to ffmpeg if pydub is not available
            import subprocess
            subprocess.run(
                ["ffmpeg", "-y", "-i", tmp_path, "-ar", "44100", "-acodec", "pcm_s16le", output_file],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        os.remove(tmp_path)
        return output_file
