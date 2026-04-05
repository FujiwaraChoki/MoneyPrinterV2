import importlib
import json
import os
import sys
import unittest
from unittest.mock import Mock
from unittest.mock import patch


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


class YouTubePromptGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_modules = {
            "classes.YouTube": sys.modules.pop("classes.YouTube", None),
            "llm_provider": sys.modules.pop("llm_provider", None),
        }
        self.youtube_module = importlib.import_module("classes.YouTube")
        self.addCleanup(self.restore_modules)

    def restore_modules(self) -> None:
        sys.modules.pop("classes.YouTube", None)
        sys.modules.pop("llm_provider", None)
        for module_name, module in self._original_modules.items():
            if module is not None:
                sys.modules[module_name] = module

    def test_generate_prompts_caps_long_scripts_at_ten_images(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.subject = "science and technology"
        youtube.script = "A" * 258

        generated_response = json.dumps(
            [f"image prompt {index}" for index in range(12)]
        )
        youtube.generate_response = Mock(return_value=generated_response)

        with patch.object(self.youtube_module, "success"), patch.object(
            self.youtube_module,
            "get_verbose",
            return_value=False,
        ):
            image_prompts = youtube.generate_prompts()

        self.assertEqual(len(image_prompts), 10)
        self.assertEqual(youtube.image_prompts, image_prompts)
        self.assertIn(
            "Generate 10 Image Prompts",
            youtube.generate_response.call_args.args[0],
        )

    def test_generate_prompts_prefers_actual_prompt_array_over_example_echo(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.subject = "maritime disappearance"
        youtube.script = "A ship vanished and left behind bloodstained bandages."

        generated_response = (
            'Here is the format example: ["image prompt 1", "image prompt 2", "image prompt 3"]\n'
            'Actual prompts: ["A battered cargo ship drifting alone on a dark ocean", '
            '"A bloodstained doctor bag abandoned on a silent deck", '
            '"Empty lifeboat davits against a stormy twilight sky"]'
        )
        youtube.generate_response = Mock(return_value=generated_response)

        with patch.object(self.youtube_module, "success"), patch.object(
            self.youtube_module,
            "get_verbose",
            return_value=True,
        ), patch.object(
            self.youtube_module.YouTube,
            "_sanitize_image_prompt",
            side_effect=lambda text: text,
        ):
            image_prompts = youtube.generate_prompts()

        self.assertEqual(
            image_prompts,
            [
                "A battered cargo ship drifting alone on a dark ocean",
                "A bloodstained doctor bag abandoned on a silent deck",
                "Empty lifeboat davits against a stormy twilight sky",
            ],
        )

    def test_generate_prompts_requests_documentary_non_graphic_images(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.subject = "Dyatlov Pass"
        youtube.script = "A group fled their tent into the snow and no one knows why."
        youtube.generate_response = Mock(return_value='["A snow-covered tent at night"]')

        with patch.object(self.youtube_module, "success"), patch.object(
            self.youtube_module,
            "get_verbose",
            return_value=False,
        ):
            youtube.generate_prompts()

        prompt = youtube.generate_response.call_args.args[0]

        self.assertIn("documentary-style", prompt)
        self.assertIn("non-graphic", prompt)
        self.assertIn("Avoid gore", prompt)
        self.assertIn("panic close-ups", prompt)

    def test_generate_prompts_requests_national_geographic_camera_language(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.subject = "Dyatlov Pass"
        youtube.script = "A group fled their tent into the snow and no one knows why."
        youtube.generate_response = Mock(return_value='["A snow-covered tent at night"]')

        with patch.object(self.youtube_module, "success"), patch.object(
            self.youtube_module,
            "get_verbose",
            return_value=False,
        ):
            youtube.generate_prompts()

        prompt = youtube.generate_response.call_args.args[0]

        self.assertIn("National Geographic-style documentary photography", prompt)
        self.assertIn("professional camera language", prompt)
        self.assertIn("shot type", prompt)
        self.assertIn("camera angle", prompt)
        self.assertIn("lens choice", prompt)
        self.assertIn("not stylized AI art", prompt)

    def test_generate_prompts_sanitizes_risky_distress_language(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.subject = "Dyatlov Pass"
        youtube.script = "A group fled their tent into the snow and no one knows why."
        youtube.generate_response = Mock(
            return_value=json.dumps(
                [
                    (
                        "A chilling, moonlit view of the hastily abandoned Dyatlov Pass tent, "
                        "their faces contorted in sheer panic as they desperately flee into a brutal, "
                        "sub-zero arctic blizzard without proper winter gear."
                    )
                ]
            )
        )

        with patch.object(self.youtube_module, "success"), patch.object(
            self.youtube_module,
            "get_verbose",
            return_value=False,
        ):
            image_prompts = youtube.generate_prompts()

        lowered = image_prompts[0].lower()
        self.assertIn("dyatlov pass tent", lowered)
        self.assertIn("documentary-style historical scene", lowered)
        self.assertIn("no visible injury", lowered)
        self.assertIn("move away", lowered)
        self.assertNotIn("faces contorted in sheer panic", lowered)
        self.assertNotIn("desperately flee", lowered)
        self.assertNotIn("their faces", lowered)
        self.assertNotIn("brutal", lowered)

    def test_generate_prompts_raises_after_repeated_unformatted_responses(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.subject = "Dyatlov Pass"
        youtube.script = "A group fled their tent into the snow and no one knows why."
        attempts = {"count": 0}

        def unformatted_response(_prompt: str) -> str:
            attempts["count"] += 1
            if attempts["count"] > 3:
                self.fail("generate_prompts retried more than 3 times")
            return "not valid json"

        youtube.generate_response = Mock(side_effect=unformatted_response)

        with patch.object(self.youtube_module, "get_verbose", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "Failed to generate Image Prompts"):
                youtube.generate_prompts()

        self.assertEqual(youtube.generate_response.call_count, 3)

    def test_sanitize_image_prompt_softens_explicit_medical_trauma(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)

        sanitized = youtube._sanitize_image_prompt(
            "A grim and detailed autopsy scene from 1959, focusing on the unexplained internal injuries "
            "of a victim, showing massive chest trauma with no external wounds, under cold clinical light."
        ).lower()

        self.assertIn("archival medical investigation setting", sanitized)
        self.assertIn("medical findings", sanitized)
        self.assertIn("documentary-style historical scene", sanitized)
        self.assertIn("no visible injury", sanitized)
        self.assertNotIn("autopsy scene", sanitized)
        self.assertNotIn("internal injuries", sanitized)
        self.assertNotIn("massive chest trauma", sanitized)

    def test_sanitize_image_prompt_adds_national_geographic_real_camera_style(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)

        sanitized = youtube._sanitize_image_prompt(
            "A snow-covered tent at night beneath a stormy sky."
        ).lower()

        self.assertIn("national geographic-style documentary photography", sanitized)
        self.assertIn("professional documentary camera language", sanitized)
        self.assertIn("shot type", sanitized)
        self.assertIn("camera angle", sanitized)
        self.assertIn("lens choice", sanitized)
        self.assertIn("not stylized ai art", sanitized)

    def test_generate_script_uses_story_structured_prompt(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.subject = "The ship that disappeared overnight"
        youtube._language = "english"
        youtube._niche = "strange real events"
        youtube.generate_response = Mock(
            return_value=(
                "A ship vanished without a trace. "
                "It had left port the night before. "
                "The strangest detail was what crews found next. "
                "Search teams kept uncovering new clues. "
                "The final report only deepened the mystery. "
                "No one ever explained the last signal."
            )
        )

        with patch.object(
            self.youtube_module,
            "get_script_sentence_length",
            return_value=6,
        ):
            script = youtube.generate_script()

        prompt = youtube.generate_response.call_args.args[0]

        self.assertEqual(script, youtube.script)
        self.assertIn("exactly 6 sentences", prompt)
        self.assertIn("compact narrated story", prompt)
        self.assertIn("Every sentence must add a new concrete detail", prompt)
        self.assertIn("Hook with the strangest or most unsettling claim", prompt)
        self.assertIn("End with a final sting", prompt)

    def test_generate_metadata_raises_after_repeated_oversized_titles(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.subject = "A town heard the same sound every night"
        youtube.script = "A script."
        attempts = {"count": 0}

        def oversized_title(_prompt: str) -> str:
            attempts["count"] += 1
            if attempts["count"] > 3:
                self.fail("generate_metadata retried more than 3 times")
            return "A" * 101

        youtube.generate_response = Mock(side_effect=oversized_title)

        with patch.object(self.youtube_module, "get_verbose", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "Generated title remained too long"):
                youtube.generate_metadata()

        self.assertEqual(youtube.generate_response.call_count, 3)

    def test_generate_metadata_raises_after_repeated_oversized_descriptions(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.subject = "A town heard the same sound every night"
        youtube.script = "A script."
        title = "Short title"
        long_description = "D" * 5001
        youtube.generate_response = Mock(
            side_effect=[title, long_description, long_description, long_description]
        )

        with patch.object(self.youtube_module, "get_verbose", return_value=False):
            with self.assertRaisesRegex(
                RuntimeError,
                "Generated description remained too long",
            ):
                youtube.generate_metadata()

        self.assertEqual(youtube.generate_response.call_count, 4)

    def test_generate_metadata_requests_historical_impossibility_packaging(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.subject = "The storm that made telegraphs burst into flame"
        youtube.script = "Operators watched sparks leap from their equipment as the sky lit up."
        youtube.generate_response = Mock(
            side_effect=[
                "The Night the Sky Powered Telegraphs #history #mystery",
                "The night the sky powered the grid.\nA real story about the storm that made telegraph lines come alive.",
            ]
        )

        metadata = youtube.generate_metadata()

        title_prompt = youtube.generate_response.call_args_list[0].args[0]
        description_prompt = youtube.generate_response.call_args_list[1].args[0]

        self.assertEqual(metadata, youtube.metadata)
        self.assertIn("clean curiosity gap", title_prompt)
        self.assertIn("historical impossibility", title_prompt)
        self.assertIn("one story, one mystery, one payoff", title_prompt)
        self.assertIn("high-contrast opening line", description_prompt)
        self.assertIn("one story, one mystery, one payoff", description_prompt)
        self.assertIn("why it matters", description_prompt)

    def test_generate_topic_requests_reported_background_rich_story_ideas(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube._language = "english"
        youtube._niche = "true crime and strange real events"
        youtube.get_videos = Mock(return_value=[])
        youtube.generate_response = Mock(
            return_value="The killing that forced a city to confront its own police corruption"
        )

        topic = youtube.generate_topic()
        prompt = youtube.generate_response.call_args.args[0]

        self.assertEqual(topic, youtube.subject)
        self.assertIn(
            "enough verified background to explain who, where, when, and why it matters",
            prompt,
        )
        self.assertIn("historical impossibility", prompt)
        self.assertIn("one story, one mystery, one payoff", prompt)
        self.assertIn("broad curiosity overlap", prompt)
        self.assertIn("reported documentary story", prompt)
        self.assertIn("not a vague teaser premise", prompt)

    def test_generate_script_requests_reported_context_and_fact_discipline(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.subject = "The ship that disappeared overnight"
        youtube._language = "english"
        youtube._niche = "true crime and strange real events"
        youtube.generate_response = Mock(
            return_value=(
                "A ship vanished without a trace. "
                "It had left port the night before. "
                "The strangest detail was what crews found next. "
                "Search teams kept uncovering new clues. "
                "The final report only deepened the mystery. "
                "No one ever explained the last signal."
            )
        )

        with patch.object(
            self.youtube_module,
            "get_script_sentence_length",
            return_value=6,
        ):
            youtube.generate_script()

        prompt = youtube.generate_response.call_args.args[0]

        self.assertIn(
            "discipline of a reported newspaper feature and the narrative pull of a top true crime podcast",
            prompt,
        )
        self.assertIn(
            "Give enough background context for the viewer to understand why the story matters",
            prompt,
        )
        self.assertIn(
            "Clearly distinguish confirmed facts from rumor, legend, or theory",
            prompt,
        )
        self.assertIn("Do not invent facts", prompt)
        self.assertIn('make the viewer think "wait, what?"', prompt)
        self.assertIn("one story, one mystery, one payoff", prompt)
        self.assertIn("35 to 45 second spoken short", prompt)

    def test_generate_script_prompt_preserves_raw_output_constraints(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.subject = "A town heard the same sound every night"
        youtube._language = "english"
        youtube._niche = "strange real events"
        youtube.generate_response = Mock(return_value="One. Two. Three. Four. Five. Six.")

        with patch.object(
            self.youtube_module,
            "get_script_sentence_length",
            return_value=6,
        ):
            youtube.generate_script()

        prompt = youtube.generate_response.call_args.args[0]

        self.assertIn("Do not use markdown", prompt)
        self.assertIn("Do not use filler", prompt)
        self.assertIn('Do not say things like "welcome back"', prompt)
        self.assertIn("Return only the raw script", prompt)
        self.assertNotIn("SENTENCES ARE SHORT", prompt)

    def test_generate_script_prompt_uses_configured_sentence_count(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.subject = "A city woke up covered in ash"
        youtube._language = "english"
        youtube._niche = "strange real events"
        youtube.generate_response = Mock(return_value="One. Two. Three. Four. Five.")

        with patch.object(
            self.youtube_module,
            "get_script_sentence_length",
            return_value=5,
        ):
            youtube.generate_script()

        prompt = youtube.generate_response.call_args.args[0]

        self.assertIn("exactly 5 sentences", prompt)

    def test_generate_script_prompt_uses_account_niche(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.subject = "A village disappeared from the map"
        youtube._language = "english"
        youtube._niche = "unexplained disappearances and strange real events"
        youtube.generate_response = Mock(return_value="One. Two. Three. Four. Five. Six.")

        with patch.object(
            self.youtube_module,
            "get_script_sentence_length",
            return_value=6,
        ):
            youtube.generate_script()

        prompt = youtube.generate_response.call_args.args[0]

        self.assertIn(
            "The niche is: unexplained disappearances and strange real events.",
            prompt,
        )

    def test_generate_script_raises_after_repeated_oversized_responses(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.subject = "A village disappeared from the map"
        youtube._language = "english"
        youtube._niche = "unexplained disappearances and strange real events"
        youtube.generate_response = Mock(return_value="A" * 5001)

        with patch.object(
            self.youtube_module,
            "get_script_sentence_length",
            return_value=6,
        ), patch.object(
            self.youtube_module,
            "get_verbose",
            return_value=False,
        ):
            with self.assertRaisesRegex(RuntimeError, "Generated script remained too long"):
                youtube.generate_script()

        self.assertEqual(youtube.generate_response.call_count, 3)

    def test_generate_script_raises_when_response_is_empty(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.subject = "A village disappeared from the map"
        youtube._language = "english"
        youtube._niche = "unexplained disappearances and strange real events"
        youtube.generate_response = Mock(return_value="")

        with patch.object(
            self.youtube_module,
            "get_script_sentence_length",
            return_value=6,
        ), patch.object(self.youtube_module, "error") as error_mock:
            with self.assertRaisesRegex(RuntimeError, "The generated script is empty"):
                youtube.generate_script()

        error_mock.assert_called_once_with("The generated script is empty.")


if __name__ == "__main__":
    unittest.main()
