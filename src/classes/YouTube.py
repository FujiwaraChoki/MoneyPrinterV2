import re
import base64
import json
import time
import os
import shutil
import sys
import subprocess
import requests
from difflib import SequenceMatcher
from urllib.parse import parse_qs
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
    "back",
    "became",
    "behind",
    "brand",
    "built",
    "business",
    "case",
    "channel",
    "company",
    "content",
    "created",
    "creator",
    "creators",
    "culture",
    "deaths",
    "deadly",
    "disappearance",
    "disaster",
    "documentary",
    "dollar",
    "dollars",
    "economy",
    "empire",
    "entire",
    "event",
    "explained",
    "failed",
    "failure",
    "followed",
    "for",
    "from",
    "ghost",
    "grew",
    "growth",
    "history",
    "historical",
    "how",
    "incident",
    "in",
    "inside",
    "internet",
    "into",
    "made",
    "makes",
    "market",
    "media",
    "million",
    "millions",
    "model",
    "money",
    "mysteries",
    "mystery",
    "never",
    "niche",
    "no",
    "of",
    "on",
    "online",
    "passage",
    "people",
    "platform",
    "platforms",
    "product",
    "real",
    "revenue",
    "rise",
    "sale",
    "sales",
    "sense",
    "ship",
    "short",
    "shorts",
    "single",
    "small",
    "social",
    "sold",
    "startup",
    "still",
    "story",
    "strange",
    "success",
    "that",
    "the",
    "their",
    "this",
    "tiktok",
    "to",
    "tragedy",
    "true",
    "turned",
    "unexplained",
    "unsolved",
    "vanished",
    "vanishing",
    "venture",
    "video",
    "videos",
    "viral",
    "went",
    "what",
    "why",
    "with",
    "worked",
    "world",
    "youtube",
}

WEIRD_BUSINESS_NICHE = "weird business / internet / creator-economy micro-doc Shorts"
FINANCE_NICHE = "manim-finance"
PSYCHOLOGY_NICHE = "manim-psychology"
PHYSICS_NICHE = "manim-physics"

