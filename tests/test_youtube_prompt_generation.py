import importlib
import json
import os
import sys
import tempfile
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

    def test_build_topic_prompt_targets_weird_business_microdocs(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube._niche = "weird business / internet / creator-economy micro-doc Shorts"
        youtube._language = "english"

        prompt = youtube._build_topic_prompt([])

        self.assertIn("weird business", prompt.lower())
        self.assertIn("viral products", prompt.lower())
        self.assertIn("creator moves", prompt.lower())
        self.assertIn("internet scams", prompt.lower())
        self.assertIn("one familiar thing, one contradiction, one payoff", prompt.lower())
        self.assertNotIn("historical impossibility", prompt.lower())
        self.assertNotIn("true crime", prompt.lower())

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

    def test_generate_prompts_requests_realistic_business_visuals(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube._niche = "weird business / internet / creator-economy micro-doc Shorts"
        youtube.subject = "The app that made printed photos into a subscription"
        youtube.script = "An app sold nostalgia through recurring photo orders."
        youtube.generate_response = Mock(return_value='["A smartphone showing a photo subscription checkout flow"]')

        with patch.object(self.youtube_module, "success"), patch.object(
            self.youtube_module,
            "get_verbose",
            return_value=False,
        ):
            youtube.generate_prompts()

        prompt = youtube.generate_response.call_args.args[0]

        self.assertIn("realistic and grounded", prompt)
        self.assertIn("app screens", prompt)
        self.assertIn("dashboards", prompt)
        self.assertIn("realistic business photography", prompt)

    def test_generate_prompts_requests_editorial_commercial_camera_language(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube._niche = "weird business / internet / creator-economy micro-doc Shorts"
        youtube.subject = "The storefront strategy that made a brand feel premium"
        youtube.script = "A brand used visual merchandising to justify higher prices."
        youtube.generate_response = Mock(return_value='["A premium retail storefront with branded packaging"]')

        with patch.object(self.youtube_module, "success"), patch.object(
            self.youtube_module,
            "get_verbose",
            return_value=False,
        ):
            youtube.generate_prompts()

        prompt = youtube.generate_response.call_args.args[0]

        self.assertIn("polished editorial or commercial visual", prompt)
        self.assertIn("clean camera language", prompt)
        self.assertIn("grounded lighting", prompt)
        self.assertIn("legible layouts", prompt)
        self.assertIn("not a wilderness documentary", prompt)
        self.assertIn("not stylized AI art", prompt)

    def test_generate_prompts_sanitizes_risky_distress_language(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube._niche = "weird business / internet / creator-economy micro-doc Shorts"
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
        self.assertIn("realistic business/editorial visual", lowered)
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
        youtube._niche = "weird business / internet / creator-economy micro-doc Shorts"

        sanitized = youtube._sanitize_image_prompt(
            "A grim and detailed autopsy scene from 1959, focusing on the unexplained internal injuries "
            "of a victim, showing massive chest trauma with no external wounds, under cold clinical light."
        ).lower()

        self.assertIn("archival medical investigation setting", sanitized)
        self.assertIn("medical findings", sanitized)
        self.assertIn("realistic business/editorial visual", sanitized)
        self.assertNotIn("autopsy scene", sanitized)
        self.assertNotIn("internal injuries", sanitized)
        self.assertNotIn("massive chest trauma", sanitized)

    def test_sanitize_image_prompt_adds_business_editorial_camera_style(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube._niche = "weird business / internet / creator-economy micro-doc Shorts"

        sanitized = youtube._sanitize_image_prompt(
            "A snow-covered tent at night beneath a stormy sky."
        ).lower()

        self.assertIn("realistic business/editorial visual", sanitized)
        self.assertIn("app screens", sanitized)
        self.assertIn("dashboards", sanitized)
        self.assertIn("grounded lighting", sanitized)
        self.assertIn("not surreal ai art", sanitized)

    def test_generate_script_uses_story_structured_prompt(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.subject = "How a photo-printing app became a breakout subscription business"
        youtube._language = "english"
        youtube._niche = "weird business / internet / creator-economy micro-doc Shorts"
        youtube.generate_response = Mock(
            return_value=(
                "One app turned disposable photos into a habit people kept paying for. "
                "It launched with a simple promise and a sharper business model. "
                "The real lift came from how it packaged nostalgia as a recurring product. "
                "Creators amplified it because the format was easy to explain and show. "
                "That turned a small product idea into a bigger internet business story. "
                "The lesson was that distribution mattered as much as the app itself."
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
        self.assertIn("6-sentence", prompt)
        self.assertIn("micro-doc", prompt.lower())
        self.assertIn("depth requirement", prompt.lower())
        self.assertIn("business model", prompt.lower())
        self.assertIn("work or fail", prompt.lower())
        self.assertIn("short declarative sentences", prompt.lower())
        self.assertIn("one idea per sentence", prompt.lower())
        self.assertIn("easy to caption on screen", prompt.lower())
        self.assertIn("judgment question", prompt.lower())
        self.assertNotIn("true crime podcast", prompt.lower())
        self.assertNotIn("historical impossibility", prompt.lower())

    def test_generate_prompts_requests_business_and_internet_visuals_for_new_niche(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube._niche = "weird business / internet / creator-economy micro-doc Shorts"
        youtube.subject = "The app that turned photo printing into a subscription"
        youtube.script = "An app sold nostalgia through a recurring purchase loop."
        youtube.generate_response = Mock(
            return_value='["A smartphone showing a photo subscription checkout flow"]'
        )

        with patch.object(self.youtube_module, "success"), patch.object(
            self.youtube_module,
            "get_verbose",
            return_value=False,
        ):
            youtube.generate_prompts()

        prompt = youtube.generate_response.call_args.args[0].lower()

        self.assertIn("app screens", prompt)
        self.assertIn("dashboards", prompt)
        self.assertIn("storefronts", prompt)
        self.assertIn("creator setups", prompt)
        self.assertNotIn("national geographic-style documentary photography", prompt)
        self.assertNotIn("dead bodies", prompt)

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

    def test_generate_metadata_requests_business_microdoc_packaging(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.subject = "The app that turned printed photos into a subscription"
        youtube.script = "Customers kept paying because nostalgia was packaged like a recurring utility."
        youtube.generate_response = Mock(
            side_effect=[
                "The App That Made Nostalgia Recurring Revenue",
                "A photo app looked simple on the surface. The real story was the subscription loop behind it. Smart brand move or manipulation?",
            ]
        )

        metadata = youtube.generate_metadata()

        title_prompt = youtube.generate_response.call_args_list[0].args[0]
        description_prompt = youtube.generate_response.call_args_list[1].args[0]

        self.assertEqual(metadata, youtube.metadata)
        self.assertIn("clean curiosity gap", title_prompt)
        self.assertIn("surprising business model", title_prompt)
        self.assertIn("Lead with the contradiction, not the category label", title_prompt)
        self.assertIn("Do not use hashtags in the title", title_prompt)
        self.assertIn("prefer 5 to 10 words", title_prompt)
        self.assertIn("one story, one tension, one payoff", title_prompt)
        self.assertIn("high-contrast opening line", description_prompt)
        self.assertIn("Do not repeat the title verbatim", description_prompt)
        self.assertIn("one story, one tension, one payoff", description_prompt)
        self.assertIn("why it matters", description_prompt)
        self.assertIn("end with a short judgment question", description_prompt)

    def test_generate_topic_requests_reported_background_rich_story_ideas(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube._language = "english"
        youtube._niche = "true crime and strange real events"
        youtube.get_videos = Mock(return_value=[])
        youtube.generate_response = Mock(
            return_value="The photo app that turned disposable cameras into subscription revenue"
        )

        topic = youtube.generate_topic()
        prompt = youtube.generate_response.call_args.args[0]

        self.assertEqual(topic, youtube.subject)
        self.assertIn(
            "enough verified background to explain who, what, how, and why it mattered",
            prompt,
        )
        self.assertIn("weird businesses", prompt)
        self.assertIn("viral products", prompt)
        self.assertIn("creator moves", prompt)
        self.assertIn("instantly interesting before explanation", prompt)
        self.assertIn("familiar app, company, creator, product, or platform", prompt)
        self.assertIn("one familiar thing, one contradiction, one payoff", prompt)
        self.assertIn("one story, one tension, one payoff", prompt)
        self.assertIn("reported micro-doc story", prompt)
        self.assertIn("not a vague trend summary", prompt)

    def test_generate_script_requests_reported_context_and_fact_discipline(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.subject = "The app that turned photo printing into a subscription"
        youtube._language = "english"
        youtube._niche = "true crime and strange real events"
        youtube.generate_response = Mock(
            return_value=(
                "One app turned disposable photos into recurring revenue. "
                "It looked simple, but the business model was unusually sticky. "
                "The real engine was how it packaged nostalgia as a habit. "
                "Creators and social posts helped spread the story. "
                "That mix of product and distribution made the company grow. "
                "The payoff was a mundane product turned into a subscription loop."
            )
        )

        with patch.object(
            self.youtube_module,
            "get_script_sentence_length",
            return_value=6,
        ):
            youtube.generate_script()

        prompt = youtube.generate_response.call_args.args[0]

        self.assertIn("DEPTH REQUIREMENT", prompt)
        self.assertIn(
            "how money, attention, or platforms actually work",
            prompt,
        )
        self.assertIn(
            "Clearly distinguish confirmed facts from reported estimates or public speculation",
            prompt,
        )
        self.assertIn("Do not invent facts", prompt)
        self.assertIn("counterintuitive", prompt.lower())
        self.assertIn("Hook", prompt)
        self.assertIn("BEAT STRUCTURE", prompt)
        self.assertIn("transferable pattern", prompt.lower())
        self.assertIn("Short declarative sentences", prompt)
        self.assertIn("one idea per sentence", prompt.lower())
        self.assertIn("easy to caption on screen", prompt.lower())
        self.assertIn("judgment question", prompt.lower())

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
        self.assertIn('Do not say "welcome back"', prompt)
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

        self.assertIn("5-sentence", prompt)

    def test_generate_script_prompt_uses_effective_business_niche(self) -> None:
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
            "Niche: weird business / internet / creator-economy micro-doc Shorts",
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

    def test_generate_manim_code_injects_text_fallbacks_for_tex_objects(self) -> None:
        youtube = self.youtube_module.YouTube.__new__(self.youtube_module.YouTube)
        youtube.subject = "Bloom filters"
        youtube.script = "Bloom filters trade false positives for low memory use."
        youtube.generate_response = Mock(
            return_value=(
                "from manim import *\n"
                "config.pixel_width = 1080\n"
                "config.pixel_height = 1920\n"
                "config.frame_width = 4.5\n"
                "config.frame_height = 8\n\n"
                "class ExplainerScene(Scene):\n"
                "    def construct(self):\n"
                "        title = Text('Bloom Filter')\n"
                "        formula = MathTex('h_1(x)=2', font_size=36)\n"
                "        label = Tex('maybe present', font_size=28)\n"
                "        self.add(title, formula, label)\n"
            )
        )

        with tempfile.TemporaryDirectory() as temp_dir, patch.object(
            self.youtube_module,
            "ROOT_DIR",
            temp_dir,
        ), patch.object(
            self.youtube_module,
            "get_verbose",
            return_value=False,
        ):
            os.makedirs(os.path.join(temp_dir, ".mp"), exist_ok=True)
            scene_path = youtube.generate_manim_code()
            with open(scene_path, "r", encoding="utf-8") as handle:
                scene_source = handle.read()

            self.assertIn("def MathTex(*parts, **kwargs):", scene_source)
            self.assertIn("def Tex(*parts, **kwargs):", scene_source)
            self.assertIn("return Text(joined_parts, **safe_kwargs)", scene_source)
            self.assertIn('joined_parts = joined_parts.replace("\\\\text", "")', scene_source)
            self.assertIn('joined_parts = joined_parts.replace("\\\\", "")', scene_source)


if __name__ == "__main__":
    unittest.main()
