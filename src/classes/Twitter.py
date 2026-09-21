import re
import sys
import time
import os
import json

from cache import *
from config import *
from status import *
from llm_provider import generate_text
from typing import List, Optional
from datetime import datetime
from termcolor import colored
from selenium_firefox import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Twitter:
    """
    Class for the Bot, that grows a Twitter account.
    """

    def __init__(
        self,
        account_uuid: str,
        account_nickname: str,
        fp_profile_path: str,
        topic: str,
        character_context: str = "",
    ) -> None:
        """
        Initializes the Twitter Bot.

        Args:
            account_uuid (str): The account UUID
            account_nickname (str): The account nickname
            fp_profile_path (str): The path to the Firefox profile

        Returns:
            None
        """
        self.account_uuid: str = account_uuid
        self.account_nickname: str = account_nickname
        self.fp_profile_path: str = fp_profile_path
        self.topic: str = topic
        self.character_context: str = character_context.strip()

        # Initialize the Firefox profile
        self.options: Options = Options()

        # Set headless state of browser
        if get_headless():
            self.options.add_argument("--headless")

        if not os.path.isdir(fp_profile_path):
            raise ValueError(
                f"Firefox profile path does not exist or is not a directory: {fp_profile_path}"
            )

        # Set the profile path
        self.options.add_argument("-profile")
        self.options.add_argument(fp_profile_path)

        # Set the service
        self.service: Service = Service(GeckoDriverManager().install())

        # Initialize the browser
        self.browser: webdriver.Firefox = webdriver.Firefox(
            service=self.service, options=self.options
        )
        self.wait: WebDriverWait = WebDriverWait(self.browser, 30)

    def post(self, text: Optional[str] = None) -> None:
        """
        Starts the Twitter Bot.

        Args:
            text (str): The text to post

        Returns:
            None
        """
        bot: webdriver.Firefox = self.browser
        verbose: bool = get_verbose()

        bot.get("https://x.com/compose/post")

        post_content: str = text if text is not None else self.generate_post()
        now: datetime = datetime.now()

        print(colored(" => Posting to Twitter:", "blue"), post_content[:30] + "...")
        body = post_content

        text_box = None
        text_box_selectors = [
            (By.CSS_SELECTOR, "div[data-testid='tweetTextarea_0'][role='textbox']"),
            (By.XPATH, "//div[@data-testid='tweetTextarea_0']//div[@role='textbox']"),
            (By.XPATH, "//div[@role='textbox']"),
        ]

        for selector in text_box_selectors:
            try:
                text_box = self.wait.until(EC.element_to_be_clickable(selector))
                text_box.click()
                text_box.send_keys(body)
                break
            except Exception:
                continue

        if text_box is None:
            raise RuntimeError(
                "Could not find tweet text box. Ensure you are logged into X in this Firefox profile."
            )


        post_button = None
        post_button_selectors = [
            (By.XPATH, "//button[@data-testid='tweetButtonInline']"),
            (By.XPATH, "//button[@data-testid='tweetButton']"),
            (By.XPATH, "//span[text()='Post']/ancestor::button"),
        ]

        for selector in post_button_selectors:
            try:
                post_button = self.wait.until(EC.element_to_be_clickable(selector))
                post_button.click()
                break
            except Exception:
                continue

        if post_button is None:
            raise RuntimeError("Could not find the Post button on X compose screen.")

        if verbose:
            print(colored(" => Pressed [ENTER] Button on Twitter..", "blue"))
        time.sleep(2)

        # Add the post to the cache
        self.add_post({"content": body, "date": now.strftime("%m/%d/%Y, %H:%M:%S")})

        success("Posted to Twitter successfully!")

    def get_posts(self) -> List[dict]:
        """
        Gets the posts from the cache.

        Returns:
            posts (List[dict]): The posts
        """
        if not os.path.exists(get_twitter_cache_path()):
            # Create the cache file
            with open(get_twitter_cache_path(), "w") as file:
                json.dump({"accounts": []}, file, indent=4)

        with open(get_twitter_cache_path(), "r") as file:
            parsed = json.load(file)

            # Find our account
            accounts = parsed["accounts"]
            for account in accounts:
                if account["id"] == self.account_uuid:
                    posts = account["posts"]

                    if posts is None:
                        return []

                    # Return the posts
                    return posts

        return []

    def add_post(self, post: dict) -> None:
        """
        Adds a post to the cache.

        Args:
            post (dict): The post to add

        Returns:
            None
        """
        posts = self.get_posts()
        posts.append(post)

        with open(get_twitter_cache_path(), "r") as file:
            previous_json = json.loads(file.read())

            # Find our account
            accounts = previous_json["accounts"]
            for account in accounts:
                if account["id"] == self.account_uuid:
                    account["posts"].append(post)

            # Commit changes
            with open(get_twitter_cache_path(), "w") as f:
                f.write(json.dumps(previous_json))

    def generate_post(self) -> str:
        """
        Generates a post for the Twitter account based on the topic.

        Returns:
            post (str): The post
        """
        if get_verbose():
            info("Generating a post...")

        completion: Optional[str] = None
        rejection_reason: Optional[str] = None

        for attempt in range(3):
            prompt = self._build_post_prompt(rejection_reason)
            completion = generate_text(prompt)

            if completion is None:
                continue

            completion = self._clean_generated_post(completion)
            rejection_reason = self._get_post_rejection_reason(completion)

            if not rejection_reason:
                if get_verbose():
                    info(f"Length of post: {len(completion)}")
                if len(completion) >= 260:
                    return completion[:257].rsplit(" ", 1)[0] + "..."

                return completion

            if get_verbose():
                warning(
                    f"Twitter post attempt {attempt + 1} was rejected: {rejection_reason}"
                )

        if completion is None:
            error("Failed to generate a post. Please try again.")
            sys.exit(1)

        completion = self._clean_generated_post(completion)
        if len(completion) >= 260:
            completion = completion[:257].rsplit(" ", 1)[0] + "..."

        return completion

    def _build_post_prompt(self, rejection_reason: Optional[str] = None) -> str:
        """
        Builds a stricter prompt so the model returns one tweet instead of
        meta commentary or a list of options.

        Returns:
            prompt (str): LLM prompt for tweet generation
        """
        language_instruction = self._build_language_instruction()
        recent_posts = self.get_posts()[-5:]
        recent_examples = [
            post["content"].strip()
            for post in recent_posts
            if post.get("content")
        ]

        prompt_sections = [
            "Write exactly one ready-to-post X/Twitter post.",
            f"Topic: {self.topic}",
            f"{language_instruction}",
            (
                "Style: sound like a real person posting on social media, not a marketing bot, "
                "not a news anchor, and not a content generator."
            ),
            (
                "Write it like a native speaker who actually uses this dialect every day. "
                "It should feel casual, current, and believable."
            ),
            "Requirements:",
            "- Return only the final post text.",
            "- Focus on one specific, concrete angle of the topic.",
            "- Make it useful, opinionated, surprising, or relatable.",
            "- It should read like one real thought, tip, opinion, or observation someone would genuinely post.",
            "- Prefer a concrete example, use case, or practical detail over generic statements.",
            "- Maximum 2 short sentences.",
            "- Maximum 220 characters if possible, and never exceed 260 characters.",
            "- At most 1 emoji, and only if it feels natural.",
            "- Do not include explanations, introductions, option labels, headings, or quotation marks.",
            "- Do not say things like 'Here are a few options' or 'Option 1'.",
            "- Do not use placeholders, stage directions, or bracketed notes.",
            "- Do not write vague filler such as 'a new project', 'something interesting', or 'imagine that...'.",
            "- Do not use parentheses.",
            "- Avoid hashtags unless they are truly necessary.",
            "- Use concrete wording instead of generic hype.",
            "- Avoid sounding dramatic, cheesy, salesy, or AI-generated.",
            "- Avoid fake suspense, teaser language, and made-up news.",
            "- Do not start with generic hooks like 'يا جماعة الخير', 'هل تبحث', 'تخيل', or similar cliché openers.",
            "- Do not say 'قرينا', 'خبر مهم', or anything that sounds like a vague rumor unless the tweet includes a real concrete fact.",
            "- For Arabic dialect writing, prefer natural spoken phrasing over stiff Modern Standard Arabic unless the topic clearly needs formal language.",
            "Bad style example: يا جماعة الخير، الأخبار دي حلوة! قرينا على مشروع جديد في شركة…",
            "Good style example: أكتر استخدام فعلي للذكاء الاصطناعي في الشغل اليومي دلوقتي هو تلخيص الاجتماعات وكتابة الإيميلات بدل ما تضيع ساعة في كل مهمة.",
        ]

        if self.character_context:
            prompt_sections.extend(
                [
                    "Account character context:",
                    self.character_context,
                    "Stay consistent with that character's voice, worldview, audience, and recurring style.",
                ]
            )

        if recent_examples:
            prompt_sections.extend(
                [
                    "Avoid repeating the same tone or wording as these recent posts:",
                    *[f"- {example}" for example in recent_examples],
                ]
            )

        if rejection_reason:
            prompt_sections.extend(
                [
                    "The previous attempt was rejected.",
                    f"Reason: {rejection_reason}",
                    "Write a stronger replacement that fixes that problem.",
                ]
            )

        return "\n".join(prompt_sections)

    def _build_language_instruction(self) -> str:
        """
        Converts configured language/dialect values into an explicit writing
        instruction for the LLM.

        Returns:
            instruction (str): prompt-ready locale instruction
        """
        raw_language = get_twitter_language().strip()
        raw_dialect = get_twitter_dialect().strip()

        normalized_language = raw_language.lower().replace("-", "_").replace(" ", "_")

        aliases = {
            "arabic_eg": ("Arabic", "Egyptian Arabic"),
            "egyptian_arabic": ("Arabic", "Egyptian Arabic"),
            "arabic_egyptian": ("Arabic", "Egyptian Arabic"),
            "arabic_sa": ("Arabic", "Saudi Arabic"),
            "arabic_gulf": ("Arabic", "Gulf Arabic"),
            "arabic_levantine": ("Arabic", "Levantine Arabic"),
            "arabic_maghrebi": ("Arabic", "Maghrebi Arabic"),
            "darija": ("Arabic", "Moroccan Darija"),
        }

        if normalized_language in aliases:
            language, dialect = aliases[normalized_language]
        else:
            language = raw_language or "English"
            dialect = raw_dialect

        if dialect:
            return (
                f"Write in {dialect} dialect. The base language should be {language}. "
                "Use natural wording that sounds local and human, not formal textbook phrasing."
            )

        return f"Write in {language}."

    def _clean_generated_post(self, completion: str) -> str:
        """
        Removes common meta-output artifacts from LLM responses so we can post
        only the usable tweet text.

        Args:
            completion (str): raw LLM output

        Returns:
            cleaned (str): cleaned post text
        """
        cleaned = completion.replace("\r", "").strip()
        cleaned = re.sub(r"^```[\w-]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = re.sub(
            r"(?is)^okay[,!\s-]*here(?:'s| are)\s+.*?(?:\n\s*\n|\n)",
            "",
            cleaned,
        )

        option_block = re.search(
            r"(?is)option\s*1(?:\s*\([^)]*\))?\s*:\s*(.+?)(?=\n\s*option\s*2\b|\Z)",
            cleaned,
        )
        if option_block:
            cleaned = option_block.group(1).strip()

        cleaned = re.sub(r"(?im)^\s*option\s*\d+(?:\s*\([^)]*\))?\s*:\s*", "", cleaned)
        cleaned = re.sub(r"(?im)^\s*(twitter post|post|tweet)\s*:\s*", "", cleaned)
        cleaned = re.sub(r"(?im)^\s*[-*]\s*", "", cleaned)
        cleaned = cleaned.replace('"', "").replace("“", "").replace("”", "")

        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        cleaned = " ".join(lines)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -:\n\t")

        return cleaned

    def _looks_like_meta_output(self, completion: str) -> bool:
        """
        Detects whether the generated text still looks like instructions or a
        menu of options instead of a ready-to-post tweet.

        Args:
            completion (str): cleaned LLM output

        Returns:
            is_meta (bool): True when output still looks malformed
        """
        lowered = completion.lower()
        meta_markers = [
            "here are a few options",
            "option 1",
            "twitter post about",
            "ready-to-post",
            "concise & action-oriented",
        ]
        return any(marker in lowered for marker in meta_markers)

    def _get_post_rejection_reason(self, completion: str) -> Optional[str]:
        """
        Returns a human-readable rejection reason for poor tweet outputs.

        Args:
            completion (str): cleaned LLM output

        Returns:
            reason (Optional[str]): rejection reason, or None when acceptable
        """
        if not completion:
            return "The post was empty."

        if self._looks_like_meta_output(completion):
            return "The output still looked like instructions or multiple options."

        placeholder_patterns = [
            r"(?i)\bimagine\b",
            r"(?i)\bsomething interesting\b",
            r"(?i)\ba new project\b",
            r"تخيل",
            r"شيء مثير للاهتمام",
            r"مشروع جديد",
            r"يا جماعة الخير",
            r"هل تبحث",
            r"قرينا",
            r"خبر مهم",
        ]
        for pattern in placeholder_patterns:
            if re.search(pattern, completion):
                return "The post used generic filler or placeholder wording."

        if "(" in completion or ")" in completion:
            return "The post included stage directions or parenthetical notes."

        if completion.count("…") > 0 or "..." in completion:
            return "The post used vague trailing ellipses instead of a complete thought."

        if len(completion) < 25:
            return "The post was too short to be useful."

        return None
