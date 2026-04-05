import re
import base64
import json
import time
import os
import requests
from difflib import SequenceMatcher
from urllib.parse import urlparse

from PIL import Image
from cinematic_motion import render_motion_frame
from utils import *
from cache import *
from .Tts import TTS
from llm_provider import generate_text
from config import *
from status import *
from uuid import uuid4
from constants import *
from typing import List
from typing import Optional
from typing import Set
from moviepy.editor import *
from termcolor import colored
from selenium import webdriver
from moviepy.video.fx.all import crop
from moviepy.config import change_settings
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from moviepy.video.tools.subtitles import SubtitlesClip
from webdriver_manager.firefox import GeckoDriverManager
from datetime import datetime


def _ensure_pillow_antialias_compatibility(image_module) -> None:
    if hasattr(image_module, "ANTIALIAS"):
        return

    if hasattr(image_module, "Resampling"):
        image_module.ANTIALIAS = image_module.Resampling.LANCZOS
        return

    image_module.ANTIALIAS = image_module.LANCZOS


_ensure_pillow_antialias_compatibility(Image)


GENERIC_STORY_TOKENS = {
    "a",
    "an",
    "and",
    "at",
    "case",
    "deaths",
    "deadly",
    "disappearance",
    "disaster",
    "documentary",
    "event",
    "explained",
    "for",
    "from",
    "ghost",
    "history",
    "historical",
    "how",
    "incident",
    "in",
    "inside",
    "made",
    "makes",
    "mysteries",
    "mystery",
    "no",
    "of",
    "on",
    "passage",
    "real",
    "sense",
    "ship",
    "short",
    "shorts",
    "still",
    "story",
    "strange",
    "that",
    "the",
    "this",
    "to",
    "tragedy",
    "true",
    "unexplained",
    "unsolved",
    "vanished",
    "vanishing",
    "what",
    "why",
    "with",
}


# Set ImageMagick Path
change_settings({"IMAGEMAGICK_BINARY": get_imagemagick_path()})


