import os
import asyncio
import tempfile
import soundfile as sf
import numpy as np

import edge_tts

from config import ROOT_DIR, get_tts_voice

# ---------------------------------------------------------------------------
# Voice mapping: config'deki kısa isim → Edge TTS ses adı
# Yeni ses eklemek için buraya satır ekleyin.
# ---------------------------------------------------------------------------
VOICE_MAP = {
    # Türkçe
    "Ahmet":  "tr-TR-AhmetNeural",   # erkek
    "Emel":   "tr-TR-EmelNeural",    # kadın
    # İngilizce
    "Guy":    "en-US-GuyNeural",     # erkek
    "Aria":   "en-US-AriaNeural",    # kadın
    "Jenny":  "en-US-JennyNeural",   # kadın
    "Jasper": "en-US-GuyNeural",     # eski addan fallback
    # Varsayılan fallback
    "default": "en-US-GuyNeural",
}


def _resolve_voice(voice_name: str) -> str:
    """Kısa adı Edge TTS ses adına çevirir.
    Tam ad (örn. 'tr-TR-AhmetNeural') doğrudan kullanılır."""
    if "-" in voice_name:          # zaten tam format
        return voice_name
    return VOICE_MAP.get(voice_name, VOICE_MAP["default"])


class TTS:
    def __init__(self) -> None:
        self._voice = _resolve_voice(get_tts_voice())

    def synthesize(self, text: str, output_file: str = os.path.join(ROOT_DIR, ".mp", "audio.wav")) -> str:
        """
        Edge TTS ile yüksek kaliteli ses üretir ve WAV olarak kaydeder.

        Args:
            text (str): Seslendirilen metin
            output_file (str): Çıktı WAV yolu

        Returns:
            output_file (str): Kaydedilen dosya yolu
        """
        async def _run():
            communicate = edge_tts.Communicate(text, self._voice)
            # Önce geçici MP3'e yaz, sonra WAV'a dönüştür
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

        # MP3 → WAV dönüşümü (yüksek kalite: 44100 Hz, 16-bit)
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_mp3(tmp_path)
            audio = audio.set_frame_rate(44100).set_sample_width(2)  # 16-bit
            audio.export(output_file, format="wav")
        except Exception:
            # pydub yoksa ffmpeg ile dönüştür
            import subprocess
            subprocess.run(
                ["ffmpeg", "-y", "-i", tmp_path, "-ar", "44100", "-acodec", "pcm_s16le", output_file],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        os.remove(tmp_path)
        return output_file
