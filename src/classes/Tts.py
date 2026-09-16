import os
import soundfile as sf

try:
    from kittentts import KittenTTS as KittenModel
    KITTENTTS_IMPORT_ERROR = None
except ImportError as exc:
    KittenModel = None
    KITTENTTS_IMPORT_ERROR = exc

from config import ROOT_DIR, get_tts_voice

KITTEN_MODEL = "KittenML/kitten-tts-mini-0.8"
KITTEN_SAMPLE_RATE = 24000

class TTS:
    def __init__(self) -> None:
        if KittenModel is None:
            raise RuntimeError(
                "KittenTTS is not available. MoneyPrinterV2 currently requires a "
                "Python 3.12 virtual environment for TTS support. Recreate your "
                "venv with 'py -3.12 -m venv venv' and reinstall requirements."
            ) from KITTENTTS_IMPORT_ERROR

        self._model = KittenModel(KITTEN_MODEL)
        self._voice = get_tts_voice()

    def synthesize(self, text, output_file=os.path.join(ROOT_DIR, ".mp", "audio.wav")):
        audio = self._model.generate(text, voice=self._voice)
        sf.write(output_file, audio, KITTEN_SAMPLE_RATE)
        return output_file
