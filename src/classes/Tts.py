import os
import asyncio
import soundfile as sf

from config import ROOT_DIR, get_tts_voice, get_tts_provider

KITTEN_MODEL = "KittenML/kitten-tts-mini-0.8"
KITTEN_SAMPLE_RATE = 24000

# Well-known KittenTTS voices
KITTEN_VOICES = [
    {"name": "Bella", "gender": "Female", "language": "en"},
    {"name": "Jasper", "gender": "Male", "language": "en"},
    {"name": "Luna", "gender": "Female", "language": "en"},
    {"name": "Bruno", "gender": "Male", "language": "en"},
    {"name": "Rosie", "gender": "Female", "language": "en"},
    {"name": "Hugo", "gender": "Male", "language": "en"},
    {"name": "Kiki", "gender": "Female", "language": "en"},
    {"name": "Leo", "gender": "Male", "language": "en"},
]


class TTS:
    """Multi-provider Text-to-Speech engine.

    Supported providers:
        - edge_tts  : Microsoft Edge TTS (300+ voices, free, high quality)
        - kitten_tts: KittenTTS local model (8 English voices)
    """

    def __init__(self, provider: str = None, voice: str = None) -> None:
        self._provider = (provider or get_tts_provider()).lower()
        self._voice = voice or get_tts_voice()

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def voice(self) -> str:
        return self._voice

    # ------------------------------------------------------------------
    # Voice listing
    # ------------------------------------------------------------------

    @staticmethod
    def list_voices(provider: str = None, language_filter: str = None) -> list[dict]:
        """List available voices for a provider, optionally filtered by language prefix.

        Args:
            provider: TTS provider name. Defaults to config value.
            language_filter: ISO language prefix to filter by (e.g. "en", "es").

        Returns:
            List of voice dicts with keys: name, gender, language, friendly_name.
        """
        provider = (provider or get_tts_provider()).lower()

        if provider == "edge_tts":
            return TTS._list_edge_voices(language_filter)
        if provider == "kitten_tts":
            return TTS._list_kitten_voices(language_filter)
        return []

    @staticmethod
    def _list_kitten_voices(language_filter: str = None) -> list[dict]:
        voices = []
        for v in KITTEN_VOICES:
            if language_filter and not v["language"].startswith(language_filter.lower()):
                continue
            voices.append({**v, "friendly_name": v["name"]})
        return voices

    @staticmethod
    def _list_edge_voices(language_filter: str = None) -> list[dict]:
        try:
            import edge_tts
        except ImportError:
            return []

        raw_voices = asyncio.run(edge_tts.list_voices())
        result = []
        for v in raw_voices:
            locale = v.get("Locale", "")
            if language_filter and not locale.lower().startswith(language_filter.lower()):
                continue
            result.append({
                "name": v["ShortName"],
                "gender": v.get("Gender", "Unknown"),
                "language": locale,
                "friendly_name": v.get("FriendlyName", v["ShortName"]),
            })
        return result

    # ------------------------------------------------------------------
    # Synthesis
    # ------------------------------------------------------------------

    def synthesize(self, text: str, output_file: str = None) -> str:
        """Synthesize text to an audio file.

        Args:
            text: The text to speak.
            output_file: Desired output path (WAV). The actual path may differ
                         depending on the provider's native format.

        Returns:
            The path to the generated audio file.
        """
        if output_file is None:
            output_file = os.path.join(ROOT_DIR, ".mp", "audio.wav")

        if self._provider == "edge_tts":
            return self._synthesize_edge(text, output_file)
        return self._synthesize_kitten(text, output_file)

    def _synthesize_kitten(self, text: str, output_file: str) -> str:
        from kittentts import KittenTTS as KittenModel

        model = KittenModel(KITTEN_MODEL)
        audio = model.generate(text, voice=self._voice)
        sf.write(output_file, audio, KITTEN_SAMPLE_RATE)
        return output_file

    def _synthesize_edge(self, text: str, output_file: str) -> str:
        try:
            import edge_tts
        except ImportError:
            raise ImportError(
                "edge-tts is not installed. Run: pip install edge-tts"
            )

        # Edge TTS outputs MP3 natively
        mp3_path = os.path.splitext(output_file)[0] + ".mp3"
        communicate = edge_tts.Communicate(text, self._voice)
        asyncio.run(communicate.save(mp3_path))

        # Return MP3 directly — MoviePy and Whisper both support it
        return mp3_path