ALL_MANIM_NICHES = {FINANCE_NICHE, PSYCHOLOGY_NICHE, PHYSICS_NICHE}


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

        # Browser is created lazily — only when upload_video() is actually called.
        self.browser: webdriver.Firefox | None = None

    def _create_browser(self):
        if not os.path.isdir(self._fp_profile_path):
            raise ValueError(
                f"Firefox profile path does not exist or is not a directory: {self._fp_profile_path}"
            )
        options: Options = Options()
        if get_headless():
            options.add_argument("--headless")
        options.add_argument("-profile")
        options.add_argument(self._fp_profile_path)
        service: Service = Service(GeckoDriverManager().install())
        return webdriver.Firefox(service=service, options=options)

    def _ensure_browser(self):
        if self.browser is None:
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
    def effective_niche(self) -> str:
        if getattr(self, "_niche", None) in ALL_MANIM_NICHES:
            return self._niche
        return WEIRD_BUSINESS_NICHE

    def _is_weird_business_profile(self) -> bool:
        return self.effective_niche == WEIRD_BUSINESS_NICHE

    def _is_manim_profile(self) -> bool:
        return self.effective_niche in ALL_MANIM_NICHES

    def _is_finance_profile(self) -> bool:
        return self.effective_niche == FINANCE_NICHE

    def _is_psychology_profile(self) -> bool:
        return self.effective_niche == PSYCHOLOGY_NICHE

    def _is_physics_profile(self) -> bool:
        return self.effective_niche == PHYSICS_NICHE

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

    def _niche_topics_path(self) -> str:
        """Returns the path to the per-niche topics log markdown file."""
        safe = re.sub(r"[^\w\-]", "-", self.effective_niche).lower()
        return os.path.join(ROOT_DIR, ".mp", f"topics-{safe}.md")

    def _load_niche_topics(self) -> List[str]:
        """Reads the niche topics log and returns all recorded topics."""
        path = self._niche_topics_path()
        if not os.path.exists(path):
            return []
        topics = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("- "):
                    topic = line[2:].strip()
                    if topic:
                        topics.append(topic)
        return topics

    def _record_niche_topic(self, topic: str) -> None:
        """Appends a newly chosen topic to the per-niche topics log."""
        path = self._niche_topics_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        write_header = not os.path.exists(path)
        with open(path, "a", encoding="utf-8") as f:
            if write_header:
                f.write(f"# Topics: {self.effective_niche}\n\n")
            f.write(f"- {topic}\n")

    def generate_topic(self) -> str:
        """
        Generates a topic based on the YouTube Channel niche.

        Returns:
            topic (str): The generated topic.
        """
        existing_videos = self.get_videos()
        avoid_story_references = self._get_story_references(existing_videos)

        # Merge in every topic from the persistent per-niche log,
        # prioritising them at the front so they are never truncated out.
        for logged in self._load_niche_topics():
            if logged not in avoid_story_references:
                avoid_story_references.insert(0, logged)

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
            self._record_niche_topic(completion)
            return completion

        raise RuntimeError(
            "Generated topic remained too similar to previous videos after 5 attempts."
        )

    def _build_topic_prompt(self, avoid_story_references: List[str]) -> str:
        if self._is_finance_profile():
            return self._build_finance_topic_prompt(avoid_story_references)
        if self._is_psychology_profile():
            return self._build_psychology_topic_prompt(avoid_story_references)
        if self._is_physics_profile():
            return self._build_physics_topic_prompt(avoid_story_references)

        avoid_block = ""
        if avoid_story_references:
            bullet_list = "\n".join(
                f"        - {story}" for story in avoid_story_references[:100]
            )
            avoid_block = f"""

        Do not generate a topic that repeats or is substantially similar to these previously covered stories:
{bullet_list}

        Avoid the same core event, expedition, disaster, person, place, year, vessel, case, or incident even if you reword the title.
        """

        return f"""
        Please generate a specific video idea about the following niche: {self.effective_niche}.
        The language is: {self.language}.
        Make it exactly one sentence.
        Prefer a fresh story that does not overlap with prior videos on this channel.{avoid_block}
        Choose a real and reportable business or internet story with enough verified background to explain who, what, how, and why it mattered.
        Prefer stories about weird businesses, viral products, creator moves, internet scams, platform mechanics, growth loops, pricing twists, monetization tricks, or strange consumer behavior.
        Prefer stories that are instantly interesting before explanation, not topics that only become interesting after a long setup.
        Favor a familiar app, company, creator, product, or platform colliding with one surprising business detail, contradiction, or outcome.
        Frame the idea as one familiar thing, one contradiction, one payoff.
        Prefer one story, one tension, one payoff rather than a broad listicle, theme, or bundle of incidents.
        Prefer a reported micro-doc story, not a vague trend summary or generic advice.
        Favor cases with concrete companies, products, creators, launches, campaigns, features, or records that can support a tightly reported short.
        Only return the topic, nothing else.
        """

    def _build_finance_topic_prompt(self, avoid_story_references: List[str]) -> str:
        avoid_block = ""
        if avoid_story_references:
            bullet_list = "\n".join(
                f"        - {story}" for story in avoid_story_references[:100]
            )
            avoid_block = f"""

        Do not generate a topic that repeats or is substantially similar to these previously covered topics:
{bullet_list}

        Avoid the same financial concept, product, or money mechanic even if reworded.
        """

        return f"""
        Generate a specific personal finance or money concept to explain in a 45-60 second animated YouTube Short.
        The language is: {self.language}.
        Make it exactly one sentence that names the concept or poses the money question clearly.
        Prefer a fresh topic that does not overlap with prior videos on this channel.{avoid_block}

        Choose topics from high-engagement categories where the math or mechanism surprises people:

        TIER 1 — Highest engagement (counterintuitive money math):
        - Compound interest reveals: how $5 a day becomes $1M over 40 years, why starting at 22 vs 32 doubles your retirement, the Rule of 72 for doubling money
        - Credit card traps: how the minimum payment treadmill works, why 24% APR costs you $X on a $5,000 balance, how cash-back rewards are secretly funded by interchange fees merchants pay
        - Mortgage secrets: how amortization front-loads 80% of interest in the first half of a 30-year loan, why a $300K mortgage actually costs $550K total, how one extra payment a year saves 5 years
        - Inflation math: what $100 in 1990 buys today, how 3% inflation silently erodes a $500K retirement over 20 years, why keeping cash in a savings account is a guaranteed loss
        - Investing fee traps: how a 1% fund fee costs more than $100,000 over a career, the index fund vs. active fund performance gap over 20 years

        TIER 2 — Strong engagement (money concepts most people misunderstand):
        - Tax math: how progressive tax brackets actually work (vs. the common misconception), why a Roth IRA beats a 401k for young earners, how capital gains tax is lower than income tax and why
        - Insurance math: why term life beats whole life insurance financially, how deductibles and premiums trade off, the expected-value math behind extended warranties
        - Salary negotiation math: the lifetime cost of accepting a $5,000 lower starting offer, how annual raise compounding works over a 30-year career
        - Debt avalanche vs. snowball: the math difference in total interest paid, when psychological wins beat pure math

        TIER 3 — Solid engagement (relatable everyday money moments):
        - Subscription creep: how $9.99/month services add up, the average American's annual subscription total
        - Car costs: how depreciation makes a new car lose $5,000 in the first year, the true hourly cost of car ownership
        - Housing rent vs. buy: the break-even timeline calculator, how the 5% rule determines when renting is smarter

        Prioritize Tier 1 and Tier 2 topics. Avoid vague financial advice and generic tips.
        Prefer topics where a number, graph, or calculation is the "wow" moment — something that changes how the viewer thinks about their money.
        The best topic names are surprising math claims: "Your minimum payment will take 22 years to clear a $5,000 balance", "How a 1% fee silently steals $150,000 from your retirement".
        Prefer concepts with a clear visual: a growing curve, a shrinking bar, a side-by-side comparison, a timeline, or a cascading cost breakdown.
        Keep it specific — name the exact concept or scenario, not a broad category.
        Only return the topic, nothing else.
        """

    def _build_psychology_topic_prompt(self, avoid_story_references: List[str]) -> str:
        avoid_block = ""
        if avoid_story_references:
            bullet_list = "\n".join(
                f"        - {story}" for story in avoid_story_references[:100]
            )
            avoid_block = f"""

        Do not generate a topic that repeats or is substantially similar to these previously covered topics:
{bullet_list}

        Avoid the same bias, effect, or psychological pattern even if reworded.
        """

        return f"""
        Generate a specific psychology, cognitive bias, or human behavior concept to explain in a 45-60 second animated YouTube Short.
        The language is: {self.language}.
        Make it exactly one sentence that names the concept or poses the behavioral question clearly.
        Prefer a fresh topic that does not overlap with prior videos on this channel.{avoid_block}

        Choose topics from high-engagement categories where the human brain surprises itself:

        TIER 1 — Highest engagement (counterintuitive behavior everyone recognizes in themselves):
        - Cognitive biases: the decoy effect (why you always pick the middle-priced option), loss aversion (why losing $50 hurts more than gaining $50 feels good), the sunk cost fallacy (why you finish bad movies), anchoring bias (why the first price you see dominates all decisions), the IKEA effect (why you value things you build more than things you buy)
        - Perception tricks: the Dunning-Kruger curve (why beginners feel confident and intermediates feel lost), the spotlight effect (why you think everyone noticed your mistake), choice paralysis (why more options lead to fewer sales)
        - Habit and addiction loops: variable reward schedules (why slot machines and social media are the same mechanism), the habit loop (cue → routine → reward), why removing friction changes behavior more than motivation
        - Social behavior: the bystander effect (why a crowd does nothing), conformity pressure (Asch's line experiment), why people tip more when the waiter writes their name

        TIER 2 — Strong engagement (mental shortcuts and decision traps):
        - Memory illusions: why eyewitness testimony is unreliable, how the peak-end rule means a vacation's last day dominates the whole memory, why we remember negative events more vividly
        - The psychology of pricing: why $9.99 feels much cheaper than $10, how free shipping changes purchase behavior, why larger package sizes trick us into buying more
        - Procrastination science: temporal discounting (why $100 today beats $150 in a year), implementation intentions (the one phrase that doubles follow-through), why "just start for 2 minutes" works
        - Social proof mechanics: why restaurant menus mark "most popular" items, how Amazon reviews manipulate us, the bandwagon effect

        TIER 3 — Solid engagement (famous psychology experiments and real-world effects):
        - Classic experiments: the Milgram obedience experiment, the Stanford marshmallow test and what follow-up studies found, the Robbers Cave tribal conflict experiment
        - Therapy-derived insights: why venting can make anger worse (catharsis myth), how cognitive reframing changes emotional response, the paradox of trying to suppress a thought

        Prioritize Tier 1 and Tier 2 topics. Avoid vague pop-psychology platitudes.
        Prefer topics where the viewer will say "wait, that's me" — self-recognition is the highest-shareability driver.
        The best topic names are revealing claims: "Why you'll always pick the middle price on any menu", "The brain glitch that makes you finish movies you hate".
        Prefer concepts with a clear visual: a decision tree, a before/after brain state, curves diverging, a timeline of a habit loop, a scale tipping.
        Keep it specific — name the exact bias, effect, or experiment, not a broad category.
        Only return the topic, nothing else.
        """

    def _build_physics_topic_prompt(self, avoid_story_references: List[str]) -> str:
        avoid_block = ""
        if avoid_story_references:
            bullet_list = "\n".join(
                f"        - {story}" for story in avoid_story_references[:100]
            )
            avoid_block = f"""

        Do not generate a topic that repeats or is substantially similar to these previously covered topics:
{bullet_list}

        Avoid the same physical phenomenon, device, or natural process even if reworded.
        """

        return f"""
        Generate a specific everyday physics or "how things actually work" concept to explain in a 45-60 second animated YouTube Short.
        The language is: {self.language}.
        Make it exactly one sentence that names the concept or poses the "how does this work?" question clearly.
        Prefer a fresh topic that does not overlap with prior videos on this channel.{avoid_block}

        Choose topics from high-engagement categories where the real mechanism surprises people:

        TIER 1 — Highest engagement (familiar devices with surprising mechanisms):
        - Sound and waves: how noise-canceling headphones generate an exact anti-wave, how Shazam fingerprints any song using frequency peaks, how a microphone converts air pressure to electricity, why your voice sounds different in a recording
        - Light and optics: how a camera focuses (the lens equation), why the sky is blue but sunsets are red (Rayleigh scattering), how your phone screen makes colors with three dots, how night vision amplifies photons
        - Everyday forces: why ice is slippery (pressure-melting vs. liquid layer debate), how planes generate lift (Bernoulli vs. Newtonian debate), why spinning a ball curves its flight path (Magnus effect), how a gyroscope resists falling over
        - Invisible physics: how a microwave heats food without heating the plate, why metal in a microwave sparks, how wireless charging works (inductive coupling), why your phone compass works (Hall effect)

        TIER 2 — Strong engagement (nature and body physics most people misunderstand):
        - Water and fluids: why water drains clockwise vs. counterclockwise (Coriolis myth vs. reality), how surface tension lets insects walk on water, why hot water sometimes freezes faster than cold water (Mpemba effect)
        - Heat and energy: how a refrigerator works (heat pump cycle), why blowing on soup cools it (evaporative cooling), how a thermos keeps things hot for hours, why a black car gets hotter than a white car
        - Electricity: how a battery generates voltage (electrochemical potential), why birds don't get electrocuted on power lines but you would, how a touchscreen knows where your finger is (capacitive sensing)
        - Body physics: why you see stars when you stand up too fast, how your ear converts air vibrations to hearing, why muscles can only pull (never push), how your knee joint is a four-bar linkage

        TIER 3 — Solid engagement (surprising natural phenomena):
        - Weather: how lightning chooses its path (stepped leaders), why hailstones have layers, how a rainbow forms at exactly 42 degrees, what causes thunder's rolling boom
        - Space and gravity: why satellites don't fall (they're constantly falling), how GPS triangulates your position in real-time, why the moon always shows the same face, how a black hole's event horizon works without needing equations

        Prioritize Tier 1 and Tier 2 topics. Avoid abstract physics that requires equations to appreciate.
        Prefer topics where someone uses the device or sees the phenomenon every day but has no idea how it works.
        The best topic names are "how does X actually work?" questions or surprising true claims: "Noise-canceling headphones generate sound to cancel sound", "Your microwave only heats water molecules".
        Prefer concepts with a clear visual: wave diagrams, particle arrows, cross-section cutaways, force vectors, before/after comparisons, animated cycles.
        Keep it specific — name the exact device, phenomenon, or mechanism, not a broad field.
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

    def _story_anchor_bigrams(self, text: str) -> Set[tuple]:
        """
        Returns ordered bigrams of consecutive distinctive tokens in text order.

        Used to detect shared named subjects ("pink sauce", "fyre festival") that
        a broad token-overlap score may miss when the surrounding framing vocabulary
        differs significantly between two topics.
        """
        ordered = [
            token
            for token in self._story_tokens(text)
            if token not in GENERIC_STORY_TOKENS and len(token) >= 4
        ]
        return {(ordered[i], ordered[i + 1]) for i in range(len(ordered) - 1)}

    def _find_similar_video(self, candidate_topic: str, videos: List[dict]) -> Optional[dict]:
        best_match = None
        best_score = 0.0
        candidate_bigrams = self._story_anchor_bigrams(candidate_topic)

        for video in videos:
            # Only compare against short identifier fields (topic + title).
            # Scripts and descriptions are full prose documents that inevitably
            # share vocabulary with any new on-niche topic, causing false positives.
            comparisons = [
                video.get("topic", ""),
                video.get("title", ""),
            ]

            for comparison in comparisons:
                score = self._story_similarity_score(candidate_topic, comparison)

                # If both the candidate and the comparison share at least one anchor
                # bigram (two consecutive distinctive tokens like "pink sauce" or
                # "fyre festival"), treat them as covering the same named subject
                # regardless of framing vocabulary differences.
                if candidate_bigrams and comparison:
                    shared_anchors = candidate_bigrams & self._story_anchor_bigrams(comparison)
                    if shared_anchors:
                        score = max(score, 0.80)

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

        if self._is_finance_profile():
            prompt = f"""
        Write a narration voiceover script for a {sentence_length}-sentence animated personal finance YouTube Short.

        Topic: {self.subject}
        Language: {self.language}

        DEPTH REQUIREMENT — this must be a deep, analytical explanation, not a surface summary:
        - Include the actual numbers, rates, and calculations. Do not vague-gesture at math — show it.
          Good: "At 8 percent average annual return, $10,000 doubles every 9 years — that's $80,000 by year 27 without adding a single dollar."
          Bad: "Compound interest grows your money over time."
        - Name the precise mechanism. Explain WHY the effect happens, not just that it happens.
          Good: "The key is that each year's interest earns its own interest — so the base keeps growing, and so does the gain."
          Bad: "Your money makes money."
        - Reference real benchmark data: 8% historical S&P 500 average, 24% average credit card APR, 7% average mortgage rate, 3% average inflation, 15% recommended savings rate.
        - Walk through the calculation step by step over multiple sentences so the viewer can follow the math as the animation builds.
        - Include the counterintuitive or uncomfortable truth — the thing banks, retailers, or employers don't advertise.

        VISUAL SYNC — each sentence tells the animation what to show:
        - Each sentence must describe a discrete visual beat: a bar growing, a number changing, a line diverging on a graph.
        - First sentence: A specific dollar figure or percentage shock. The animation shows the contrast or the number.
        - Middle sentences: The calculation unfolding. Each sentence = one step of the math animating on screen.
        - Final sentence: The full picture — the surprising total, the hidden cost, the net difference — shown side by side.

        Script constraints:
        - Plain spoken English. No jargon without a one-phrase gloss.
        - Short declarative sentences. One idea per sentence.
        - Do not say "welcome back", "in this video", "subscribe", or any channel filler.
        - Do not use markdown, bullet points, or speaker labels.
        - Return only the raw narration script.
        """
        elif self._is_psychology_profile():
            prompt = f"""
        Write a narration voiceover script for a {sentence_length}-sentence animated psychology and human behavior YouTube Short.

        Topic: {self.subject}
        Language: {self.language}

        DEPTH REQUIREMENT — this must be a deep, mechanistic explanation of the psychology, not a surface-level definition:
        - Name the bias or effect by its technical name and define it precisely in one sentence.
        - Explain the neurological or evolutionary mechanism — WHY the brain built this shortcut.
          Good: "Loss aversion evolved because avoiding predators mattered more than finding food — missing a threat was fatal, missing a reward was just disappointing."
          Bad: "Your brain is wired to avoid losses."
        - Include the research finding that quantifies it. Cite real data:
          Kahneman and Tversky: losses feel 2.25x more painful than equivalent gains
          Milgram obedience study: 65% continued to maximum shock level
          Dunning-Kruger: beginners rate themselves in the 62nd percentile on average
          Asch conformity: 75% conformed at least once when confederates gave wrong answers
          Cialdini's social proof: hotel towel reuse increased 26% with peer norms framing
        - Walk through the cognitive mechanism step by step — name the trigger, the automatic response, and the downstream behavior.
        - Show how the bias is deliberately exploited in real products, pricing, or UX design.
        - End with the specific catch signal — the one cue that tells you this bias is active right now.

        VISUAL SYNC — each sentence tells the animation what to show:
        - Each sentence corresponds to a discrete visual beat on screen.
        - First sentence: A visual hook that names the effect and shows the contrast.
        - Middle sentences: Step-by-step diagram of the cognitive process — scales tipping, probability bars, decision branches, before/after comparisons animating.
        - Final sentence: The practical takeaway shown as a visual state change or labeled rule.

        Script constraints:
        - Plain spoken English. No academic jargon without a plain-English gloss.
        - Short declarative sentences. One idea per sentence.
        - Do not say "welcome back", "in this video", "subscribe", or any channel filler.
        - Do not use markdown, bullet points, or speaker labels.
        - Return only the raw narration script.
        """
        elif self._is_physics_profile():
            prompt = f"""
        Write a narration voiceover script for a {sentence_length}-sentence animated everyday physics YouTube Short.

        Topic: {self.subject}
        Language: {self.language}

        DEPTH REQUIREMENT — this must explain the actual physics mechanism at the process level, not just state that it works:
        - Name the specific physical effect, wave behavior, force, or particle interaction — then explain each step of the process.
          Good: "The microphone membrane vibrates at the exact frequency of the incoming sound. That vibration moves a coil of wire through a magnetic field. Moving a conductor through a magnet generates an electrical current — that's Faraday's law. The current mirrors the pressure wave exactly."
          Bad: "Microphones convert sound to electricity."
        - Walk through the chain of cause and effect: step 1 → step 2 → step 3 → output.
        - Name the relevant physical principle by name when it fits naturally:
          Bernoulli's principle, the Doppler effect, Rayleigh scattering, Faraday's law, Newton's third law, resonance, constructive/destructive interference, capacitive sensing, inductive coupling.
        - Include one real number that makes the scale tangible:
          GPS signals travel 20,000 km and must be timed to 30 nanoseconds. Noise-canceling headphones sample sound 3,000 times per second to compute the anti-wave.
        - Address the common misconception directly — what the viewer thought and why the reality is more interesting.

        VISUAL SYNC — each sentence tells the animation what to show:
        - Each sentence corresponds to a discrete visual beat: a wave emerging, a force arrow appearing, a cross-section animating, a particle moving step by step.
        - First sentence: Show the device or phenomenon and the common misconception versus the true mechanism.
        - Middle sentences: Animate each step of the physical process in sequence — one sentence per step, one animation per sentence.
        - Final sentence: The full mechanism resolved — show the complete cycle, the elegant result, or the scale of the effect.

        Script constraints:
        - Plain spoken English. No equations as formulas — translate them into words.
        - Short declarative sentences. One idea per sentence.
        - Do not say "welcome back", "in this video", "subscribe", or any channel filler.
        - Do not use markdown, bullet points, or speaker labels.
        - Return only the raw narration script.
        """
        else:
            prompt = f"""
        Write a narration voiceover script for a {sentence_length}-sentence business and internet micro-doc YouTube Short.

        Subject: {self.subject}
        Language: {self.language}
        Niche: {self.effective_niche}

        DEPTH REQUIREMENT — the viewer must learn something real and transferable, not just hear a story:
        - Name the exact mechanism that made the business, product, or creator move work or fail.
          Good: "They priced the hardware at cost and made every dollar on replacement cartridges — a classic razor-and-blades model, except the lifetime cartridge spend averaged $1,400 per customer."
          Bad: "They had a clever business model."
        - Include the actual numbers: revenue, user counts, growth rates, prices, margins, timelines, conversion rates, or valuations.
          Good: "The waitlist hit 100,000 people before the product shipped. They charged $300 upfront. That's $30 million in committed demand with no inventory risk."
          Bad: "They had a huge waitlist."
        - Explain WHY the mechanism worked on a psychological or economic level — not just what happened.
          Good: "FOMO made the waitlist itself feel like social proof. Paying to join signaled quality. By launch day, customers had already convinced themselves it was worth it."
          Bad: "People were excited about it."
        - Name the transferable pattern — the underlying principle that shows up in other businesses, platforms, or creator strategies.
          Examples: artificial scarcity, community moat, distribution arbitrage, price anchoring, network effects on one side only, manufactured urgency, loss-leader acquisition, parasocial trust conversion.
        - Address what failed, what the critics got wrong, or what the founder didn't see coming.
        - Clearly distinguish confirmed facts from reported estimates or public speculation.

        BEAT STRUCTURE — follow this shape closely:
        1. Hook: The most counterintuitive number, claim, or outcome. Make it feel impossible.
        2. Context: Who, what, when — just enough to orient the viewer in one sentence.
        3. Mechanism: The exact business model, growth loop, platform trick, or pricing structure — explained step by step.
        4. Why it worked: The psychological or economic reason people responded. Name the principle.
        5. Escalation or consequence: What happened at scale — the traction, the backlash, the copy-cats, the collapse.
        6. The real insight: What this story reveals about how money, attention, or platforms actually work.
        7. Closing line: A judgment question or call to action — short, spoken, non-cringe. E.g. "Was this genius or just luck?" or "Follow for more."

        If sentence count is under 6, compress beats 3-5 without losing the mechanism or the real insight.
        If sentence count is over 6, add concrete escalation detail — more numbers, a second twist, or a named consequence.

        Script constraints:
        - Short declarative sentences. One idea per sentence. Easy to caption on screen.
        - Plain spoken English. No jargon without a one-phrase gloss immediately after.
        - Do not say "welcome back", "in this video", "did you know", or any channel filler.
        - Do not use markdown, bullet points, titles, speaker labels, or quotation marks around the full response.
        - Do not invent facts. If a number is an estimate, say "roughly" or "reportedly."
        - Return only the raw script.

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

        if self._is_finance_profile():
            title_prompt = f"""
                Generate a YouTube Shorts title for the following personal finance concept: {self.subject}.
                Lead with a specific number, dollar amount, or surprising financial claim that makes the stat feel personal.
                Make it sound like a financial truth most people don't know but affects them directly.
                Keep it under 70 characters when possible. Prefer 5-10 words.
                Avoid generic advice framing. No "how to save money" style — lead with the shocking math.
                Do not use hashtags.
                Only return the title, nothing else.
                Limit the title under 100 characters.
                """
            description_prompt_template = f"""
                Generate a YouTube Shorts description for the following personal finance script: {{script}}.
                Open with the key dollar figure or financial fact from the script that will grab attention.
                Follow with 1-2 sentences that make the concept feel personally relevant to the viewer.
                End with a question that invites comments, such as asking what the viewer would do differently.
                Only return the description, nothing else.
                Limit the description under {{max_len}} characters.
                """
        elif self._is_psychology_profile():
            title_prompt = f"""
                Generate a YouTube Shorts title for the following psychology and human behavior concept: {self.subject}.
                Name the specific bias, effect, or mental pattern and lead with what it makes people do against their own interest.
                Make it feel like a personal revelation — "you" do this.
                Keep it under 70 characters when possible. Prefer 5-10 words.
                Avoid vague self-help framing. Lead with the specific mechanism, not generic "your brain" language.
                Do not use hashtags.
                Only return the title, nothing else.
                Limit the title under 100 characters.
                """
            description_prompt_template = f"""
                Generate a YouTube Shorts description for the following psychology script: {{script}}.
                Open with the name of the bias or effect and a one-sentence claim about what it makes people do.
                Follow with 1-2 sentences that ground the concept in a real everyday situation the viewer will recognize.
                End with a question that invites self-reflection or a debate about whether the viewer has experienced this.
                Only return the description, nothing else.
                Limit the description under {{max_len}} characters.
                """
        elif self._is_physics_profile():
            title_prompt = f"""
                Generate a YouTube Shorts title for the following everyday physics concept: {self.subject}.
                Lead with the surprising true mechanism of the device or phenomenon — the counterintuitive truth most people don't know.
                Make it sound like a revelation about something the viewer uses or sees every day.
                Keep it under 70 characters when possible. Prefer 5-10 words.
                Avoid textbook phrasing. Lead with "why", "how", or a surprising true claim.
                Do not use hashtags.
                Only return the title, nothing else.
                Limit the title under 100 characters.
                """
            description_prompt_template = f"""
                Generate a YouTube Shorts description for the following everyday physics script: {{script}}.
                Open with the surprising real mechanism this video explains, in one vivid sentence.
                Follow with 1-2 sentences that make the viewer appreciate the invisible physics in their daily life.
                End with a question that invites comments, such as what other device the viewer wants explained.
                Only return the description, nothing else.
                Limit the description under {{max_len}} characters.
                """
        else:
            title_prompt = f"""
                Generate a YouTube Shorts title for the following real business or internet story: {self.subject}.
                Create a clean curiosity gap built around a surprising business model, creator move, viral product, platform mechanic, scam, or monetization twist.
                Lead with the contradiction, not the category label.
                Make it sound like a surprising true claim about a real company, product, creator, app, or internet behavior.
                Keep it specific, emotionally charged, and narrow: one story, one tension, one payoff.
                prefer 5 to 10 words when possible.
                Avoid generic educational phrasing, vague teaser language, listicle framing, or documentary-label titles.
                Do not use hashtags in the title.
                Only return the title, nothing else.
                Limit the title under 100 characters.
                """
            description_prompt_template = f"""
                Generate a YouTube Shorts description for the following script: {{script}}.
                Start with a high-contrast opening line that feels cinematic and immediate.
                Keep the description focused on one story, one tension, one payoff.
                Make the viewer understand why it matters without spoiling the entire curiosity gap.
                If appropriate, hint at the business lesson, creator takeaway, or modern implication.
                Do not repeat the title verbatim or open with a flat summary sentence.
                end with a short judgment question that can spark comments.
                Only return the description, nothing else.
                Limit the description under {{max_len}} characters.
                """

        title = ""
        for _ in range(max_attempts):
            title = self.generate_response(title_prompt)

            if len(title) <= 100:
                break

            if get_verbose():
                warning("Generated Title is too long. Retrying...")
        else:
            raise RuntimeError("Generated title remained too long after 3 attempts.")

        max_description_length = 5000
        description = ""
        for _ in range(max_attempts):
            description = self.generate_response(
                description_prompt_template.format(
                    script=self.script,
                    max_len=max_description_length,
                )
            )

            if len(description) <= max_description_length:
                break

            if get_verbose():
                warning("Generated Description is too long. Retrying...")
        else:
            raise RuntimeError(
                "Generated description remained too long after 3 attempts."
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
        if self._is_weird_business_profile():
            business_suffix = (
                " Realistic business/editorial visual, modern app screens, dashboards, "
                "storefronts, product packaging, creator setups, checkout flows, "
                "analytics charts, social posts, or office scenes, grounded lighting, "
                "clean composition, legible interface detail, not surreal AI art."
            )

            if "realistic business/editorial visual" not in lowered:
                cleaned_prompt = f"{cleaned_prompt}.{business_suffix}"

            return cleaned_prompt

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

        Use vivid visual detail, but keep every prompt realistic and grounded.
        Favor app screens, dashboards, storefronts, ecommerce listings,
        creator setups, product packaging, checkout flows, analytics charts,
        office scenes, screenshots, interfaces, headlines, and realistic business photography.
        Make each prompt feel like a polished editorial or commercial visual,
        not a wilderness documentary, not a historical reenactment, and not stylized AI art.
        Use clean camera language, modern interface detail, grounded lighting,
        legible layouts, and commercially plausible composition.

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

        speed = get_tts_speed()
        # Build the audio filter chain: optional speed change + 0.75s silence tail so
        # the video never hard-cuts mid-word and ends with a natural breath pause.
        filters = []
        if speed != 1.0:
            filters.append(f"atempo={speed}")
        filters.append("apad=pad_dur=0.75")

        processed_path = path.replace(".wav", "_processed.wav")
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", path,
                "-filter:a", ",".join(filters),
                processed_path,
            ],
            check=True,
            capture_output=True,
        )
        os.replace(processed_path, path)

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

    def record_crosspost_result(self, video: dict, crosspost_result: dict) -> None:
        """
        Persists successful Post Bridge platform status onto a cached video.

        Args:
            video (dict): Cached video identity fields.
            crosspost_result (dict): Detailed Post Bridge result payload.

        Returns:
            None
        """
        platform_statuses = dict(crosspost_result.get("platforms") or {})
        if not platform_statuses:
            return

        merged_crossposts = {}
        existing_video = self._find_cached_video_record(video)
        if isinstance(existing_video, dict):
            merged_crossposts.update(dict(existing_video.get("crossposts") or {}))

        merged_crossposts.update(dict(video.get("crossposts") or {}))
        merged_crossposts.update(platform_statuses)

        self.add_video(
            {
                "path": video.get("path"),
                "url": video.get("url"),
                "crossposts": merged_crossposts,
            }
        )

    def _find_cached_video_record(self, video: dict) -> Optional[dict]:
        cache = get_youtube_cache_path()

        with open(cache, "r") as file:
            payload = json.loads(file.read())

        for account in payload.get("accounts", []):
            if account.get("id") != self._account_uuid:
                continue

            for existing_video in account.get("videos", []):
                if video.get("path") and existing_video.get("path") == video.get("path"):
                    return existing_video
                if video.get("url") and existing_video.get("url") == video.get("url"):
                    return existing_video

        return None

    def record_post_bridge_publish_result(self, publish_result: dict) -> None:
        """
        Persist a Post Bridge publish outcome onto the cached video record.

        YouTube is treated as the primary upload target and is reflected via the
        cached video's uploaded flag. Non-YouTube targets remain in crossposts.

        Args:
            publish_result (dict): Detailed Post Bridge result payload.

        Returns:
            None
        """
        platform_statuses = dict(publish_result.get("platforms") or {})
        youtube_status = dict(platform_statuses.get("youtube") or {})
        uploaded_to_youtube = youtube_status.get("status") == "success"

        video_update = {
            "topic": getattr(self, "subject", ""),
            "script": getattr(self, "script", ""),
            "title": str(getattr(self, "metadata", {}).get("title", "") or ""),
            "description": str(
                getattr(self, "metadata", {}).get("description", "") or ""
            ),
            "path": getattr(self, "video_path", None),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if uploaded_to_youtube:
            video_update["uploaded"] = True

        self.add_video(video_update)

        non_youtube_platforms = {
            platform: details
            for platform, details in platform_statuses.items()
            if str(platform).strip().lower() != "youtube"
        }

        if non_youtube_platforms:
            self.record_crosspost_result(
                {
                    "path": getattr(self, "video_path", None),
                    "url": getattr(self, "uploaded_video_url", None),
                },
                {
                    "platforms": non_youtube_platforms,
                },
            )

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

        # Build subtitle clips: phrase-level text with a semi-transparent dark background.
        # Research-backed defaults: 3-6 words per card, white text, dark pill, lower-center
        # position at ~72% of frame height. bg is composed behind each text card via
        # ColorClip.set_opacity() rather than a solid bg_color on the TextClip itself.
        _font_path = os.path.join(get_fonts_dir(), get_font())

        def generator(txt):
            text_clip = TextClip(
                txt,
                font=_font_path,
                fontsize=88,
                color="white",
                stroke_color="black",
                stroke_width=3,
                size=(920, None),
                method="caption",
            )
            w, h = text_clip.size
            pad = 18
            bg = ColorClip(
                size=(w + pad * 2, h + pad * 2),
                color=(0, 0, 0),
            ).set_opacity(0.60)
            return CompositeVideoClip(
                [bg, text_clip.set_pos("center")],
                size=(w + pad * 2, h + pad * 2),
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
            equalize_subtitles(subtitles_path, get_subtitle_max_chars())
            subtitles = SubtitlesClip(subtitles_path, generator)
            # Position centered horizontally, lower-center vertically (~72% down 1920px frame).
            # set_pos returns a new clip in MoviePy 1.x — assign the result.
            subtitles = subtitles.set_pos(("center", 1380))
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

    # ------------------------------------------------------------------
    # Manim how-to channel methods
    # ------------------------------------------------------------------

    def _inject_portrait_safeguards(self, source: str) -> str:
        """
        Post-processes generated Manim code to enforce portrait safe-zone width clamping.
        Inserts a ``if mob.width > 3.0: mob.scale_to_fit_width(3.0)`` guard after every
        Text() or VGroup() assignment so that oversized text cannot overflow the screen
        regardless of what font_size the LLM chose.
        """
        text_assign_re = re.compile(r'^(\s+)(\w+)\s*=\s*(?:Text|VGroup)\s*\(')
        lines = source.split('\n')
        result = []
        i = 0
        while i < len(lines):
            line = lines[i]
            m = text_assign_re.match(line)
            if m:
                indent = m.group(1)
                varname = m.group(2)
                # Collect lines until parentheses are balanced (handles multi-line calls)
                block = [line]
                depth = line.count('(') - line.count(')')
                j = i + 1
                while depth > 0 and j < len(lines):
                    block.append(lines[j])
                    depth += lines[j].count('(') - lines[j].count(')')
                    j += 1
                # Check if next non-empty line already scales this var
                next_line = lines[j] if j < len(lines) else ''
                already_scaled = (
                    f'{varname}.scale_to_fit_width' in next_line
                    or f'{varname}.scale(' in next_line
                )
                result.extend(block)
                if not already_scaled:
                    result.append(f'{indent}if {varname}.width > 3.0: {varname}.scale_to_fit_width(3.0)')
                i = j
            else:
                result.append(line)
                i += 1
        return '\n'.join(result)

    def _inject_manim_text_fallbacks(self, source: str) -> str:
        """
        Injects plain-text fallback helpers so generated scenes do not depend on
        a system LaTeX installation when the model emits MathTex or Tex.

        Args:
            source (str): Raw generated scene source.

        Returns:
            str: Scene source with fallback helpers inserted when needed.
        """
        if "MathTex(" not in source and not re.search(r"(?<!\w)Tex\(", source):
            return source

        if "def MathTex(*parts, **kwargs):" in source:
            return source

        fallback_helpers = """
def _safe_plain_text(*parts, **kwargs):
    safe_kwargs = {}
    for key in ("font_size", "color", "slant", "weight", "gradient", "t2c", "t2f", "t2g", "t2s", "line_spacing"):
        if key in kwargs:
            safe_kwargs[key] = kwargs[key]

    joined_parts = " ".join(str(part) for part in parts)
    joined_parts = joined_parts.replace("\\\\text", "")
    joined_parts = joined_parts.replace("\\\\rightarrow", "->")
    joined_parts = joined_parts.replace("\\\\to", "->")
    joined_parts = joined_parts.replace("\\\\cdot", "*")
    joined_parts = joined_parts.replace("\\\\times", "x")
    joined_parts = joined_parts.replace("{", "")
    joined_parts = joined_parts.replace("}", "")
    joined_parts = joined_parts.replace("\\\\", "")
    return Text(joined_parts, **safe_kwargs)


def MathTex(*parts, **kwargs):
    return _safe_plain_text(*parts, **kwargs)


def Tex(*parts, **kwargs):
    return _safe_plain_text(*parts, **kwargs)
""".strip()

        class_match = re.search(r"^class\s+ExplainerScene\b", source, flags=re.MULTILINE)
        if class_match is None:
            return f"{fallback_helpers}\n\n{source}"

        before_class = source[:class_match.start()].rstrip()
        from_class_onward = source[class_match.start():].lstrip()
        return f"{before_class}\n\n{fallback_helpers}\n\n{from_class_onward}"

    def generate_manim_code(self) -> str:
        """
        Prompts the LLM to generate a complete Manim Python scene file for the
        current subject and script.

        Returns:
            scene_path (str): Path to the written .py scene file.
        """
        # Build a numbered beat list so the LLM can sync visuals to narration
        raw_sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", self.script.strip()) if s.strip()]
        narration_beats = "\n".join(
            f"        Beat {i + 1}: {s}"
            for i, s in enumerate(raw_sentences)
        )

        prompt = f"""
        Generate a complete, self-contained Manim Python animation scene for a YouTube Short (9:16 portrait, 1080x1920).

        Topic: {self.subject}
        Narration (voiceover read aloud alongside the animation): {self.script}

        ═══════════════════════════════════════
        MANDATORY: VERTICAL 9:16 PORTRAIT LAYOUT
        ═══════════════════════════════════════
        Start the file with EXACTLY these four config lines before any other code:
          from manim import *
          config.pixel_width = 1080
          config.pixel_height = 1920
          config.frame_width = 4.5
          config.frame_height = 8

        COORDINATE SYSTEM — memorize these hard limits:
          frame_width = 4.5  →  left edge = x -2.25,  right edge = x +2.25
          frame_height = 8   →  bottom edge = y -4.0,  top edge = y +4.0

        SAFE ZONE — every Mobject's bounding box MUST fit inside:
          x: -1.8  to  +1.8
          y: -1.4  to  +3.5  ← HARD LIMIT: bottom 40% is the subtitle overlay — never go below -1.4

        SUBTITLE ZONE WARNING:
          A subtitle text band is burned into the video at the bottom of the screen
          (approximately pixel y=1380–1600, which is Manim y=-1.75 to -2.5).
          Any Manim content placed below y=-1.4 will be HIDDEN under the subtitles.
          Keep every visual completely above y=-1.4. There is NO footer zone.

        FORBIDDEN — these positions will clip or be hidden:
          ✗  LEFT * N  or  RIGHT * N  where N > 1.6  (full screen is only 2.25 wide)
          ✗  UP * N   or  DOWN * N   where N > 3.3
          ✗  DOWN * N  where N > 1.2  (subtitle zone below y=-1.4 — content will be covered)
          ✗  .to_edge(LEFT), .to_edge(RIGHT)  — use explicit .move_to() with safe coords instead
          ✗  Any VGroup or bar chart that spans more than 3.2 units wide
          ✗  Two side-by-side columns unless each is ≤ 1.4 units wide with a ≤ 0.3 gap
          ✗  Any Text placed below y=-1.4
          ✗  Any Text that has not had .scale_to_fit_width(min(t.width, 3.0)) applied

        TEXT SIZING AND MANDATORY WIDTH CLAMPING:
          After EVERY Text() you create, immediately call .scale_to_fit_width(3.0) on it.
          This is not optional — every single Text() must be clamped:

            hook = Text("YOUR TEXT\\nHERE", font_size=32)
            hook.scale_to_fit_width(3.0)        # ← REQUIRED for every Text
            hook.move_to(np.array([0, 2.8, 0]))

          Font size guidelines (portrait — these are upper limits, go smaller if wrapping):
            Title / hook line:      font_size = 28–36,  wrap after 14 characters using "\\n"
            Body explanation text:  font_size = 22–28,  wrap after 20 characters using "\\n"
            Diagram labels:         font_size = 16–22
            Any VGroup: call .scale_to_fit_width(3.0) on the whole VGroup after assembling it

        LAYOUT ZONES — use these y positions (subtitle zone occupies below y=-1.4):
          Top label:       y ≈ +3.0   (short title, question, or hook text)
          Upper visual:    y ≈ +1.5   (primary chart, diagram, or key value)
          Center:          y ≈  0.0   (animation transforms)
          Lower visual:    y ≈ -0.8   (secondary comparison or step)
          Footer takeaway: y ≈ -1.2   (minimum allowable — do NOT go lower)

        POSITIONING — always use explicit coordinates:
          .move_to(np.array([x, y, 0]))   ← preferred
          .shift(UP * 1.2)                ← acceptable if small N
          NEVER trust default centering for portrait — everything drifts off-screen

        ════════════════════════════════════════
        MANDATORY: SYNC EVERY VISUAL TO THE NARRATION
        ════════════════════════════════════════
        The animation must show exactly what each narration sentence describes.
        One beat = one sentence = one distinct visual animation step.
        Do NOT animate generic transitions — each beat must illustrate the specific
        claim made in that sentence.

        Narration beats:
{narration_beats}

        Beat → visual mapping rules:
        - Beat 1 (hook): Bold text or dramatic visual contrast that mirrors the hook claim
        - Middle beats: Animate the EXACT mechanism described — grow bars as the number grows,
          move an arrow when direction is mentioned, split a bar when a fee is deducted,
          show the calculation building in real-time as the sentence says it
        - Final beat: Show the "aha" payoff — final state, conclusion, or surprising comparison

        ═══════════════════════════
        GENERAL SCENE REQUIREMENTS
        ═══════════════════════════
        - Define exactly one scene class named `ExplainerScene` that inherits from `Scene`.
        - Total animation runtime: 45–60 seconds. Use self.wait() calls to match narration pacing.
        - Color palette: dark background (default), WHITE for text, YELLOW for highlights,
          GREEN for positive/gain, RED for negative/loss/cost, BLUE for neutral data.
        - Use Text() only. Do NOT use MathTex, Tex, or LaTeX. Write math as plain strings.
        - Animations to use: Write, FadeIn, FadeOut, Create, Transform, GrowFromCenter,
          DrawBorderThenFill, MoveToTarget, ReplacementTransform, LaggedStart.
        - Do NOT use: ThreeDScene, OpenGLRenderer, external images, SVG files, audio code,
          always_redraw, ValueTracker-based updaters (keep it simple and reliable).

        Return ONLY raw Python code. No markdown fences, no explanation text outside the code.
        """

        completion = self.generate_response(prompt)

        # Strip markdown code fences if the LLM wrapped the output
        completion = re.sub(r"^```python\s*\n?", "", completion.strip(), flags=re.IGNORECASE)
        completion = re.sub(r"^```\s*\n?", "", completion.strip())
        completion = re.sub(r"\n?```\s*$", "", completion.strip())
        completion = self._inject_manim_text_fallbacks(completion)
        completion = self._inject_portrait_safeguards(completion)

        if "ExplainerScene" not in completion:
            raise RuntimeError("Generated Manim code does not contain ExplainerScene class.")

        scene_path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + "_scene.py")
        with open(scene_path, "w", encoding="utf-8") as f:
            f.write(completion)

        if get_verbose():
            info(f' => Wrote Manim scene to "{scene_path}"')

        return scene_path

    def render_manim(self, scene_path: str) -> str:
        """
        Renders a Manim scene file to an MP4 via the manim CLI.

        Args:
            scene_path (str): Path to the .py scene file.

        Returns:
            video_path (str): Path to the rendered MP4 file.
        """
        import glob

        media_dir = os.path.join(ROOT_DIR, ".mp", "manim_media")
        os.makedirs(media_dir, exist_ok=True)

        scene_stem = os.path.splitext(os.path.basename(scene_path))[0]

        _manim_bin = os.path.join(os.path.dirname(sys.executable), "manim")
        cmd = [
            _manim_bin, "render",
            scene_path,
            "ExplainerScene",
            "-ql",
            "--media_dir", media_dir,
        ]

        if get_verbose():
            info(f" => Running manim: {' '.join(cmd)}")

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT_DIR)

        if result.returncode != 0:
            error_output = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(f"Manim render failed:\n{error_output}")

        # Locate the rendered MP4 (quality suffix varies, e.g. 480p15)
        pattern = os.path.join(media_dir, "videos", scene_stem, "*", "ExplainerScene.mp4")
        matches = sorted(glob.glob(pattern))

        if not matches:
            raise RuntimeError(
                f"Manim render completed but no MP4 found matching: {pattern}"
            )

        rendered_path = matches[-1]
        output_path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + "_manim.mp4")
        os.rename(rendered_path, output_path)

        if get_verbose():
            info(f' => Rendered Manim video to "{output_path}"')

        return output_path

    def combine_manim(self, manim_video_path: str) -> str:
        """
        Combines a Manim-rendered video with TTS audio, background music, and subtitles.

        Args:
            manim_video_path (str): Path to the Manim MP4.

        Returns:
            path (str): Path to the final combined MP4.
        """
        combined_path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + ".mp4")
        threads = get_threads()

        tts_clip = AudioFileClip(self.tts_path)
        max_duration = tts_clip.duration

        manim_clip = VideoFileClip(manim_video_path)

        # Loop Manim video if it is shorter than TTS; trim if longer
        if manim_clip.duration < max_duration:
            loops_needed = int(max_duration / manim_clip.duration) + 1
            manim_clip = concatenate_videoclips([manim_clip.copy() for _ in range(loops_needed)])
        manim_clip = manim_clip.subclip(0, max_duration).set_fps(30)

        # Ensure portrait 1080×1920
        if (manim_clip.w, manim_clip.h) != (1080, 1920):
            manim_clip = manim_clip.resize((1080, 1920))

        _font_path_manim = os.path.join(get_fonts_dir(), get_font())

        def generator(txt):
            text_clip = TextClip(
                txt,
                font=_font_path_manim,
                fontsize=88,
                color="white",
                stroke_color="black",
                stroke_width=3,
                size=(920, None),
                method="caption",
            )
            w, h = text_clip.size
            pad = 18
            bg = ColorClip(
                size=(w + pad * 2, h + pad * 2),
                color=(0, 0, 0),
            ).set_opacity(0.60)
            return CompositeVideoClip(
                [bg, text_clip.set_pos("center")],
                size=(w + pad * 2, h + pad * 2),
            )

        subtitles = None
        try:
            subtitles_path = self.generate_subtitles(self.tts_path)
            equalize_subtitles(subtitles_path, get_subtitle_max_chars())
            subtitles = SubtitlesClip(subtitles_path, generator)
            subtitles = subtitles.set_pos(("center", 1380))
        except Exception as e:
            raise RuntimeError(f"Failed to generate subtitles: {e}") from e

        random_song = choose_random_manim_song()
        random_song_clip = AudioFileClip(random_song).set_fps(44100)
        random_song_clip = random_song_clip.fx(afx.volumex, 0.1)
        comp_audio = CompositeAudioClip([tts_clip.set_fps(44100), random_song_clip])

        final_clip = manim_clip.set_audio(comp_audio)
        final_clip = final_clip.set_duration(max_duration)

        if subtitles is not None:
            final_clip = CompositeVideoClip([final_clip, subtitles])

        final_clip.write_videofile(combined_path, threads=threads, audio_codec="aac")

        success(f'Wrote Manim Video to "{combined_path}"')

        return combined_path

    # ------------------------------------------------------------------

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

        if self._is_manim_profile():
            # Generate Manim animation code and render it
            scene_path = self.generate_manim_code()
            manim_video_path = self.render_manim(scene_path)

            # Generate the TTS
            self.generate_script_to_speech(tts_instance)

            # Combine Manim video with TTS + music + subtitles
            path = self.combine_manim(manim_video_path)
        else:
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

    def load_cached_video(self, video: dict) -> None:
        """
        Loads a cached video record onto the current YouTube instance so the
        existing upload flow can retry the Short without regenerating assets.

        Args:
            video (dict): Cached video record for this account.

        Returns:
            None
        """
        self.video_path = os.path.abspath(video["path"])
        self.metadata = {
            "title": video.get("title", ""),
            "description": self._resolve_cached_description(video),
        }
        self.subject = video.get("topic", "")
        self.script = video.get("script", "")

    def _resolve_cached_description(self, video: dict) -> str:
        """
        Returns the best available description for a cached Short.

        Older cache entries may not include a dedicated description field.
        Reuse the script or topic before falling back to an empty description.

        Args:
            video (dict): Cached video record.

        Returns:
            description (str): Best available description text.
        """
        for field_name in ("description", "script", "topic", "title"):
            value = str(video.get(field_name, "") or "").strip()
            if value:
                return value

        return ""

    def _extract_video_id_from_studio_url(self, href: Optional[str]) -> Optional[str]:
        """
        Extract a YouTube video ID from a Studio or watch URL.

        Args:
            href (str | None): URL collected from YouTube Studio.

        Returns:
            video_id (str | None): Parsed video ID when available.
        """
        if not href:
            return None

        parsed_url = urlparse(href)
        query_params = parse_qs(parsed_url.query)
        if query_params.get("v"):
            return query_params["v"][0]

        path_segments = [segment for segment in parsed_url.path.split("/") if segment]
        if "video" in path_segments:
            video_index = path_segments.index("video")
            if video_index + 1 < len(path_segments):
                return path_segments[video_index + 1]

        if path_segments:
            return path_segments[-1]

        return None

    def _fetch_uploaded_short_url(
        self,
        max_attempts: int = 5,
        delay_seconds: float = 2.0,
    ) -> Optional[str]:
        """
        Poll YouTube Studio for the uploaded Short URL.

        Returns:
            url (str | None): Public watch URL when available.
        """
        driver = self.browser
        studio_shorts_url = (
            f"https://studio.youtube.com/channel/{self.channel_id}/videos/short"
        )

        for attempt in range(max_attempts):
            driver.get(studio_shorts_url)
            videos = driver.find_elements(By.TAG_NAME, "ytcp-video-row")

            if videos:
                anchor_tag = videos[0].find_element(By.TAG_NAME, "a")
                href = anchor_tag.get_attribute("href")

                if get_verbose():
                    info(f"\t=> Extracting video ID from URL: {href}")

                video_id = self._extract_video_id_from_studio_url(href)
                if video_id:
                    return build_url(video_id)

            if attempt < max_attempts - 1:
                time.sleep(delay_seconds)

        return None

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

    def _click_upload_option_and_verify(
        self,
        option_element,
        description: str,
        focus_delay_seconds: float = 0.5,
    ) -> None:
        self.browser.execute_script(
            """
            const element = arguments[0];
            element.scrollIntoView({block: "center", inline: "nearest"});
            if (typeof element.focus === "function") {
                element.focus();
            }
            """,
            option_element,
        )
        option_element.click()
        time.sleep(focus_delay_seconds)

        is_selected = self.browser.execute_script(
            """
            const element = arguments[0];
            const roleAncestor = element.closest('[role="radio"]');
            const parentElement = element.parentElement;
            return Boolean(element.checked)
                || element.getAttribute('aria-checked') === 'true'
                || element.getAttribute('checked') !== null
                || (roleAncestor && roleAncestor.getAttribute('aria-checked') === 'true')
                || (parentElement && parentElement.getAttribute('aria-checked') === 'true');
            """,
            option_element,
        )

        if not is_selected:
            raise RuntimeError(f"Failed to select YouTube {description}.")

    def _set_upload_audience_selection(self) -> None:
        audience_name = (
            YOUTUBE_MADE_FOR_KIDS_NAME
            if get_is_for_kids()
            else YOUTUBE_NOT_MADE_FOR_KIDS_NAME
        )
        audience_description = (
            "made for kids audience"
            if get_is_for_kids()
            else "not made for kids audience"
        )
        audience_option = self.browser.find_element(By.NAME, audience_name)
        self._click_upload_option_and_verify(
            audience_option,
            audience_description,
        )

    def _set_upload_visibility_public(self) -> None:
        radio_buttons = self.browser.find_elements(By.XPATH, YOUTUBE_RADIO_BUTTON_XPATH)
        if not radio_buttons:
            raise RuntimeError("Could not find YouTube visibility options.")

        public_radio_button = radio_buttons[0]
        self._click_upload_option_and_verify(
            public_radio_button,
            "public visibility",
        )

    def upload_video(self) -> bool:
        """
        Uploads the video to YouTube.

        Returns:
            success (bool): Whether the upload was successful or not.
        """
        current_step = "initialize channel context"
        file_attached = False
        title_value = ""
        description_value = ""
        self.last_upload_retry_allowed = True
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
            file_attached = True

            # Wait for upload to finish
            time.sleep(5)

            # Set title
            current_step = "load YouTube metadata textboxes"
            title_el, description_el = self._get_upload_metadata_textboxes()
            title_value = str(self.metadata.get("title", "") or "").strip()
            if not title_value:
                title_value = os.path.splitext(os.path.basename(self.video_path))[0]
            description_value = str(self.metadata.get("description", "") or "").strip()

            if verbose:
                info("\t=> Setting title...")

            current_step = "set video title"
            self._set_upload_metadata_text(
                title_el,
                title_value,
                focus_delay_seconds=1,
            )

            if verbose:
                info("\t=> Setting description...")

            # Set description
            current_step = "set video description"
            time.sleep(10)
            self._set_upload_metadata_text(
                description_el,
                description_value,
                focus_delay_seconds=0.5,
            )

            time.sleep(0.5)

            # Set `made for kids` option
            if verbose:
                info("\t=> Setting `made for kids` option...")

            current_step = "set audience selection"
            self._set_upload_audience_selection()

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

            # Set as public
            if verbose:
                info("\t=> Setting as public...")

            current_step = "set visibility to public"
            self._set_upload_visibility_public()

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
            url = self._fetch_uploaded_short_url()
            self.uploaded_video_url = url

            if url and verbose:
                success(f" => Uploaded Video: {url}")

            if not url:
                warning(
                    "YouTube upload finished, but Studio did not return a Short URL yet. Continuing without a saved URL."
                )

            # Add video to cache
            video_record = {
                "topic": self.subject,
                "script": self.script,
                "title": title_value,
                "description": description_value,
                "path": self.video_path,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "uploaded": True,
            }
            if url:
                video_record["url"] = url

            self.add_video(video_record)

            # Close the browser
            driver.quit()
            self.browser = None
            self.last_upload_retry_allowed = False

            return True
        except Exception as e:
            self.last_upload_retry_allowed = not file_attached
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
