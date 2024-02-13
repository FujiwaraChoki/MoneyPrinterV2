from config import *
from selenium_firefox import *
from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.common import keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

class AffiliateMarketing:
    """
    This class will be used to handle all the affiliate marketing related operations.    
    """
    def __init__(self, affiliate_link: str, fp_profile_path: str) -> None:
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

    def scrape_product_information(self) -> None:
        """
        This method will be used to scrape the product information from the affiliate link.
        """
        # Open the affiliate link
        self.browser.get(self.affiliate_link)

        # Get the product name
        try:
            product_name: str = self.browser.find_element(By.CLASS_NAME, "product-name").text
            print(f"Product Name: {product_name}")
        except exceptions.NoSuchElementException:
            print("Product Name not found.")

        # Get the product price
        try:
            product_price: str = self.browser.find_element(By.CLASS_NAME, "product-price").text
            print(f"Product Price: {product_price}")
        except exceptions.NoSuchElementException:
            print("Product Price not found.")

        # Get the product description
        try:
            product_description: str = self.browser.find_element(By.CLASS_NAME, "product-description").text
            print(f"Product Description: {product_description}")
        except exceptions.NoSuchElementException:
            print("Product Description not found.")