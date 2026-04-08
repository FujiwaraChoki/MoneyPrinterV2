import re
import sys
import time
import os
import json

from cache import *
from config import *
from status import *
from llm_provider import generate_text
from content_profile import (
    build_profile_context,
    has_service_strategy,
    load_case_brief,
    normalize_content_profile,
)
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

    def _variant_instruction(self) -> str:
        """
        Returns a specialized instruction block for the selected service variant.

        Returns:
            instruction (str): Variant-specific prompt guidance
        """
        variant = self.content_profile.get("content_variant", "general")

        if variant == "deployment":
            return (
                "Focus on shipping a real project from repo to running environment. "
                "Prefer setup pitfalls, environment mismatches, hosting choices, or launch blockers."
            )
        if variant == "hardening":
            return (
                "Focus on security, auth, exposure, secret handling, backup gaps, or operational risk reduction."
            )
        if variant == "customization":
            return (
                "Focus on adapting an existing project to a workflow, client need, UI change, or integration requirement."
            )

        return (
            "Focus on practical implementation lessons that can become reusable content, downloadable resources, or low-touch monetizable assets."
        )

    def _asset_instruction(self) -> str:
        """
        Returns specialized guidance for the selected asset type.

        Returns:
            instruction (str): Asset-specific prompt guidance
        """
        asset_type = self.content_profile.get("asset_type", "")
        capture_type = self.content_profile.get("capture_type", "")
        monetization_type = self.content_profile.get("monetization_type", "")

        return (
            f"Primary asset type: {asset_type or 'general content asset'}. "
            f"Capture type: {capture_type or 'none'}. "
            f"Monetization type: {monetization_type or 'none'}. "
            "The post should nudge the reader toward a reusable asset or owned relationship, not only a direct service sale."
        )

    def __init__(
        self,
        account_uuid: str,
        account_nickname: str,
        fp_profile_path: str,
        topic: str,
        content_profile: dict | None = None,
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
        self.content_profile = normalize_content_profile(content_profile)
        self.case_brief = load_case_brief(self.content_profile)

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
        if has_service_strategy(self.content_profile):
            completion = generate_text(
                f"""
                Write a concise X post in {get_twitter_language()} for a technical content and audience-building business.

                Topic / angle: {self.topic}
                {build_profile_context(self.content_profile)}
                Reusable case brief:
                {self.case_brief or "None"}
                Variant guidance:
                {self._variant_instruction()}
                Asset guidance:
                {self._asset_instruction()}

                Requirements:
                - Maximum 240 characters
                - Sound like a calm operator, not a hype marketer
                - Mention one concrete problem and one practical insight
                - Prefer deployment, security, workflow, cost, or implementation lessons
                - Avoid generic inspiration, vague AI hot takes, and empty engagement bait
                - If there is a CTA, point to a reusable asset, subscription, download, or owned destination before direct selling
                - Only return the post text
                """
            )
        else:
            completion = generate_text(
                f"Generate a Twitter post about: {self.topic} in {get_twitter_language()}. "
                "The Limit is 2 sentences. Choose a specific sub-topic of the provided topic."
            )

        if get_verbose():
            info("Generating a post...")

        if completion is None:
            error("Failed to generate a post. Please try again.")
            sys.exit(1)

        # Apply Regex to remove all *
        completion = re.sub(r"\*", "", completion).replace('"', "")

        if has_service_strategy(self.content_profile):
            completion = self.review_post(completion)

        if get_verbose():
            info(f"Length of post: {len(completion)}")
        if len(completion) >= 260:
            return completion[:257].rsplit(" ", 1)[0] + "..."

        return completion

    def review_post(self, draft: str) -> str:
        """
        Reviews the generated post against service-led quality constraints.

        Args:
            draft (str): Initial generated post

        Returns:
            post (str): Reviewed post
        """
        reviewed = generate_text(
            f"""
            Review and improve this X post for a technical asset-building operator.

            Draft:
            {draft}

            Context:
            Topic / angle: {self.topic}
            {build_profile_context(self.content_profile)}
            Reusable case brief:
            {self.case_brief or "None"}
            Variant guidance:
            {self._variant_instruction()}
            Asset guidance:
            {self._asset_instruction()}

            Requirements:
            - Keep the core meaning
            - Remove hype, fluff, and generic AI phrasing
            - Make it sound specific, credible, and useful
            - Prefer owned-audience or reusable-asset direction over hard selling
            - Keep it under 240 characters
            - Only return the final post
            """
        )

        cleaned = re.sub(r"\*", "", reviewed).replace('"', "").strip()
        return cleaned or draft
