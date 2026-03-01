import g4f

from status import *
from config import *
from constants import *
from .Twitter import Twitter
from selenium_firefox import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

class AffiliateMarketing:
    """
    This class will be used to handle all the affiliate marketing related operations.    
    """
    def __init__(self, affiliate_link: str, fp_profile_path: str, twitter_account_uuid: str, account_nickname: str, topic: str) -> None:
        """
        Initializes the Affiliate Marketing class.

        Args:
            affiliate_link (str): The affiliate link
            fp_profile_path (str): The path to the Firefox profile
            twitter_account_uuid (str): The Twitter account UUID
            account_nickname (str): The account nickname
            topic (str): The topic of the product

        Returns:
            None
        """
        self._fp_profile_path: str = fp_profile_path

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

        # Set the affiliate link
        self.affiliate_link: str = affiliate_link

        # Set the Twitter account UUID
        self.account_uuid: str = twitter_account_uuid

        # Set the Twitter account nickname
        self.account_nickname: str = account_nickname

        # Set the Twitter topic
        self.topic: str = topic

        # Scrape the product information
        self.scrape_product_information()

    def scrape_product_information(self) -> None:
        """
        This method will be used to scrape the product
        information from the affiliate link.
        """
        # Open the affiliate link
        self.browser.get(self.affiliate_link)

        # Get the product name
        product_title: str = self.browser.find_element(By.ID, AMAZON_PRODUCT_TITLE_ID).text
        
        # Get the features of the product
        features: any = self.browser.find_elements(By.ID, AMAZON_FEATURE_BULLETS_ID)

        if get_verbose():
            info(f"Product Title: {product_title}")

        if get_verbose():
            info(f"Features: {features}")
            
        # Set the product title
        self.product_title: str = product_title

        # Set the features
        self.features: any = features

    def generate_response(self, prompt: str) -> str:
        """
        This method will be used to generate the response for the user.

        Args:
            prompt (str): The prompt for the user.

        Returns:
            response (str): The response for the user.
        """
        if get_model() == "google":
            import google.generativeai as genai

            genai.configure(api_key=get_gemini_api_key())

            model = genai.GenerativeModel('gemini-pro')

            response: str = model.generate_content(prompt).text

            return response

        # Generate the response
        response: str = g4f.ChatCompletion.create(
            model=parse_model(get_model()),
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Return the response
        return response

    def generate_pitch(self) -> str:
        """
        This method will be used to generate a pitch for the product.

        Returns:
            pitch (str): The pitch for the product.
        """
        # Generate the response
        pitch: str = self.generate_response(f"I want to promote this product on my website. Generate a brief pitch about this product, return nothing else except the pitch. Information:\nTitle: \"{self.product_title}\"\nFeatures: \"{str(self.features)}\"") + "\nYou can buy the product here: " + self.affiliate_link

        self.pitch: str = pitch

        # Return the response
        return pitch
    
    def share_pitch(self, where: str) -> None:
        """
        This method will be used to share the pitch on the specified platform.

        Args:
            where (str): The platform where the pitch will be shared.
        """
        if where == "twitter":
            # Initialize the Twitter class
            twitter: Twitter = Twitter(self.account_uuid, self.account_nickname, self._fp_profile_path, self.topic)

            # Share the pitch
            twitter.post(self.pitch)

    def quit(self) -> None:
        """
        This method will be used to quit the browser.
        """
        # Quit the browser
        self.browser.quit()