class YouTube:
    """
    Class for YouTube Automation.

    Steps to create a YouTube Short:
    1. Generate a topic [DONE]
    2. Generate a script [DONE]
    3. Generate metadata (Title, Description, Tags) [DONE]
    4. Generate AI Image Prompts [DONE]
    4. Generate Images based on generated Prompts [DONE]
    5. Convert Text-to-Speech [DONE]
    6. Show images each for n seconds, n: Duration of TTS / Amount of images [DONE]
    7. Combine Concatenated Images with the Text-to-Speech [DONE]
    """

    def __init__(
        self,
        account_uuid: str,
        account_nickname: str,
        fp_profile_path: str,
        niche: str,
        language: str,
    ) -> None:
        """
        Constructor for YouTube Class.

        Args:
            account_uuid (str): The unique identifier for the YouTube account.
            account_nickname (str): The nickname for the YouTube account.
            fp_profile_path (str): Path to the firefox profile that is logged into the specificed YouTube Account.
            niche (str): The niche of the provided YouTube Channel.
            language (str): The language of the Automation.

        Returns:
            None
        """
        self._account_uuid: str = account_uuid
        self._account_nickname: str = account_nickname
        self._fp_profile_path: str = fp_profile_path
        self._niche: str = niche
        self._language: str = language

        self.images = []

        # Initialize the Firefox profile
        self.options: Options = Options()

        # Set headless state of browser
        if get_headless():
            self.options.add_argument("--headless")

        if not os.path.isdir(self._fp_profile_path):
            raise ValueError(
                f"Firefox profile path does not exist or is not a directory: {self._fp_profile_path}"
            )

        self.options.add_argument("-profile")
        self.options.add_argument(self._fp_profile_path)

        # Set the service
        self.service: Service = Service(GeckoDriverManager().install())

        # Initialize the browser
        self.browser: webdriver.Firefox = self._create_browser()

    def _create_browser(self):
        return webdriver.Firefox(service=self.service, options=self.options)

    def _ensure_browser(self):
        if getattr(self, "browser", None) is None:
            self.browser = self._create_browser()
        return self.browser

    @property
    def niche(self) -> str:
        """
        Getter Method for the niche.

        Returns:
            niche (str): The niche
        """
        return self._niche

    @property
    def language(self) -> str:
        """
        Getter Method for the language to use.

        Returns:
            language (str): The language
        """
        return self._language

    def generate_response(self, prompt: str, model_name: str = None) -> str:
        """
        Generates an LLM Response based on a prompt and the user-provided model.

        Args:
            prompt (str): The prompt to use in the text generation.

        Returns:
            response (str): The generated AI Repsonse.
        """
        return generate_text(prompt, model_name=model_name)

    def generate_topic(self) -> str:
        """
        Generates a topic based on the YouTube Channel niche.

        Returns:
            topic (str): The generated topic.
        """
        existing_videos = self.get_videos()
        avoid_story_references = self._get_story_references(existing_videos)
        max_attempts = 5

        for _ in range(max_attempts):
            completion = self.generate_response(
                self._build_topic_prompt(avoid_story_references)
            )
            completion = re.sub(r"\*", "", str(completion or "")).strip()

            if not completion:
                error("Failed to generate Topic.")
                raise RuntimeError("Failed to generate Topic.")

            similar_video = self._find_similar_video(completion, existing_videos)
            if similar_video is not None:
                if get_verbose():
                    warning(
                        "Generated topic is too similar to a previous video. Retrying..."
                    )

                reference = self._get_video_story_reference(similar_video)
                if reference and reference not in avoid_story_references:
                    avoid_story_references.append(reference)

                if completion not in avoid_story_references:
                    avoid_story_references.append(completion)
                continue

            self.subject = completion
            return completion

        raise RuntimeError(
            "Generated topic remained too similar to previous videos after 5 attempts."
        )

    def _build_topic_prompt(self, avoid_story_references: List[str]) -> str:
        avoid_block = ""
        if avoid_story_references:
            bullet_list = "\n".join(
                f"        - {story}" for story in avoid_story_references[:15]
            )
            avoid_block = f"""

        Do not generate a topic that repeats or is substantially similar to these previously covered stories:
{bullet_list}

        Avoid the same core event, expedition, disaster, person, place, year, vessel, case, or incident even if you reword the title.
        """

        return f"""
        Please generate a specific video idea about the following niche: {self.niche}.
        The language is: {self.language}.
        Make it exactly one sentence.
        Prefer a fresh story that does not overlap with prior videos on this channel.{avoid_block}
        Choose a real story with enough verified background to explain who, where, when, and why it matters.
        Prefer a reported documentary story, not a vague teaser premise.
        Favor cases with concrete people, places, dates, institutions, or records that can support a tightly reported short.
        Only return the topic, nothing else.
        """

    def _normalize_story_text(self, text: str) -> str:
        cleaned = re.sub(r"[^a-z0-9]+", " ", str(text or "").lower())
        return re.sub(r"\s+", " ", cleaned).strip()

    def _story_tokens(self, text: str) -> List[str]:
        normalized = self._normalize_story_text(text)
        return [token for token in normalized.split() if token]

    def _story_distinctive_tokens(self, text: str) -> Set[str]:
        return {
            token
            for token in self._story_tokens(text)
            if token not in GENERIC_STORY_TOKENS and len(token) >= 4
        }

    def _story_years(self, text: str) -> Set[str]:
        return {token for token in self._story_tokens(text) if re.fullmatch(r"\d{4}", token)}

    def _story_similarity_score(self, candidate: str, comparison: str) -> float:
        candidate_text = self._normalize_story_text(candidate)
        comparison_text = self._normalize_story_text(comparison)

        if not candidate_text or not comparison_text:
            return 0.0

        if candidate_text == comparison_text:
            return 1.0

        if candidate_text in comparison_text or comparison_text in candidate_text:
            return 0.95

        candidate_tokens = self._story_distinctive_tokens(candidate_text)
        comparison_tokens = self._story_distinctive_tokens(comparison_text)
        token_overlap = candidate_tokens & comparison_tokens
        candidate_years = self._story_years(candidate_text)
        comparison_years = self._story_years(comparison_text)

        overlap_coverage = (
            len(token_overlap) / len(candidate_tokens) if candidate_tokens else 0.0
        )
        token_union = candidate_tokens | comparison_tokens
        jaccard = len(token_overlap) / len(token_union) if token_union else 0.0
        sequence_ratio = SequenceMatcher(
            None,
            candidate_text,
            comparison_text,
        ).ratio()

        score = max(
            sequence_ratio * 0.55 + overlap_coverage * 0.35 + jaccard * 0.10,
            overlap_coverage * 0.75 + jaccard * 0.25,
        )

        if token_overlap and any(len(token) >= 8 for token in token_overlap):
            score += 0.10

        if len(token_overlap) >= 2:
            score += 0.10

        if candidate_years and (candidate_years & comparison_years):
            score += 0.05

        return min(score, 1.0)

    def _get_video_story_reference(self, video: dict) -> str:
        return (
            str(video.get("topic") or "").strip()
            or str(video.get("title") or "").strip()
            or str(video.get("description") or "").strip()[:160]
        )

    def _get_story_references(self, videos: List[dict]) -> List[str]:
        references = []
        for video in videos:
            for reference in (
                str(video.get("topic") or "").strip(),
                str(video.get("title") or "").strip(),
                str(video.get("description") or "").strip()[:160],
            ):
                if reference and reference not in references:
                    references.append(reference)
        return references

    def _find_similar_video(self, candidate_topic: str, videos: List[dict]) -> Optional[dict]:
        best_match = None
        best_score = 0.0

        for video in videos:
            comparisons = [
                video.get("topic", ""),
                video.get("title", ""),
                video.get("description", ""),
                video.get("script", ""),
            ]

            for comparison in comparisons:
                score = self._story_similarity_score(candidate_topic, comparison)
                if score > best_score:
                    best_score = score
                    best_match = video

        if best_score >= 0.72:
            return best_match

        return None

    def generate_script(self) -> str:
        """
        Generate a script for a video, depending on the subject of the video, the number of paragraphs, and the AI model.

        Returns:
            script (str): The script of the video.
        """
        sentence_length = get_script_sentence_length()
        prompt = f"""
        Generate a script for a YouTube Short in exactly {sentence_length} sentences.

        The subject is: {self.subject}
        The language is: {self.language}
        The niche is: {self.niche}.

        Write the script like a compact narrated story about a real event.
        Write with the discipline of a reported newspaper feature and the narrative pull of a top true crime podcast.
        Every sentence must add a new concrete detail or move the story forward.
        Give enough background context for the viewer to understand why the story matters.
        Clearly distinguish confirmed facts from rumor, legend, or theory.
        Do not invent facts or present speculation as certainty.
        Do not use filler, introductions, conclusions, listicles, or educational framing.
        Do not say things like "welcome back", "in this video", or "did you know".
        Do not use markdown, titles, bullet points, speaker labels, or quotation marks around the full response.
        Return only the raw script.

        Use this beat structure as closely as possible:
        1. Hook with the strangest or most unsettling claim.
        2. Ground the story with who, where, or when.
        3. Explain the core anomaly, disaster, or impossible-seeming detail.
        4. Escalate with consequence, discovery, or rising tension.
        5. Deliver the main reveal, confirmed outcome, or historical consequence.
        6. End with a final sting, unresolved mystery, or haunting closing fact.

        If the sentence count is lower than 6, combine adjacent beats while keeping a hook, context, anomaly, consequence, and closing line.
        If the sentence count is higher than 6, use extra sentences only for concrete escalation details.

        Do not under any circumstance reference this prompt in your response.
        """
        max_attempts = 3
        completion = ""

        for attempt in range(max_attempts):
            completion = self.generate_response(prompt)

            # Apply regex to remove *
            completion = re.sub(r"\*", "", completion)

            if not completion:
                error("The generated script is empty.")
                raise RuntimeError("The generated script is empty.")

            if len(completion) <= 5000:
                break

            if get_verbose():
                warning("Generated Script is too long. Retrying...")
        else:
            raise RuntimeError("Generated script remained too long after 3 attempts.")

        self.script = completion

        return completion

    def generate_metadata(self) -> dict:
        """
        Generates Video metadata for the to-be-uploaded YouTube Short (Title, Description).

        Returns:
            metadata (dict): The generated metadata.
        """
        max_attempts = 3
        title = ""
        for _ in range(max_attempts):
            title = self.generate_response(
                f"Please generate a YouTube Video Title for the following subject, including hashtags: {self.subject}. Only return the title, nothing else. Limit the title under 100 characters."
            )

            if len(title) <= 100:
                break

            if get_verbose():
                warning("Generated Title is too long. Retrying...")
        else:
            raise RuntimeError("Generated title remained too long after 3 attempts.")

        description = self.generate_response(
            f"Please generate a YouTube Video Description for the following script: {self.script}. Only return the description, nothing else."
        )

        self.metadata = {"title": title, "description": description}

        return self.metadata

    def _looks_like_placeholder_prompt(self, prompt: str) -> bool:
        normalized = str(prompt).strip().lower()
        return normalized.startswith("image prompt") or "..." in normalized

    def _extract_image_prompt_candidates(self, completion: str) -> List[List[str]]:
        candidates: List[List[str]] = []

        def add_candidate(candidate) -> None:
            if not isinstance(candidate, list):
                return

            normalized = [str(item).strip() for item in candidate if str(item).strip()]
            if not normalized:
                return

            if all(isinstance(item, str) for item in normalized):
                candidates.append(normalized)

        try:
            parsed_completion = json.loads(completion)
            if isinstance(parsed_completion, dict):
                add_candidate(parsed_completion.get("image_prompts", []))
            else:
                add_candidate(parsed_completion)
        except Exception:
            pass

        for match in re.finditer(r"\[[\s\S]*?\]", completion):
            snippet = match.group(0)
            try:
                parsed_candidate = json.loads(snippet)
            except Exception:
                continue

            add_candidate(parsed_candidate)

        return candidates

    def _select_best_image_prompt_candidate(
        self, candidates: List[List[str]], n_prompts: int
    ) -> List[str]:
        if not candidates:
            return []

        def score(candidate: List[str]) -> tuple[int, int, int]:
            substantive_count = sum(
                1 for item in candidate if not self._looks_like_placeholder_prompt(item)
            )
            total_length = sum(len(item) for item in candidate)
            target_fit = -abs(len(candidate) - n_prompts)
            return substantive_count, target_fit, total_length

        best_candidate = max(candidates, key=score)
        return best_candidate[:n_prompts]

    def _sanitize_image_prompt(self, prompt: str) -> str:
        cleaned_prompt = " ".join(str(prompt).split())
        replacements = [
            (
                r"their faces contorted in sheer panic",
                "distant figures with indistinct expressions",
            ),
            (
                r"their faces contorted in panic",
                "distant figures with indistinct expressions",
            ),
            (
                r"faces? contorted in sheer panic",
                "distant figures with indistinct expressions",
            ),
            (
                r"faces? contorted in panic",
                "distant figures with indistinct expressions",
            ),
            (r"desperately flee(?:ing)?", "move away"),
            (r"\bflee(?:ing)?\b", "move away"),
            (r"\bautopsy scene\b", "archival medical investigation setting"),
            (
                r"massive chest trauma with no external wounds",
                "unexplained medical findings documented in records",
            ),
            (r"\binternal injuries?\b", "medical findings"),
            (r"\bvictim\b", "historical subject"),
            (r"\bbloodstained\b", "weathered"),
            (r"\bbloody\b", "weathered"),
            (r"\bcorpse(s)?\b", "aftermath"),
            (r"\bdead bod(?:y|ies)\b", "aftermath"),
            (r"\bchilling\b", "atmospheric"),
            (r"\bgrim\b", "somber"),
            (r"\bbrutal\b", "severe"),
            (r"\bpanic\b", "urgency"),
            (r"\bterrified\b", "alarmed"),
            (r"\bscreaming\b", "tense"),
            (r"\bwithout proper winter gear\b", "in limited winter clothing"),
            (r"\bmove away their tent\b", "move away from their tent"),
            (r"\bA atmospheric\b", "An atmospheric"),
        ]

        for pattern, replacement in replacements:
            cleaned_prompt = re.sub(
                pattern,
                replacement,
                cleaned_prompt,
                flags=re.IGNORECASE,
            )

        cleaned_prompt = re.sub(r"\s+", " ", cleaned_prompt).strip(" ,.")
        cleaned_prompt = cleaned_prompt.rstrip(".")

        lowered = cleaned_prompt.lower()
        documentary_style_suffix = (
            " National Geographic-style documentary photography, authentic "
            "photojournalism, professional documentary camera language, "
            "specific shot type, camera angle, lens choice, natural or "
            "practical lighting, grounded composition, realistic textures, "
            "not stylized AI art."
        )
        safety_suffix = (
            " Documentary-style historical scene, non-graphic, focus on setting, "
            "atmosphere, weather, objects, and distant figures, no visible injury, "
            "no gore, no dead bodies, no terrified facial close-ups."
        )

        if "national geographic-style documentary photography" not in lowered:
            cleaned_prompt = f"{cleaned_prompt}.{documentary_style_suffix}"
            lowered = cleaned_prompt.lower()

        if "non-graphic" not in lowered:
            cleaned_prompt = f"{cleaned_prompt}.{safety_suffix}"

        return cleaned_prompt

    def generate_prompts(self) -> List[str]:
        """
        Generates AI Image Prompts based on the provided Video Script.

        Returns:
            image_prompts (List[str]): Generated List of image prompts.
        """
        n_prompts = max(1, min(10, int(len(self.script) / 3)))

        prompt = f"""
        Generate {n_prompts} Image Prompts for AI Image Generation,
        depending on the subject of a video.
        Subject: {self.subject}

        The image prompts are to be returned as
        a JSON-Array of strings.

        Each search term should consist of a full sentence,
        always add the main subject of the video.

        Use vivid visual detail, but keep every prompt documentary-style
        and non-graphic.
        Make each prompt feel like National Geographic-style documentary photography
        or a frame from real documentary footage, not stylized AI art.
        Use professional camera language with a specific shot type,
        camera angle, lens choice, and lighting or composition cues.
        Focus on atmosphere, setting, weather, objects, distant figures,
        authentic textures, practical lighting, and historically grounded detail.
        Avoid gore, visible injury, dead bodies, medical trauma, panic close-ups,
        screaming faces, or explicit suffering.

        YOU MUST ONLY RETURN THE JSON-ARRAY OF STRINGS.
        YOU MUST NOT RETURN ANYTHING ELSE.
        YOU MUST NOT RETURN THE SCRIPT.

        The search terms must be related to the subject of the video.
        Here is an example of a JSON-Array of strings:
        ["image prompt 1", "image prompt 2", "image prompt 3"]

        For context, here is the full text:
        {self.script}
        """

        max_attempts = 3
        image_prompts = []
        for _ in range(max_attempts):
            completion = (
                str(self.generate_response(prompt))
                .replace("```json", "")
                .replace("```", "")
            )

            candidates = self._extract_image_prompt_candidates(completion)
            image_prompts = self._select_best_image_prompt_candidate(
                candidates, n_prompts
            )

            if image_prompts:
                break

            if get_verbose():
                warning("LLM returned an unformatted response. Attempting to clean...")
                warning("Failed to generate Image Prompts. Retrying...")
        else:
            raise RuntimeError("Failed to generate Image Prompts after 3 attempts.")

        if get_verbose():
            info(f" => Generated Image Prompts: {image_prompts}")

        if len(image_prompts) > n_prompts:
            image_prompts = image_prompts[: int(n_prompts)]

        image_prompts = [self._sanitize_image_prompt(item) for item in image_prompts]
        self.image_prompts = image_prompts

        success(f"Generated {len(image_prompts)} Image Prompts.")

        return image_prompts

    def _persist_image(self, image_bytes: bytes, provider_label: str) -> str:
        """
        Writes generated image bytes to a PNG file in .mp.

        Args:
            image_bytes (bytes): Image payload
            provider_label (str): Label for logging

        Returns:
            path (str): Absolute image path
        """
        image_path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + ".png")

        with open(image_path, "wb") as image_file:
            image_file.write(image_bytes)

        if get_verbose():
            info(f' => Wrote image from {provider_label} to "{image_path}"')

        self.images.append(image_path)
        return image_path

    def generate_image_nanobanana2(self, prompt: str) -> str:
        """
        Generates an AI Image using Nano Banana 2 API (Gemini image API).

        Args:
            prompt (str): Prompt for image generation

        Returns:
            path (str): The path to the generated image.
        """
        print(f"Generating Image using Nano Banana 2 API: {prompt}")

        api_key = get_nanobanana2_api_key()
        if not api_key:
            error("nanobanana2_api_key is not configured.")
            return None

        base_url = get_nanobanana2_api_base_url().rstrip("/")
        model = get_nanobanana2_model()
        aspect_ratio = get_nanobanana2_aspect_ratio()

        endpoint = f"{base_url}/models/{model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": {"aspectRatio": aspect_ratio},
            },
        }

        try:
            response = requests.post(
                endpoint,
                headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                json=payload,
                timeout=300,
            )
            response.raise_for_status()
            body = response.json()

            candidates = body.get("candidates", [])
            for candidate in candidates:
                content = candidate.get("content", {})
                for part in content.get("parts", []):
                    inline_data = part.get("inlineData") or part.get("inline_data")
                    if not inline_data:
                        continue
                    data = inline_data.get("data")
                    mime_type = inline_data.get("mimeType") or inline_data.get("mime_type", "")
                    if data and str(mime_type).startswith("image/"):
                        image_bytes = base64.b64decode(data)
                        return self._persist_image(image_bytes, "Nano Banana 2 API")

            if get_verbose():
                warning(f"Nano Banana 2 did not return an image payload. Response: {body}")
            return None
        except Exception as e:
            if get_verbose():
                warning(f"Failed to generate image with Nano Banana 2 API: {str(e)}")
            return None

    def _openrouter_modalities(self, model: str) -> list[str]:
        image_and_text_prefixes = ("google/", "openai/", "openrouter/")
        if str(model).startswith(image_and_text_prefixes):
            return ["image", "text"]
        return ["image"]

    def _persist_openrouter_image(self, image_url: str, model: str) -> str:
        if image_url.startswith("data:image/"):
            _, encoded = image_url.split(",", 1)
            image_bytes = base64.b64decode(encoded)
            return self._persist_image(image_bytes, f"OpenRouter ({model})")

        parsed = urlparse(image_url)
        if parsed.scheme in {"http", "https"}:
            response = requests.get(image_url, timeout=300)
            response.raise_for_status()
            return self._persist_image(response.content, f"OpenRouter ({model})")

        raise ValueError(f"Unsupported OpenRouter image URL format: {image_url[:64]}")

    def generate_image_openrouter(self, prompt: str) -> str:
        api_key = get_openrouter_api_key()
        if not api_key:
            if get_verbose():
                warning("openrouter_api_key is not configured for image generation.")
            return None

        models = get_openrouter_image_models()
        if not models:
            if get_verbose():
                warning("No OpenRouter image models configured. Falling back to Google AI Studio.")
            return None

        base_url = get_openrouter_base_url().rstrip("/")
        aspect_ratio = get_nanobanana2_aspect_ratio()

        for model in models:
            print(f"Generating Image using OpenRouter ({model}): {prompt}")

            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "modalities": self._openrouter_modalities(model),
                "image_config": {"aspect_ratio": aspect_ratio},
                "stream": False,
            }

            try:
                response = requests.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=300,
                )
                response.raise_for_status()
                body = response.json()

                choices = body.get("choices", [])
                if not choices:
                    if get_verbose():
                        warning(f"OpenRouter returned no choices for model {model}. Response: {body}")
                    continue

                message = choices[0].get("message", {})
                images = message.get("images", [])
                for image in images:
                    image_payload = image.get("image_url") or image.get("imageUrl") or {}
                    image_url = image_payload.get("url")
                    if image_url:
                        return self._persist_openrouter_image(image_url, model)

                if get_verbose():
                    warning(f"OpenRouter model {model} did not return an image payload. Response: {body}")
            except Exception as e:
                if get_verbose():
                    warning(f"Failed to generate image with OpenRouter model {model}: {str(e)}")

        return None

    def generate_image(self, prompt: str) -> str:
        """
        Generates an AI Image based on the configured provider.

        Args:
            prompt (str): Reference for image generation

        Returns:
            path (str): The path to the generated image.
        """
        prompt = self._sanitize_image_prompt(prompt)
        provider = get_image_provider()

        if provider == "openrouter_then_googleai":
            image_path = self.generate_image_openrouter(prompt)
            if image_path is not None:
                return image_path
            return self.generate_image_nanobanana2(prompt)

        if provider == "openrouter_only":
            return self.generate_image_openrouter(prompt)

        return self.generate_image_nanobanana2(prompt)

    def generate_script_to_speech(self, tts_instance: TTS) -> str:
        """
        Converts the generated script into Speech using KittenTTS and returns the path to the wav file.

        Args:
            tts_instance (tts): Instance of TTS Class.

        Returns:
            path_to_wav (str): Path to generated audio (WAV Format).
        """
        path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + ".wav")

        # Clean script, remove every character that is not a word character, a space, a period, a question mark, or an exclamation mark.
        self.script = re.sub(r"[^\w\s.?!]", "", self.script)

        tts_instance.synthesize(self.script, path)

        self.tts_path = path

        if get_verbose():
            info(f' => Wrote TTS to "{path}"')

        return path

    def add_video(self, video: dict) -> None:
        """
        Adds a video to the cache.

        Args:
            video (dict): The video to add

        Returns:
            None
        """
        cache = get_youtube_cache_path()

        with open(cache, "r") as file:
            previous_json = json.loads(file.read())

            # Find our account
            accounts = previous_json["accounts"]
            for account in accounts:
                if account["id"] == self._account_uuid:
                    existing_videos = account.get("videos", [])
                    replacement_index = None

                    video_path = video.get("path")
                    video_url = video.get("url")

                    for index, existing_video in enumerate(existing_videos):
                        if video_path and existing_video.get("path") == video_path:
                            replacement_index = index
                            break
                        if video_url and existing_video.get("url") == video_url:
                            replacement_index = index
                            break

                    if replacement_index is None:
                        existing_videos.append(video)
                    else:
                        existing_videos[replacement_index] = {
                            **existing_videos[replacement_index],
                            **video,
                        }

                    account["videos"] = existing_videos

            # Commit changes
            with open(cache, "w") as f:
                f.write(json.dumps(previous_json))

    def generate_subtitles(self, audio_path: str) -> str:
        """
        Generates subtitles for the audio using the configured STT provider.

        Args:
            audio_path (str): The path to the audio file.

        Returns:
            path (str): The path to the generated SRT File.
        """
        provider = str(get_stt_provider() or "local_whisper").lower()

        if provider == "local_whisper":
            return self.generate_subtitles_local_whisper(audio_path)

        if provider == "third_party_assemblyai":
            return self.generate_subtitles_assemblyai(audio_path)

        warning(f"Unknown stt_provider '{provider}'. Falling back to local_whisper.")
        return self.generate_subtitles_local_whisper(audio_path)

    def generate_subtitles_assemblyai(self, audio_path: str) -> str:
        """
        Generates subtitles using AssemblyAI.

        Args:
            audio_path (str): Audio file path

        Returns:
            path (str): Path to SRT file
        """
        import assemblyai as aai

        aai.settings.api_key = get_assemblyai_api_key()
        config = aai.TranscriptionConfig()
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(audio_path)
        subtitles = transcript.export_subtitles_srt()

        srt_path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + ".srt")

        with open(srt_path, "w") as file:
            file.write(subtitles)

        return srt_path

    def _format_srt_timestamp(self, seconds: float) -> str:
        """
        Formats a timestamp in seconds to SRT format.

        Args:
            seconds (float): Seconds

        Returns:
            ts (str): HH:MM:SS,mmm
        """
        total_millis = max(0, int(round(seconds * 1000)))
        hours = total_millis // 3600000
        minutes = (total_millis % 3600000) // 60000
        secs = (total_millis % 60000) // 1000
        millis = total_millis % 1000
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def generate_subtitles_local_whisper(self, audio_path: str) -> str:
        """
        Generates subtitles using local Whisper (faster-whisper).

        Args:
            audio_path (str): Audio file path

        Returns:
            path (str): Path to SRT file
        """
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            error(
                "Local STT selected but 'faster-whisper' is not installed. "
                "Install it or switch stt_provider to third_party_assemblyai."
            )
            raise

        model = WhisperModel(
            get_whisper_model(),
            device=get_whisper_device(),
            compute_type=get_whisper_compute_type(),
        )
        segments, _ = model.transcribe(audio_path, vad_filter=True)

        lines = []
        for idx, segment in enumerate(segments, start=1):
            start = self._format_srt_timestamp(segment.start)
            end = self._format_srt_timestamp(segment.end)
            text = str(segment.text).strip()

            if not text:
                continue

            lines.append(str(idx))
            lines.append(f"{start} --> {end}")
            lines.append(text)
            lines.append("")

        subtitles = "\n".join(lines)
        srt_path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + ".srt")
        with open(srt_path, "w", encoding="utf-8") as file:
            file.write(subtitles)

        return srt_path

    def _build_base_image_clip(self, image_path: str, duration: float):
        clip = ImageClip(image_path)
        clip = clip.set_duration(duration)
        clip = clip.set_fps(30)

        if round((clip.w / clip.h), 4) < 0.5625:
            if get_verbose():
                info(f" => Resizing Image: {image_path} to 1080x1920")
            clip = crop(
                clip,
                width=clip.w,
                height=round(clip.w / 0.5625),
                x_center=clip.w / 2,
                y_center=clip.h / 2,
            )
        else:
            if get_verbose():
                info(f" => Resizing Image: {image_path} to 1920x1080")
            clip = crop(
                clip,
                width=round(0.5625 * clip.h),
                height=clip.h,
                x_center=clip.w / 2,
                y_center=clip.h / 2,
            )

        return clip.resize((1080, 1920))

    def _build_motion_clip(self, image_path: str, duration: float, index: int):
        clip = self._build_base_image_clip(image_path, duration)

        if get_video_motion_style() != "cinematic":
            return clip

        zoom_intensity = get_video_zoom_intensity()
        pan_enabled = get_video_pan_enabled()
        pan_intensity = get_video_pan_intensity()

        motion_clip = clip.fl(
            lambda gf, t: render_motion_frame(
                gf(t),
                t=t,
                duration=duration,
                index=index,
                pan_enabled=pan_enabled,
                pan_intensity=pan_intensity,
                zoom_intensity=zoom_intensity,
            ),
            apply_to=["mask"],
        )
        return motion_clip.set_duration(duration).set_fps(30)

    def combine(self) -> str:
        """
        Combines everything into the final video.

        Returns:
            path (str): The path to the generated MP4 File.
        """
        combined_image_path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + ".mp4")
        threads = get_threads()
        tts_clip = AudioFileClip(self.tts_path)
        max_duration = tts_clip.duration
        req_dur = max_duration / len(self.images)

        # Make a generator that returns a TextClip when called with consecutive
        generator = lambda txt: TextClip(
            txt,
            font=os.path.join(get_fonts_dir(), get_font()),
            fontsize=100,
            color="#FFFF00",
            stroke_color="black",
            stroke_width=5,
            size=(1080, 1920),
            method="caption",
        )

        print(colored("[+] Combining images...", "blue"))

        clips = []
        tot_dur = 0
        # Add downloaded clips over and over until the duration of the audio (max_duration) has been reached
        while tot_dur < max_duration:
            for index, image_path in enumerate(self.images):
                clip = self._build_motion_clip(image_path, req_dur, index)
                clips.append(clip)
                tot_dur += clip.duration

        final_clip = concatenate_videoclips(clips)
        final_clip = final_clip.set_fps(30)
        random_song = choose_random_song()

        subtitles = None
        try:
            subtitles_path = self.generate_subtitles(self.tts_path)
            equalize_subtitles(subtitles_path, 10)
            subtitles = SubtitlesClip(subtitles_path, generator)
            subtitles.set_pos(("center", "center"))
        except Exception as e:
            raise RuntimeError(f"Failed to generate subtitles: {e}") from e

        random_song_clip = AudioFileClip(random_song).set_fps(44100)

        # Turn down volume
        random_song_clip = random_song_clip.fx(afx.volumex, 0.1)
        comp_audio = CompositeAudioClip([tts_clip.set_fps(44100), random_song_clip])

        final_clip = final_clip.set_audio(comp_audio)
        final_clip = final_clip.set_duration(tts_clip.duration)

        if subtitles is not None:
            final_clip = CompositeVideoClip([final_clip, subtitles])

        final_clip.write_videofile(combined_image_path, threads=threads, audio_codec="aac")

        success(f'Wrote Video to "{combined_image_path}"')

        return combined_image_path

    def generate_video(self, tts_instance: TTS) -> str:
        """
        Generates a YouTube Short based on the provided niche and language.

        Args:
            tts_instance (TTS): Instance of TTS Class.

        Returns:
            path (str): The path to the generated MP4 File.
        """
        # Generate the Topic
        self.generate_topic()

        # Generate the Script
        self.generate_script()

        # Generate the Metadata
        self.generate_metadata()

        # Generate the Image Prompts
        image_prompts = self.generate_prompts()

        # Generate the Images
        for prompt in image_prompts:
            image_path = self.generate_image(prompt)
            if not image_path:
                raise RuntimeError(f"Failed to generate image for prompt: {prompt}")

        # Generate the TTS
        self.generate_script_to_speech(tts_instance)

        # Combine everything
        path = self.combine()

        if get_verbose():
            info(f" => Generated Video: {path}")

        self.video_path = os.path.abspath(path)

        self.add_video(
            {
                "topic": self.subject,
                "script": self.script,
                "title": self.metadata["title"],
                "description": self.metadata["description"],
                "path": self.video_path,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "uploaded": False,
            }
        )

        return path

    def get_channel_id(self) -> str:
        """
        Gets the Channel ID of the YouTube Account.

        Returns:
            channel_id (str): The Channel ID.
        """
        driver = self.browser
        driver.get("https://studio.youtube.com")
        time.sleep(2)
        channel_id = driver.current_url.split("/")[-1]
        self.channel_id = channel_id

        return channel_id

    def _get_upload_metadata_textboxes(
        self,
        max_attempts: int = 10,
        delay_seconds: float = 1.0,
    ):
        """
        Waits for the YouTube Studio upload title and description textboxes.

        Returns:
            tuple: (title_element, description_element)
        """
        last_count = 0

        for _ in range(max_attempts):
            textboxes = self.browser.find_elements(By.ID, YOUTUBE_TEXTBOX_ID)
            last_count = len(textboxes)

            if last_count >= 2:
                return textboxes[0], textboxes[1]

            time.sleep(delay_seconds)

        raise RuntimeError(
            f"Could not find YouTube metadata textboxes after {max_attempts} attempts; found {last_count}."
        )

    def _set_upload_metadata_text(
        self,
        text_element,
        value: str,
        focus_delay_seconds: float = 0.5,
    ) -> None:
        self.browser.execute_script(
            """
            const element = arguments[0];
            const value = arguments[1];
            element.scrollIntoView({block: "center", inline: "nearest"});
            element.focus();
            element.textContent = value;
            element.innerText = value;
            element.dispatchEvent(new InputEvent("input", {
                bubbles: true,
                inputType: "insertText",
                data: value,
            }));
            element.dispatchEvent(new Event("change", { bubbles: true }));
            """,
            text_element,
            value,
        )
        time.sleep(focus_delay_seconds)

        applied_value = self.browser.execute_script(
            """
            return (arguments[0].innerText || arguments[0].textContent || "").trim();
            """,
            text_element,
        )

        normalized_expected = re.sub(r"\s+", " ", str(value or "")).strip()
        normalized_applied = re.sub(r"\s+", " ", str(applied_value or "")).strip()
        if normalized_expected != normalized_applied:
            raise RuntimeError(
                "Failed to apply YouTube metadata text; Studio kept a different value."
            )

    def upload_video(self) -> bool:
        """
        Uploads the video to YouTube.

        Returns:
            success (bool): Whether the upload was successful or not.
        """
        current_step = "initialize channel context"
        try:
            driver = self._ensure_browser()
            self.get_channel_id()

            driver = self.browser
            verbose = get_verbose()

            # Go to youtube.com/upload
            current_step = "open YouTube upload page"
            driver.get("https://www.youtube.com/upload")

            # Set video file
            current_step = "attach local video file"
            FILE_PICKER_TAG = "ytcp-uploads-file-picker"
            file_picker = driver.find_element(By.TAG_NAME, FILE_PICKER_TAG)
            INPUT_TAG = "input"
            file_input = file_picker.find_element(By.TAG_NAME, INPUT_TAG)
            file_input.send_keys(self.video_path)

            # Wait for upload to finish
            time.sleep(5)

            # Set title
            current_step = "load YouTube metadata textboxes"
            title_el, description_el = self._get_upload_metadata_textboxes()

            if verbose:
                info("\t=> Setting title...")

            current_step = "set video title"
            self._set_upload_metadata_text(
                title_el,
                self.metadata["title"],
                focus_delay_seconds=1,
            )

            if verbose:
                info("\t=> Setting description...")

            # Set description
            current_step = "set video description"
            time.sleep(10)
            self._set_upload_metadata_text(
                description_el,
                self.metadata["description"],
                focus_delay_seconds=0.5,
            )

            time.sleep(0.5)

            # Set `made for kids` option
            if verbose:
                info("\t=> Setting `made for kids` option...")

            current_step = "set audience selection"
            is_for_kids_checkbox = driver.find_element(
                By.NAME, YOUTUBE_MADE_FOR_KIDS_NAME
            )
            is_not_for_kids_checkbox = driver.find_element(
                By.NAME, YOUTUBE_NOT_MADE_FOR_KIDS_NAME
            )

            if not get_is_for_kids():
                is_not_for_kids_checkbox.click()
            else:
                is_for_kids_checkbox.click()

            time.sleep(0.5)

            # Click next
            if verbose:
                info("\t=> Clicking next...")

            current_step = "advance upload wizard"
            next_button = driver.find_element(By.ID, YOUTUBE_NEXT_BUTTON_ID)
            next_button.click()

            # Click next again
            if verbose:
                info("\t=> Clicking next again...")
            next_button = driver.find_element(By.ID, YOUTUBE_NEXT_BUTTON_ID)
            next_button.click()

            # Wait for 2 seconds
            time.sleep(2)

            # Click next again
            if verbose:
                info("\t=> Clicking next again...")
            next_button = driver.find_element(By.ID, YOUTUBE_NEXT_BUTTON_ID)
            next_button.click()

            # Set as unlisted
            if verbose:
                info("\t=> Setting as unlisted...")

            current_step = "set visibility to unlisted"
            radio_button = driver.find_elements(By.XPATH, YOUTUBE_RADIO_BUTTON_XPATH)
            radio_button[2].click()

            if verbose:
                info("\t=> Clicking done button...")

            # Click done button
            current_step = "finalize upload"
            done_button = driver.find_element(By.ID, YOUTUBE_DONE_BUTTON_ID)
            done_button.click()

            # Wait for 2 seconds
            time.sleep(2)

            # Get latest video
            if verbose:
                info("\t=> Getting video URL...")

            # Get the latest uploaded video URL
            current_step = "fetch uploaded short URL"
            driver.get(
                f"https://studio.youtube.com/channel/{self.channel_id}/videos/short"
            )
            time.sleep(2)
            videos = driver.find_elements(By.TAG_NAME, "ytcp-video-row")
            first_video = videos[0]
            anchor_tag = first_video.find_element(By.TAG_NAME, "a")
            href = anchor_tag.get_attribute("href")
            if verbose:
                info(f"\t=> Extracting video ID from URL: {href}")
            video_id = href.split("/")[-2]

            # Build URL
            url = build_url(video_id)

            self.uploaded_video_url = url

            if verbose:
                success(f" => Uploaded Video: {url}")

            # Add video to cache
            self.add_video(
                {
                    "topic": self.subject,
                    "script": self.script,
                    "title": self.metadata["title"],
                    "description": self.metadata["description"],
                    "path": self.video_path,
                    "url": url,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "uploaded": True,
                }
            )

            # Close the browser
            driver.quit()
            self.browser = None

            return True
        except Exception as e:
            error(f"Failed to upload YouTube video during step '{current_step}': {e}")
            try:
                self.browser.quit()
            except Exception:
                pass
            self.browser = None
            return False

    def get_videos(self) -> List[dict]:
        """
        Gets the uploaded videos from the YouTube Channel.

        Returns:
            videos (List[dict]): The uploaded videos.
        """
        if not os.path.exists(get_youtube_cache_path()):
            # Create the cache file
            with open(get_youtube_cache_path(), "w") as file:
                json.dump({"videos": []}, file, indent=4)
            return []

        videos = []
        # Read the cache file
        with open(get_youtube_cache_path(), "r") as file:
            previous_json = json.loads(file.read())
            # Find our account
            accounts = previous_json["accounts"]
            for account in accounts:
                if account["id"] == self._account_uuid:
                    videos = account["videos"]

        return videos
