import os
import io
import re
import csv
import time
import zipfile
import yagmail
import requests
import subprocess

from cache import *
from status import *
from config import *

class Outreach:
    """
    Class that houses the methods to reach out to businesses.
    """
    def __init__(self) -> None:
        """
        Constructor for the Outreach class.

        Returns:
            None
        """
        # Check if go is installed
        self.go_installed = os.system("go version") == 0

        # Set niche
        self.niche = get_google_maps_scraper_niche()

        # Set email credentials
        self.email_creds = get_email_credentials()

    def is_go_installed(self) -> bool:
        """
        Check if go is installed.

        Returns:
            bool: True if go is installed, False otherwise.
        """
        # Check if go is installed
        try:
            subprocess.call("go version", shell=True)
            return True
        except Exception as e:
            return False

    def unzip_file(self, zip_link: str) -> None:
        """
        Unzip the file.

        Args:
            zip_link (str): The link to the zip file.

        Returns:
            None
        """
        # Check if the scraper is already unzipped, if not, unzip it
        if os.path.exists("google-maps-scraper-0.9.7"):
            info("=> Scraper already unzipped. Skipping unzip.")
            return

        r = requests.get(zip_link)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall()

    def build_scraper(self) -> None:
        """
        Build the scraper.

        Returns:
            None
        """
        # Check if the scraper is already built, if not, build it
        if os.path.exists("google-maps-scraper.exe"):
            print(colored("=> Scraper already built. Skipping build.", "blue"))
            return

        os.chdir("google-maps-scraper-0.9.7")
        os.system("go mod download")
        os.system("go build")
        os.system("mv google-maps-scraper ../google-maps-scraper")
        os.chdir("..")

    def run_scraper_with_args_for_30_seconds(self, args: str, timeout = 300) -> None:
        """
        Run the scraper with the specified arguments for 30 seconds.

        Args:
            args (str): The arguments to run the scraper with.
            timeout (int): The time to run the scraper for.

        Returns:
            None
        """
        # Run the scraper with the specified arguments
        info(" => Running scraper...")
        command = "google-maps-scraper " + args
        try:
            scraper_process = subprocess.call(command.split(" "), shell=True, timeout=float(timeout))

            if scraper_process == 0:
                subprocess.call("taskkill /f /im google-maps-scraper.exe", shell=True)
                print(colored("=> Scraper finished successfully.", "green"))
            else:
                subprocess.call("taskkill /f /im google-maps-scraper.exe", shell=True)
                print(colored("=> Scraper finished with an error.", "red"))
            
        except Exception as e:
            subprocess.call("taskkill /f /im google-maps-scraper.exe", shell=True)
            print(colored("An error occurred while running the scraper:", "red"))
            print(str(e))

    def get_items_from_file(self, file_name: str) -> list:
        """
        Read and return items from a file.

        Args:
            file_name (str): The name of the file to read from.

        Returns:
            list: The items from the file.
        """
        # Read and return items from a file
        with open(file_name, "r", errors="ignore") as f:
            items = f.readlines()
            items = [item.strip() for item in items[1:]]
            return items
        
    def set_email_for_website(self, index: int, website: str, output_file: str):
        # Extract and set an email for a website
        email = ""

        r = requests.get(website)
        if r.status_code == 200:
            # Define a regular expression pattern to match email addresses
            email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"

            # Find all email addresses in the HTML string
            email_addresses = re.findall(email_pattern, r.text)

            email = email_addresses[0] if len(email_addresses) > 0 else ""

        if email:
            print(f"=> Setting email {email} for website {website}")
            with open(output_file, "r", newline="", errors="ignore") as csvfile:
                csvreader = csv.reader(csvfile)
                items = list(csvreader)
                items[index].append(email)

            with open(output_file, "w", newline="", errors="ignore") as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerows(items)
        
    def start(self) -> None:
        """
        Start the outreach process.

        Returns:
            None
        """
        # Check if go is installed
        if not self.is_go_installed():
            error("Go is not installed. Please install go and try again.")
            return

        # Unzip the scraper
        self.unzip_file(get_google_maps_scraper_zip_url())

        # Build the scraper
        self.build_scraper()

        # Write the niche to a file
        with open("niche.txt", "w") as f:
            f.write(self.niche)

        output_path = get_results_cache_path()
        message_subject = get_outreach_message_subject()
        message_body = get_outreach_message_body_file()

        # Run
        self.run_scraper_with_args_for_30_seconds(f"-input niche.txt -results \"{output_path}\"", timeout=get_scraper_timeout())

        # Get the items from the file
        items = self.get_items_from_file(output_path)
        success(f" => Scraped {len(items)} items.")

        # Remove the niche file
        os.remove("niche.txt")

        time.sleep(2)

        # Create a yagmail SMTP client outside the loop
        yag = yagmail.SMTP(user=self.email_creds["username"], password=self.email_creds["password"], host=self.email_creds["smtp_server"], port=self.email_creds["smtp_port"])

        # Get the email for each business
        for item in items:
            try:
                # Check if the item"s website is valid
                website = item.split(",")
                website = [w for w in website if w.startswith("http")]
                website = website[0] if len(website) > 0 else ""
                if website != "":
                    test_r = requests.get(website)
                    if test_r.status_code == 200:
                        self.set_email_for_website(items.index(item), website, output_path)
                        
                        # Send emails using the existing SMTP connection
                        receiver_email = item.split(",")[-1]

                        if "@" not in receiver_email:
                            warning(f" => No email provided. Skipping...")
                            continue

                        subject = message_subject.replace("{{COMPANY_NAME}}", item[0])
                        body = open(message_body, "r").read().replace("{{COMPANY_NAME}}", item[0])

                        info(f" => Sending email to {receiver_email}...")
                        
                        yag.send(
                            to=receiver_email,
                            subject=subject,
                            contents=body,
                        )

                        success(f" => Sent email to {receiver_email}")
                    else:
                        warning(f" => Website {website} is invalid. Skipping...")
            except Exception as err:
                error(f" => Error: {err}...")
                continue