import re
import json
import time
import os
import random
import requests
import assemblyai as aai

from utils import *
from cache import *
from .Tts import TTS
from llm_provider import generate_text
from config import *
from status import *
from uuid import uuid4
from constants import *
from typing import List
import numpy as np
from moviepy.editor import *
from termcolor import colored
from selenium_firefox import *
from selenium import webdriver
from moviepy.video.fx.all import crop
from moviepy.config import change_settings
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from moviepy.video.tools.subtitles import SubtitlesClip
from webdriver_manager.firefox import GeckoDriverManager
from datetime import datetime

# Set ImageMagick Path
change_settings({"IMAGEMAGICK_BINARY": get_imagemagick_path()})


class YouTube:
    """
    Class for YouTube Automation.

    Steps to create a YouTube Short:
    1. Generate a topic [DONE]
    2. Generate a script [DONE]
    3. Generate metadata (Title, Description, Tags) [DONE]
    4. Generate video search terms for Pexels [DONE]
    5. Download stock videos from Pexels [DONE]
    6. Convert Text-to-Speech [DONE]
    7. Crop & concatenate stock videos to fill TTS duration [DONE]
    8. Combine video + TTS + subtitles + overlays [DONE]
    """

    def __init__(
        self,
        account_uuid: str,
        account_nickname: str,
        fp_profile_path: str,
        niche: str,
        language: str,
        format_type: str = None,
    ) -> None:
        """
        Constructor for YouTube Class.

        Args:
            account_uuid (str): The unique identifier for the YouTube account.
            account_nickname (str): The nickname for the YouTube account.
            fp_profile_path (str): Path to the firefox profile that is logged into the specificed YouTube Account.
            niche (str): The niche of the provided YouTube Channel.
            language (str): The language of the Automation.
            format_type (str): Video format (ai_tool_showcase, before_after, etc.).

        Returns:
            None
        """
        self._account_uuid: str = account_uuid
        self._account_nickname: str = account_nickname
        self._fp_profile_path: str = fp_profile_path
        self._niche: str = niche
        self._language: str = language
        self._format_type: str = format_type or get_video_format()

        self.video_clips = []  # paths to downloaded Pexels stock videos
        self._browser = None  # Lazy init — only opened when needed

    def _ensure_browser(self) -> webdriver.Firefox:
        """Initializes the Firefox browser on first call, reuses on subsequent calls."""
        if self._browser is not None:
            return self._browser

        options = Options()

        if get_headless():
            options.add_argument("--headless")

        if not os.path.isdir(self._fp_profile_path):
            raise ValueError(
                f"Firefox profile path does not exist or is not a directory: {self._fp_profile_path}"
            )

        options.add_argument("-profile")
        options.add_argument(self._fp_profile_path)

        service = Service(GeckoDriverManager().install())

        firefox_bin = get_firefox_binary()
        if firefox_bin:
            options.binary_location = firefox_bin

        self._browser = webdriver.Firefox(service=service, options=options)
        return self._browser

    @property
    def browser(self) -> webdriver.Firefox:
        """Returns the browser instance, initializing it lazily if needed."""
        return self._ensure_browser()

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
        completion = self.generate_response(
            f"Please generate a specific video idea that takes about the following topic: {self.niche}. Make it exactly one sentence. Only return the topic, nothing else."
        )

        if not completion:
            error("Failed to generate Topic.")

        self.subject = completion

        return completion

    # -----------------------------------------------------------------
    # 2026 FORMAT YAPILARI — Strateji raporundan
    # -----------------------------------------------------------------
    FORMAT_STRUCTURES = {
        "ai_tool_showcase": {
            "duration": (45, 55),
            "structure": "Problem → Solution → Result",
        },
        "before_after": {
            "duration": (45, 60),
            "structure": "Before State → AI Application → After State",
        },
        "quick_tutorial": {
            "duration": (45, 60),
            "structure": "Goal → Step 1 → Step 2 → Step 3 → Result",
        },
        "ai_predictions": {
            "duration": (40, 50),
            "structure": "Question → AI Prediction → Surprising Result",
        },
        "myth_busting": {
            "duration": (45, 55),
            "structure": "False Belief → Truth → Evidence",
        },
        "ai_vs_human": {
            "duration": (45, 60),
            "structure": "Task → Human Attempt → AI Attempt → Comparison",
        },
    }

    def generate_script(self, _retry: int = 0) -> str:
        """
        Generate a script for a video using 2026 algorithm-optimized prompts.
        Applies: Hyper-Hook, Loop Bridge, Satisfaction-Focused, Format Structure.

        Returns:
            script (str): The script of the video.
        """
        MAX_RETRIES = 4
        sentence_length = get_script_sentence_length()

        # Format-based structure
        fmt = self.FORMAT_STRUCTURES.get(self._format_type, self.FORMAT_STRUCTURES["ai_tool_showcase"])
        dur_min, dur_max = fmt["duration"]
        structure = fmt["structure"]

        prompt = f"""Generate a script for a YouTube Shorts video in {sentence_length} sentences.

The script is to be returned as a plain string. No markdown, no formatting, no titles.

=== 2026 YOUTUBE ALGORITHM RULES (CRITICAL) ===
1. VIEWER SATISFACTION is the #1 metric (35% weight). Deliver genuine value, NOT clickbait.
2. WATCH COMPLETION / LOOP RATE is #2 (30% weight). Every sentence must keep the viewer watching.
3. REWATCH RATE is #3 (20% weight). The loop bridge at the end triggers rewatching.
4. The first 2 seconds = swipe or stay. The HOOK must stop the scroll instantly.

=== STRUCTURE RULES ===
1. HYPER-HOOK (Sentence 1): The FIRST sentence MUST be a powerful, curiosity-driven hook that summarizes the entire video's value in one breath. It must stop the swipe within 2 seconds. Make it dramatic and specific — NOT generic.
2. BODY (Sentences 2 to {sentence_length - 2}): Follow the "{structure}" structure. Deliver fast, clear, value-packed content. Every sentence must earn the next second of attention. Use SPECIFIC examples — name real tools, cite real data, give concrete numbers. Avoid vague filler sentences.
3. CTA (Second to last sentence): Encourage engagement — ask viewers to comment, share, or follow.
4. LOOP BRIDGE (LAST sentence): The final sentence MUST create semantic continuity with the FIRST sentence. When the video loops back to the beginning, it should feel seamless and natural. This is CRITICAL for the 2026 algorithm.

Target duration: {dur_min}-{dur_max} seconds of speech.
Video Format: {self._format_type}

=== QUALITY RULES ===
- Each sentence should be 8-15 words. Not too short, not too long.
- Use conversational, natural language. Sound like a real human talking to a friend.
- Include at least one surprising fact, statistic, or counterintuitive insight.
- Vary sentence rhythm — mix short punchy lines with slightly longer explanatory ones.
- Make every sentence earn its place. If it doesn't add value, cut it.

=== STRICT RULES ===
- MUST be exactly {sentence_length} sentences. No more, no less.
- NO markdown, NO formatting, NO titles.
- Write in the language: {self.language}
- Get straight to the point. No "welcome to this video" or similar waste.
- DO NOT mention the prompt or the script itself.
- ONLY return the raw script text.

Subject: {self.subject}
Language: {self.language}
"""
        completion = self.generate_response(prompt)

        # Apply regex to remove *
        completion = re.sub(r"\*", "", completion)

        if not completion:
            error("The generated script is empty.")
            return

        if len(completion) > 5000:
            if _retry >= MAX_RETRIES:
                warning("Script still too long after retries. Truncating.")
                completion = completion[:5000]
            else:
                if get_verbose():
                    warning(f"Generated Script is too long. Retrying ({_retry + 1}/{MAX_RETRIES})...")
                return self.generate_script(_retry + 1)

        self.script = completion

        return completion

    def generate_hook_text(self) -> str:
        """
        Generates a short, punchy hook text to overlay on the first 2 seconds of the video.
        This is a VISUAL overlay, separate from the spoken script.

        Returns:
            hook_text (str): The hook overlay text.
        """
        prompt = f"""Generate a very short, dramatic hook text for a video overlay (max 8 words).
This text will appear on screen in the first 2 seconds to grab attention.
It should create curiosity and urgency.

Examples:
- "WATCH TILL THE END..."
- "THIS CHANGES EVERYTHING"
- "YOU NEED TO HEAR THIS"
- "MOST PEOPLE DON'T KNOW THIS"
- "WAIT FOR IT..."

Make it related to this subject: {self.subject}
Language: {self.language}

Return ONLY the hook text in ALL CAPS, nothing else. No quotes, no explanation."""

        hook = self.generate_response(prompt).strip().strip('"').strip("'")
        # Ensure it's uppercase and not too long
        hook = hook.upper()
        if len(hook) > 60:
            hook = hook[:60]

        self.hook_text = hook
        if get_verbose():
            info(f" => Generated hook text: {hook}")

        return hook

    def generate_cta_text(self) -> str:
        """
        Generates a short call-to-action text to overlay on the last 3 seconds of the video,
        encouraging viewers to leave a comment.

        Returns:
            cta_text (str): The CTA overlay text.
        """
        prompt = f"""Generate a very short call-to-action text for a video overlay (max 8 words).
This text will appear on screen at the end to encourage viewers to comment.

Examples:
- "COMMENT BELOW! 👇"
- "DROP YOUR ANSWER 👇"
- "WHAT DO YOU THINK? 💬"
- "TELL ME IN COMMENTS 👇"
- "AGREE OR DISAGREE? 💬"

Subject: {self.subject}
Language: {self.language}

Return ONLY the CTA text in ALL CAPS, nothing else. No quotes, no explanation."""

        cta = self.generate_response(prompt).strip().strip('"').strip("'")
        cta = cta.upper()
        if len(cta) > 60:
            cta = cta[:60]

        self.cta_text = cta
        if get_verbose():
            info(f" => Generated CTA text: {cta}")

        return cta

    def generate_metadata(self, _retry: int = 0) -> dict:
        """
        Generates Video metadata for the to-be-uploaded YouTube Short (Title, Description).
        Follows YouTube Shorts SEO best practices:
        - Title: 40-70 chars, keyword-first, curiosity-driven, NO hashtags
        - Description: 1-3 sentence summary + 3-5 hashtags at bottom

        Returns:
            metadata (dict): The generated metadata.
        """
        MAX_RETRIES = 4

        # ── TITLE ──────────────────────────────────────────────────
        title_prompt = f"""Generate a YouTube Shorts title for the following subject.

Subject: {self.subject}
Language: {self.language}

STRICT RULES:
1. LENGTH: The title MUST be between 40 and 70 characters. This is critical — titles over 70 characters get cut off on mobile.
2. KEYWORD FIRST: Put the most important keyword(s) at the very beginning of the title (e.g. "AI", "LLM", "ChatGPT", etc.).
3. CURIOSITY + CLARITY: The title must clearly tell what the video is about AND trigger curiosity/emotion. Avoid clickbait that doesn't match content.
4. NO HASHTAGS in the title. Keep it clean.
5. NO quotation marks around the title.
6. NO emojis in the title.

Good examples:
- "AI is hiding this from you"
- "3 things LLMs can do that will shock you"
- "ChatGPT just made this job obsolete"
- "This AI tool replaces your entire workflow"

Return ONLY the title text, nothing else."""

        title = self.generate_response(title_prompt).strip().strip('"').strip("'")

        # Remove any hashtags the LLM might have sneaked in
        title = re.sub(r'#\S+', '', title).strip()

        # Validate length
        if len(title) > 70:
            if _retry >= MAX_RETRIES:
                warning("Title still too long after retries. Truncating to 70 chars.")
                # Try to truncate at last space before 70
                truncated = title[:70]
                last_space = truncated.rfind(' ')
                if last_space > 30:
                    title = truncated[:last_space]
                else:
                    title = truncated
            else:
                if get_verbose():
                    warning(f"Generated Title is {len(title)} chars (max 70). Retrying ({_retry + 1}/{MAX_RETRIES})...")
                return self.generate_metadata(_retry + 1)

        # ── DESCRIPTION (SEO Optimized — 2026) ─────────────────
        description_prompt = f"""Generate a YouTube Shorts description for the following video.

Subject: {self.subject}
Script: {self.script}
Language: {self.language}

STRICT RULES:
1. FIRST 1-2 LINES: Write a short, compelling summary of what the video covers and what the viewer will learn. This is the most visible part on mobile — make it count.
2. NATURAL KEYWORDS: Naturally weave in relevant keywords (like "AI", "LLM", "machine learning", "automation", etc.) — do NOT keyword-stuff.
3. TOTAL LENGTH: 1-3 sentences for the summary. Keep it concise and meaningful.
4. HASHTAGS: After the summary, leave one blank line, then add exactly 3-5 relevant hashtags. Include #shorts as one of them.
5. NO quotation marks around the description.

Example format:
This AI tool just replaced an entire marketing team in under 60 seconds. Here's how it works and why you need to try it today.

#shorts #AI #Automation #ArtificialIntelligence #TechTips

Return ONLY the description, nothing else."""

        description = self.generate_response(description_prompt).strip().strip('"').strip("'")

        self.metadata = {"title": title, "description": description}

        if get_verbose():
            info(f" => Title ({len(title)} chars): {title}")
            info(f" => Description: {description[:100]}...")

        return self.metadata

    def generate_video_search_terms(self, _retry: int = 0) -> List[str]:
        """
        Uses the LLM to generate English search terms for Pexels stock video API
        based on the video script/subject.

        Returns:
            search_terms (List[str]): 3-5 English search terms.
        """
        MAX_RETRIES = 5
        n_terms = 5  # we ask for 5 terms to have variety

        prompt = f"""Generate exactly {n_terms} short English search terms for finding stock videos on Pexels.com.

Subject: {self.subject}
Script: {self.script}

Rules:
- Return ONLY a valid JSON array of strings, nothing else.
- Each term must be 1-4 words in ENGLISH, even if the subject is in another language.
- Terms should describe VISUAL scenes, actions, or atmospheres that match the video content.
- Think like a video editor picking B-roll footage: dramatic, cinematic, relevant.
- Prefer vertical/portrait-friendly scenes (close-ups, people, nature, abstract).
- Do NOT include terms with text overlays or logos.

Examples:
["hacker typing dark room", "futuristic city night", "money falling slow motion", "abstract technology background", "person thinking close up"]

Return ONLY the JSON array."""

        raw = str(self.generate_response(prompt))

        completion = (
            raw
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        search_terms = []

        try:
            parsed = json.loads(completion)
            if isinstance(parsed, list):
                search_terms = [str(t).strip() for t in parsed if str(t).strip()]
        except Exception:
            if get_verbose():
                warning("LLM returned unformatted response for search terms. Attempting to clean...")

            r = re.compile(r"\[.*?\]", re.DOTALL)
            matches = r.findall(completion)
            for match in matches:
                try:
                    parsed = json.loads(match)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        search_terms = [str(t).strip() for t in parsed if str(t).strip()]
                        break
                except Exception:
                    continue

        if len(search_terms) == 0:
            if _retry >= MAX_RETRIES:
                warning(f"Failed to generate search terms after {MAX_RETRIES} retries. Using fallback.")
                search_terms = [self.niche, "cinematic background", "abstract motion"]
            else:
                if get_verbose():
                    warning(f"Failed to parse search terms. Retrying ({_retry + 1}/{MAX_RETRIES})...")
                return self.generate_video_search_terms(_retry + 1)

        if len(search_terms) > n_terms:
            search_terms = search_terms[:n_terms]

        self.search_terms = search_terms

        success(f"Generated {len(search_terms)} video search terms: {search_terms}")

        return search_terms

    def search_pexels_videos(self, query: str, per_page: int = 15, orientation: str = "portrait") -> List[dict]:
        """
        Searches Pexels API for stock videos matching the query.

        Args:
            query (str): Search term
            per_page (int): Number of results per page
            orientation (str): Video orientation (portrait, landscape, square)

        Returns:
            videos (List[dict]): List of video result dicts from Pexels API.
        """
        api_key = get_pexels_api_key()
        if not api_key:
            error("pexels_api_key is not configured in config.json.")
            return []

        url = "https://api.pexels.com/videos/search"
        headers = {"Authorization": api_key}
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": orientation,
            "size": "medium",  # medium = HD quality, not 4K (faster download)
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("videos", [])
        except Exception as e:
            warning(f"Pexels API search failed for '{query}': {e}")
            return []

    def _pick_best_video_file(self, video_data: dict) -> str | None:
        """
        From a Pexels video result, picks the best HD file URL.
        Prefers: HD quality (1280x720 or 1920x1080), mp4 format.

        Args:
            video_data (dict): Single video result from Pexels API.

        Returns:
            url (str | None): Direct download URL for the video file.
        """
        video_files = video_data.get("video_files", [])
        if not video_files:
            return None

        # Sort by height descending, prefer HD (720-1080p)
        candidates = [
            vf for vf in video_files
            if vf.get("file_type", "") == "video/mp4"
            and vf.get("height", 0) >= 720
        ]
        # Sort by height: prefer 1080 > 720 > others
        candidates.sort(key=lambda vf: abs(vf.get("height", 0) - 1080))

        if candidates:
            return candidates[0].get("link")

        # Fallback: pick highest quality mp4
        mp4s = [vf for vf in video_files if vf.get("file_type", "") == "video/mp4"]
        if mp4s:
            mp4s.sort(key=lambda vf: vf.get("height", 0), reverse=True)
            return mp4s[0].get("link")

        return None

    def download_pexels_video(self, video_url: str) -> str | None:
        """
        Downloads a video file from Pexels and saves it locally.

        Args:
            video_url (str): Direct download URL.

        Returns:
            path (str | None): Local path to the downloaded video.
        """
        try:
            response = requests.get(video_url, timeout=120, stream=True)
            response.raise_for_status()

            video_path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + ".mp4")
            with open(video_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)

            if get_verbose():
                info(f' => Downloaded Pexels video to "{video_path}"')

            self.video_clips.append(video_path)
            return video_path

        except Exception as e:
            warning(f"Failed to download Pexels video: {e}")
            return None

    def fetch_stock_videos(self) -> List[str]:
        """
        Uses search terms to fetch and download stock videos from Pexels.
        Aims to get at least 3 usable clips.

        Returns:
            paths (List[str]): List of local video file paths.
        """
        downloaded = []
        used_video_ids = set()  # avoid duplicates

        for term in self.search_terms:
            if len(downloaded) >= 5:
                break

            if get_verbose():
                info(f" => Searching Pexels for: '{term}'")

            results = self.search_pexels_videos(term)

            # Shuffle results to add variety across runs
            if results:
                random.shuffle(results)

            for video_data in results:
                if len(downloaded) >= 5:
                    break

                video_id = video_data.get("id")
                if video_id in used_video_ids:
                    continue

                file_url = self._pick_best_video_file(video_data)
                if not file_url:
                    continue

                path = self.download_pexels_video(file_url)
                if path:
                    downloaded.append(path)
                    used_video_ids.add(video_id)
                    break  # one video per search term to get variety

        if len(downloaded) < 2:
            # Emergency fallback: search generic terms
            for fallback_term in ["abstract background motion", "cinematic nature", "technology dark"]:
                if len(downloaded) >= 3:
                    break
                results = self.search_pexels_videos(fallback_term)
                if results:
                    random.shuffle(results)
                    for video_data in results[:2]:
                        video_id = video_data.get("id")
                        if video_id in used_video_ids:
                            continue
                        file_url = self._pick_best_video_file(video_data)
                        if file_url:
                            path = self.download_pexels_video(file_url)
                            if path:
                                downloaded.append(path)
                                used_video_ids.add(video_id)
                                break

        success(f"Downloaded {len(downloaded)} stock videos from Pexels.")
        return downloaded

    def generate_script_to_speech(self, tts_instance: TTS) -> str:
        """
        Converts the generated script into Speech using KittenTTS and returns the path to the wav file.

        Args:
            tts_instance (tts): Instance of TTS Class.

        Returns:
            path_to_wav (str): Path to generated audio (WAV Format).
        """
        path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + ".wav")

        # Clean script: allow word characters, spaces, and essential punctuation for TTS pacing (. ? ! , ' -)
        self.script = re.sub(r"[^\w\s.?!,'-]", "", self.script)

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
        videos = self.get_videos()
        videos.append(video)

        cache = get_youtube_cache_path()

        with open(cache, "r") as file:
            previous_json = json.loads(file.read())

            # Find our account
            accounts = previous_json["accounts"]
            for account in accounts:
                if account["id"] == self._account_uuid:
                    account["videos"].append(video)

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
        segments, _ = model.transcribe(audio_path, vad_filter=True, word_timestamps=True)

        lines = []
        idx = 1
        for segment in segments:
            if not segment.words:
                # Fallback if no words are returned
                start = self._format_srt_timestamp(segment.start)
                end = self._format_srt_timestamp(segment.end)
                text = str(segment.text).strip()
                if text:
                    lines.append(str(idx))
                    lines.append(f"{start} --> {end}")
                    lines.append(text)
                    lines.append("")
                    idx += 1
                continue
                
            for word_obj in segment.words:
                start = self._format_srt_timestamp(word_obj.start)
                end = self._format_srt_timestamp(word_obj.end)
                text = str(word_obj.word).strip()

                if not text:
                    continue

                lines.append(str(idx))
                lines.append(f"{start} --> {end}")
                lines.append(text)
                lines.append("")
                idx += 1

        subtitles = "\n".join(lines)
        srt_path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + ".srt")
        with open(srt_path, "w", encoding="utf-8") as file:
            file.write(subtitles)

        return srt_path

    def _make_overlay_clip(self, text: str, duration: float, fontsize: int = 80,
                          color: str = "#FFFFFF", bg_color: str = "black",
                          position: tuple = ("center", 200)) -> VideoClip:
        """
        Creates a premium text overlay clip with shadow effect for depth.
        Uses a two-layer approach: shadow layer + main text for a professional look.

        Args:
            text (str): Text to display
            duration (float): Duration in seconds
            fontsize (int): Font size
            color (str): Text color
            bg_color (str): Stroke/outline color
            position (tuple): Position on screen

        Returns:
            clip (VideoClip): The overlay clip
        """
        font_path = os.path.join(get_fonts_dir(), get_font())

        # Shadow layer — offset slightly for depth
        shadow_clip = TextClip(
            text,
            font=font_path,
            fontsize=fontsize,
            color="#000000",
            stroke_color="#000000",
            stroke_width=8,
            size=(960, None),
            method="caption",
            align="center",
        ).set_opacity(0.6)

        # Main text layer — crisp with strong outline
        main_clip = TextClip(
            text,
            font=font_path,
            fontsize=fontsize,
            color=color,
            stroke_color=bg_color,
            stroke_width=6,
            size=(960, None),
            method="caption",
            align="center",
        )

        # Compose shadow + main text (shadow offset by 4px down-right)
        pos_x = position[0]
        pos_y = position[1] if isinstance(position[1], str) else position[1]

        shadow_clip = shadow_clip.set_duration(duration)
        main_clip = main_clip.set_duration(duration)

        if isinstance(pos_y, int) or isinstance(pos_y, float):
            shadow_clip = shadow_clip.set_pos((pos_x, pos_y + 4))
            main_clip = main_clip.set_pos(position)
        else:
            shadow_clip = shadow_clip.set_pos(position)
            main_clip = main_clip.set_pos(position)

        combined = CompositeVideoClip(
            [shadow_clip, main_clip],
            size=(1080, 1920)
        ).set_duration(duration)

        # Smooth fade in/out
        combined = combined.crossfadein(0.3).crossfadeout(0.3)
        return combined

    def _crop_to_vertical(self, clip: VideoClip) -> VideoClip:
        """
        Center-crops a video clip to 9:16 aspect ratio (1080x1920).
        If the clip is already vertical, it resizes to fit.

        Args:
            clip (VideoClip): Input video clip

        Returns:
            clip (VideoClip): Cropped/resized clip
        """
        target_w, target_h = 1080, 1920
        target_ratio = target_w / target_h  # 0.5625

        src_w, src_h = clip.w, clip.h
        src_ratio = src_w / src_h

        if abs(src_ratio - target_ratio) < 0.05:
            # Already roughly 9:16 — just resize
            return clip.resize((target_w, target_h))

        if src_ratio > target_ratio:
            # Video is wider than 9:16 — crop sides
            new_w = int(src_h * target_ratio)
            x_center = src_w / 2
            clip = crop(clip, x_center=x_center, width=new_w, height=src_h)
        else:
            # Video is taller than 9:16 — crop top/bottom
            new_h = int(src_w / target_ratio)
            y_center = src_h / 2
            clip = crop(clip, y_center=y_center, width=src_w, height=new_h)

        return clip.resize((target_w, target_h))

    def _apply_ken_burns(self, clip: VideoClip, zoom_range: tuple = (1.05, 1.15)) -> VideoClip:
        """
        Applies Ken Burns effect (slow zoom + pan) to a video clip for dynamism.
        Each call uses a random direction to break monotony.

        Args:
            clip (VideoClip): Input video clip
            zoom_range (tuple): Min and max zoom factors

        Returns:
            clip (VideoClip): Clip with Ken Burns effect applied
        """
        w, h = clip.w, clip.h
        zoom_start = 1.0
        zoom_end = random.uniform(*zoom_range)
        # Random pan direction
        pan_x = random.uniform(-0.02, 0.02)  # percentage of width
        pan_y = random.uniform(-0.02, 0.02)  # percentage of height

        duration = clip.duration

        def make_frame(get_frame, t):
            progress = t / max(duration, 0.01)
            current_zoom = zoom_start + (zoom_end - zoom_start) * progress

            # Calculate crop region
            new_w = int(w / current_zoom)
            new_h = int(h / current_zoom)
            cx = int(w / 2 + pan_x * w * progress)
            cy = int(h / 2 + pan_y * h * progress)

            # Clamp bounds
            x1 = max(0, min(cx - new_w // 2, w - new_w))
            y1 = max(0, min(cy - new_h // 2, h - new_h))
            x2 = x1 + new_w
            y2 = y1 + new_h

            frame = get_frame(t)
            cropped = frame[y1:y2, x1:x2]

            # Resize back to original dimensions
            from PIL import Image
            img = Image.fromarray(cropped)
            img = img.resize((w, h), Image.LANCZOS)
            return np.array(img)

        return clip.fl(make_frame)

    def _create_loop_bridge(self, clips: list, crossfade_duration: float = 0.5) -> list:
        """
        Creates loop architecture by adding a crossfade transition
        from the last clip segment back to the first.
        The last 0.5s fades into content similar to the first 0.5s,
        so when YouTube loops the video it feels seamless.

        Args:
            clips (list): List of video clip segments
            crossfade_duration (float): Duration of the crossfade

        Returns:
            clips (list): Modified clips list with loop bridge applied
        """
        if len(clips) < 2:
            return clips

        try:
            # Apply crossfade-out to the last clip
            last_clip = clips[-1]
            if last_clip.duration > crossfade_duration * 2:
                clips[-1] = last_clip.crossfadeout(crossfade_duration)

            # Apply crossfade-in to the first clip
            first_clip = clips[0]
            if first_clip.duration > crossfade_duration * 2:
                clips[0] = first_clip.crossfadein(crossfade_duration)

            if get_verbose():
                info(f" => Loop bridge applied: {crossfade_duration}s crossfade")
        except Exception as e:
            warning(f"Failed to apply loop bridge: {e}")

        return clips

    def combine(self) -> str:
        """
        Combines downloaded stock videos with TTS audio, subtitles, and overlays
        into the final YouTube Shorts video.

        Returns:
            path (str): The path to the generated MP4 File.
        """
        output_path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + ".mp4")
        threads = get_threads()
        tts_clip = AudioFileClip(self.tts_path)
        max_duration = tts_clip.duration

        # Subtitle generator — premium viral style
        # Bright white with thick dark outline for maximum readability on any background
        generator = lambda txt: TextClip(
            txt,
            font=os.path.join(get_fonts_dir(), get_font()),
            fontsize=110,
            color="#FFFFFF",
            stroke_color="#000000",
            stroke_width=7,
            size=(950, None),
            method="caption",
            align="center",
        )

        print(colored("[+] Combining stock videos...", "blue"))

        # Load all downloaded stock video clips
        raw_clips = []
        use_ken_burns = get_enable_ken_burns()
        for vpath in self.video_clips:
            try:
                vc = VideoFileClip(vpath)
                vc = self._crop_to_vertical(vc)
                vc = vc.set_fps(30)
                # Remove original audio from stock video (we'll use TTS)
                vc = vc.without_audio()
                # Apply Ken Burns effect if enabled (2026 Strateji: dinamiklik)
                if use_ken_burns:
                    try:
                        vc = self._apply_ken_burns(vc)
                    except Exception as kb_err:
                        warning(f"Ken Burns failed for '{vpath}', using original: {kb_err}")
                raw_clips.append(vc)
            except Exception as e:
                warning(f"Failed to load stock video '{vpath}': {e}")

        if not raw_clips:
            error("No usable stock videos available. Cannot create video.")
            raise RuntimeError("No stock videos to combine.")

        # Build the timeline: loop through clips until we fill max_duration
        clips = []
        tot_dur = 0
        clip_idx = 0

        while tot_dur < max_duration:
            source_clip = raw_clips[clip_idx % len(raw_clips)]
            remaining = max_duration - tot_dur

            if remaining <= 0:
                break

            # Use each clip at its natural duration, or trim to remaining time
            segment_duration = min(source_clip.duration, remaining)

            if segment_duration < 0.5:
                break  # too short, just stop

            segment = source_clip.subclip(0, segment_duration)
            clips.append(segment)
            tot_dur += segment_duration
            clip_idx += 1

        # Apply loop architecture if enabled (2026 Strateji: Trend 4)
        if get_enable_loop():
            clips = self._create_loop_bridge(clips)

        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip = final_clip.set_fps(30)

        # Background music policy (2026 Strateji: orijinal ses = %100 Creator Pool)
        random_song_clip = None
        if get_use_background_music():
            try:
                random_song = choose_random_song()
                random_song_clip = AudioFileClip(random_song).set_fps(44100)
                random_song_clip = random_song_clip.fx(afx.volumex, 0.15)
            except Exception as e:
                warning(f"No background music available, continuing without it: {e}")
        else:
            if get_verbose():
                info(" => Background music disabled (original audio policy)")

        subtitles = None
        try:
            subtitles_path = self.generate_subtitles(self.tts_path)
            equalize_subtitles(subtitles_path, 10)
            subtitles = SubtitlesClip(subtitles_path, generator)
            subtitles = subtitles.set_pos(("center", 1300))
        except Exception as e:
            warning(f"Failed to generate subtitles, continuing without subtitles: {e}")

        if random_song_clip is not None:
            comp_audio = CompositeAudioClip([tts_clip.set_fps(44100), random_song_clip])
        else:
            comp_audio = tts_clip.set_fps(44100)

        final_clip = final_clip.set_audio(comp_audio)
        final_clip = final_clip.set_duration(tts_clip.duration)

        # Build the list of overlay layers
        overlay_layers = [final_clip]

        # Add subtitles layer
        if subtitles is not None:
            overlay_layers.append(subtitles)

        # HOOK OVERLAY — first 3 seconds, top area with premium styling
        hook_duration = min(3.0, max_duration * 0.3)
        try:
            hook_text = getattr(self, 'hook_text', 'WATCH TILL THE END...')
            hook_clip = self._make_overlay_clip(
                text=hook_text,
                duration=hook_duration,
                fontsize=95,
                color="#FFD700",
                bg_color="#111111",
                position=("center", 260),
            )
            hook_clip = hook_clip.set_start(0)
            overlay_layers.append(hook_clip)
            if get_verbose():
                info(f' => Added hook overlay: "{hook_text}" ({hook_duration:.1f}s)')
        except Exception as e:
            warning(f"Failed to create hook overlay, continuing without it: {e}")

        # CTA OVERLAY — last 3.5 seconds, lower area with premium styling
        cta_duration = min(3.5, max_duration * 0.3)
        cta_start = max(0, max_duration - cta_duration)
        try:
            cta_text = getattr(self, 'cta_text', 'COMMENT BELOW! 👇')
            cta_clip = self._make_overlay_clip(
                text=cta_text,
                duration=cta_duration,
                fontsize=90,
                color="#00FF88",
                bg_color="#111111",
                position=("center", 1480),
            )
            cta_clip = cta_clip.set_start(cta_start)
            overlay_layers.append(cta_clip)
            if get_verbose():
                info(f' => Added CTA overlay: "{cta_text}" (starts at {cta_start:.1f}s, {cta_duration:.1f}s)')
        except Exception as e:
            warning(f"Failed to create CTA overlay, continuing without it: {e}")

        # Compose all layers
        final_clip = CompositeVideoClip(overlay_layers)

        final_clip.write_videofile(
            output_path,
            threads=threads,
            codec="libx264",
            audio_codec="aac",
            bitrate="8000k",
            audio_bitrate="192k",
            preset="medium",
            ffmpeg_params=["-pix_fmt", "yuv420p"],
        )

        success(f'Wrote Video to "{output_path}"')

        return output_path

    def generate_video(self, tts_instance: TTS) -> str:
        """
        Generates a YouTube Short based on the provided niche and language.
        Uses Pexels stock videos instead of AI-generated images.

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

        # Generate hook and CTA overlay texts
        self.generate_hook_text()
        self.generate_cta_text()

        # Generate search terms for stock videos
        self.generate_video_search_terms()

        # Download stock videos from Pexels
        self.fetch_stock_videos()

        # Generate the TTS
        self.generate_script_to_speech(tts_instance)

        # Combine everything
        path = self.combine()

        if get_verbose():
            info(f" => Generated Video: {path}")

        self.video_path = os.path.abspath(path)

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

    def upload_video(self) -> bool:
        """
        Uploads the video to YouTube.

        Returns:
            success (bool): Whether the upload was successful or not.
        """
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        WAIT_TIMEOUT = 30

        if not hasattr(self, 'video_path') or not self.video_path:
            error("No video path set. Generate a video first.")
            return False

        if not os.path.isfile(self.video_path):
            error(f"Video file not found: {self.video_path}")
            return False

        try:
            self.get_channel_id()

            driver = self.browser
            verbose = get_verbose()
            wait = WebDriverWait(driver, WAIT_TIMEOUT)

            if verbose:
                info("\t=> Navigating to YouTube upload page...")
            driver.get("https://www.youtube.com/upload")

            if verbose:
                info("\t=> Selecting video file...")
            file_picker = wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "ytcp-uploads-file-picker"))
            )
            file_input = file_picker.find_element(By.TAG_NAME, "input")
            file_input.send_keys(self.video_path)

            if verbose:
                info("\t=> Waiting for upload form...")
            time.sleep(5)

            textboxes = wait.until(
                lambda d: d.find_elements(By.ID, YOUTUBE_TEXTBOX_ID) if len(d.find_elements(By.ID, YOUTUBE_TEXTBOX_ID)) >= 2 else False
            )

            from selenium.webdriver.common.keys import Keys
            import sys
            
            # YouTube Studio fields are contenteditable divs, so .clear() often fails.
            # We must use keyboard shortcuts to select all and delete.
            modifier = Keys.COMMAND if sys.platform == "darwin" else Keys.CONTROL

            title_el = textboxes[0]
            description_el = textboxes[-1]

            if verbose:
                info("\t=> Setting title...")
            time.sleep(1)
            title_el.click()
            time.sleep(1)
            title_el.send_keys(modifier, "a")
            time.sleep(0.5)
            title_el.send_keys(Keys.DELETE)
            time.sleep(0.5)
            title_el.send_keys(self.metadata["title"])

            if verbose:
                info("\t=> Setting description...")
            time.sleep(5)
            description_el.click()
            time.sleep(1)
            description_el.send_keys(modifier, "a")
            time.sleep(0.5)
            description_el.send_keys(Keys.DELETE)
            time.sleep(0.5)
            description_el.send_keys(self.metadata["description"])
            time.sleep(1)

            if verbose:
                info("\t=> Setting `made for kids` option...")

            # YouTube Studio wraps the "made for kids" options inside a
            # collapsible section.  We must:
            #   1. Scroll the section into view.
            #   2. Expand the section if it is collapsed.
            #   3. Click the appropriate radio button.

            # Step 1 — scroll to and expand the audience section
            try:
                # The radio buttons live inside <ytcp-video-metadata-audience>
                audience_section = wait.until(
                    EC.presence_of_element_located(
                        (By.TAG_NAME, "ytcp-video-metadata-audience")
                    )
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", audience_section
                )
                time.sleep(1)
            except Exception:
                if verbose:
                    warning("\t=> Could not locate audience section wrapper — continuing anyway.")

            # Step 2 — locate the radio buttons (retry up to 3 times)
            is_not_for_kids_checkbox = None
            is_for_kids_checkbox = None

            for _attempt in range(3):
                try:
                    is_not_for_kids_checkbox = driver.find_element(
                        By.NAME, YOUTUBE_NOT_MADE_FOR_KIDS_NAME
                    )
                    is_for_kids_checkbox = driver.find_element(
                        By.NAME, YOUTUBE_MADE_FOR_KIDS_NAME
                    )
                    break
                except Exception:
                    if verbose:
                        warning(
                            f"\t=> Kids radio buttons not found (attempt {_attempt + 1}/3). "
                            "Trying to expand the section..."
                        )
                    # Try clicking possible expand toggles
                    for selector in [
                        "ytcp-video-metadata-audience #audience button",
                        "ytcp-video-metadata-audience tp-yt-paper-radio-group",
                        "#audience",
                    ]:
                        try:
                            toggle = driver.find_element(By.CSS_SELECTOR, selector)
                            driver.execute_script(
                                "arguments[0].scrollIntoView({block:'center'});", toggle
                            )
                            toggle.click()
                            time.sleep(1)
                        except Exception:
                            continue
                    time.sleep(2)

            # Step 3 — click the correct option
            target = (
                is_for_kids_checkbox if get_is_for_kids() else is_not_for_kids_checkbox
            )
            if target:
                try:
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});", target
                    )
                    time.sleep(0.5)
                    target.click()
                except Exception:
                    # Fallback: use JS click
                    try:
                        driver.execute_script("arguments[0].click();", target)
                    except Exception as click_err:
                        warning(f"\t=> Failed to click kids option: {click_err}")
            else:
                warning(
                    "\t=> Could not find 'made for kids' radio buttons. "
                    "Upload may require manual intervention on this step."
                )
            time.sleep(0.5)

            for step_num in range(3):
                if verbose:
                    info(f"\t=> Clicking next (step {step_num + 1}/3)...")
                next_button = wait.until(
                    EC.element_to_be_clickable((By.ID, YOUTUBE_NEXT_BUTTON_ID))
                )
                next_button.click()
                time.sleep(2)

            if verbose:
                info("\t=> Setting as unlisted...")
            radio_buttons = wait.until(
                lambda d: d.find_elements(By.XPATH, YOUTUBE_RADIO_BUTTON_XPATH) if len(d.find_elements(By.XPATH, YOUTUBE_RADIO_BUTTON_XPATH)) >= 3 else False
            )
            radio_buttons[2].click()

            if verbose:
                info("\t=> Clicking done button...")
            done_button = wait.until(
                EC.element_to_be_clickable((By.ID, YOUTUBE_DONE_BUTTON_ID))
            )
            done_button.click()
            time.sleep(5)

            if verbose:
                info("\t=> Getting video URL...")
            driver.get(
                f"https://studio.youtube.com/channel/{self.channel_id}/videos/short"
            )

            # Wait for video rows to appear
            time.sleep(4)
            href = None
            for _ in range(10):
                try:
                    videos = driver.find_elements(By.TAG_NAME, "ytcp-video-row")
                    if videos:
                        # Try to find exactly the '#video-title' anchor tag instead of just any 'a'
                        anchor_tag = videos[0].find_element(By.ID, "video-title")
                        href = anchor_tag.get_attribute("href")
                        if href:
                            break
                except Exception:
                    pass
                time.sleep(2)

            if verbose:
                info(f"\t=> Extracting video ID from URL: {href}")
            
            if href:
                video_id = href.split("/")[-2]
                url = build_url(video_id)
            else:
                warning("\t=> Could not extract video URL properly. Using generic studio link.")
                url = f"https://studio.youtube.com/channel/{self.channel_id}/videos/short"
            self.uploaded_video_url = url

            if verbose:
                success(f" => Uploaded Video: {url}")

            self.add_video(
                {
                    "title": self.metadata["title"],
                    "description": self.metadata["description"],
                    "url": url,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

            return True

        except Exception as e:
            error(f"Upload failed: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"YouTube Studio Error: {str(e)}")

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
