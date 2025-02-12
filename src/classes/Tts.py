import os
import sys
import site

from config import ROOT_DIR
from TTS.utils.manage import ModelManager
from TTS.utils.synthesizer import Synthesizer

class TTS:
    """
    Class for Text-to-Speech using Coqui TTS.
    """
    def __init__(self) -> None:
        """
        Initializes the TTS class.

        Returns:
            None
        """
        # Detect virtual environment site packages
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            # We're in a virtual environment
            site_packages = site.getsitepackages()[0]
        else:
            # We're not in a virtual environment, use the user's site packages
            site_packages = site.getusersitepackages()

        # Path to the .models.json file
        models_json_path = os.path.join(
            site_packages,
            "TTS",
            ".models.json",
        )

        # Create directory if it doesn't exist
        tts_dir = os.path.dirname(models_json_path)
        if not os.path.exists(tts_dir):
            os.makedirs(tts_dir)

        # Initialize the ModelManager
        self._model_manager = ModelManager(models_json_path)

        # Download tts_models/en/ljspeech/fast_pitch
        self._model_path, self._config_path, self._model_item = \
            self._model_manager.download_model("tts_models/en/ljspeech/tacotron2-DDC_ph")

        # Download vocoder_models/en/ljspeech/hifigan_v2 as our vocoder
        voc_path, voc_config_path, _ = self._model_manager. \
            download_model("vocoder_models/en/ljspeech/univnet")
        
        # Initialize the Synthesizer
        self._synthesizer = Synthesizer(
            tts_checkpoint=self._model_path,
            tts_config_path=self._config_path,
            vocoder_checkpoint=voc_path,
            vocoder_config=voc_config_path
        )

    @property
    def synthesizer(self) -> Synthesizer:
        """
        Returns the synthesizer.

        Returns:
            Synthesizer: The synthesizer.
        """
        return self._synthesizer

    def synthesize(self, text: str, output_file: str = os.path.join(ROOT_DIR, ".mp", "audio.wav")) -> str:
        """
        Synthesizes the given text into speech.

        Args:
            text (str): The text to synthesize.
            output_file (str, optional): The output file to save the synthesized speech. Defaults to "audio.wav".

        Returns:
            str: The path to the output file.
        """
        # Synthesize the text
        outputs = self.synthesizer.tts(text)

        # Save the synthesized speech to the output file
        self.synthesizer.save_wav(outputs, output_file)

        return output_file

