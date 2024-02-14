import re
import g4f
import sys
import time

from cache import *
from config import *
from status import *
from constants import *
from typing import List
from datetime import datetime
from termcolor import colored
from selenium_firefox import *
from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.common import keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager


class Twitter:
    """
    Class for the Bot, that grows a Twitter account.
    """
    def __init__(self, account_uuid: str, account_nickname: str, fp_profile_path: str, topic: str) -> None:
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

        # Initialize the Firefox profile
        self.options: Options = Options()
        
        # Set headless state of browser
        if get_headless():
            self.options.add_argument("--headless")

        # Set the profile path
        self.options.add_argument("-profile")
        self.options.add_argument(fp_profile_path)

        # Set the service
        self.service: Service = Service(GeckoDriverManager().install())

        # Initialize the browser
        self.browser: webdriver.Firefox = webdriver.Firefox(service=self.service, options=self.options)

    def post(self, text: str = None) -> None:
        """
        Starts the Twitter Bot.

        Args:
            text (str): The text to post

        Returns:
            None
        """
        bot: webdriver.Firefox = self.browser
        verbose: bool = get_verbose()

        bot.get("https://twitter.com")

        time.sleep(2)

        post_content: str = self.generate_post()
        now: datetime = datetime.now()

        print(colored(f" => Posting to Twitter:", "blue"), post_content[:30] + "...")

        try:
            bot.find_element(By.XPATH, "//a[@data-testid='SideNav_NewTweet_Button']").click()
        except exceptions.NoSuchElementException:
            time.sleep(3)
            bot.find_element(By.XPATH, "//a[@data-testid='SideNav_NewTweet_Button']").click()

        time.sleep(2) 
        body = post_content if text is None else text

        try:
            bot.find_element(By.XPATH, "//div[@role='textbox']").send_keys(body)
        except exceptions.NoSuchElementException:
            time.sleep(2)
            bot.find_element(By.XPATH, "//div[@role='textbox']").send_keys(body)

        time.sleep(1)
        bot.find_element(By.CLASS_NAME, "notranslate").send_keys(keys.Keys.ENTER)
        bot.find_element(By.XPATH, "//div[@data-testid='tweetButton']").click()

        if verbose:
            print(colored(" => Pressed [ENTER] Button on Twitter..", "blue"))
        time.sleep(4)

        # Add the post to the cache
        self.add_post({
            "content": post_content,
            "date": now.strftime("%m/%d/%Y, %H:%M:%S")
        })

        success("Posted to Twitter successfully!")


    def get_posts(self) -> List[dict]:
        """
        Gets the posts from the cache.

        Returns:
            posts (List[dict]): The posts
        """
        if not os.path.exists(get_twitter_cache_path()):
            # Create the cache file
            with open(get_twitter_cache_path(), 'w') as file:
                json.dump({
                    "posts": []
                }, file, indent=4)

        with open(get_twitter_cache_path(), 'r') as file:
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
        completion = g4f.ChatCompletion.create(
            model=parse_model(get_model()),
            messages=[
                {
                    "role": "user",
                    "content": f"Generate a Twitter post about: {self.topic} in {get_twitter_language()}. The Limit is 2 sentences. Choose a specific sub-topic of the provided topic."
                }
            ]
        )

        if get_verbose():
            info("Generating a post...")

        if completion is None:
            error("Failed to generate a post. Please try again.")
            sys.exit(1)

        # Apply Regex to remove all *
        completion = re.sub(r"\*", "", completion).replace("\"", "")
    
        if get_verbose():
            info(f"Length of post: {len(completion)}")
        if len(completion) >= 260:
            return self.generate_post()

        return completion
