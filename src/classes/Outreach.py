import os
import io
import re
import csv
import time
import glob
import shlex
import zipfile
import yagmail
import requests
import subprocess
import platform

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

    def _find_scraper_dir(self) -> str:
        candidates = sorted(glob.glob("google-maps-scraper-*"))
        for candidate in candidates:
            if os.path.isdir(candidate) and os.path.exists(
                os.path.join(candidate, "go.mod")
            ):
                return candidate
        return ""

    def is_go_installed(self) -> bool:
        """
        Check if go is installed.

        Returns:
            bool: True if go is installed, False otherwise.
        """
        # Check if go is installed
        try:
            subprocess.call(["go", "version"])
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
        if self._find_scraper_dir():
            info("=> Scraper ya descomprimido. Omitiendo descompresión.")
            return

        r = requests.get(zip_link)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        for member in z.namelist():
            if ".." in member or member.startswith("/"):
                warning(f"Omitiendo ruta sospechosa en el archivo: {member}")
                continue
            z.extract(member)

    def build_scraper(self) -> None:
        """
        Build the scraper.

        Returns:
            None
        """
        binary_name = (
            "google-maps-scraper.exe"
            if platform.system() == "Windows"
            else "google-maps-scraper"
        )
        if os.path.exists(binary_name):
            print(colored("=> Scraper ya compilado. Omitiendo compilación.", "blue"))
            return

        scraper_dir = self._find_scraper_dir()
        if not scraper_dir:
            raise FileNotFoundError(
                "No se pudo encontrar el directorio extraído de google-maps-scraper."
            )

        subprocess.run(["go", "mod", "download"], cwd=scraper_dir, check=True)
        subprocess.run(["go", "build"], cwd=scraper_dir, check=True)

        built_binary = os.path.join(scraper_dir, binary_name)
        if not os.path.exists(built_binary):
            raise FileNotFoundError(f"Se esperaba el binario del scraper compilado en: {built_binary}")

        os.replace(built_binary, binary_name)

    def run_scraper_with_args_for_30_seconds(self, args: str, timeout=300) -> None:
        """
        Run the scraper with the specified arguments for 30 seconds.

        Args:
            args (str): The arguments to run the scraper with.
            timeout (int): The time to run the scraper for.

        Returns:
            None
        """
        info(" => Ejecutando scraper...")
        binary_name = (
            "google-maps-scraper.exe"
            if platform.system() == "Windows"
            else "google-maps-scraper"
        )
        command = [os.path.join(os.getcwd(), binary_name)] + shlex.split(args)
        try:
            scraper_process = subprocess.run(command, timeout=float(timeout))

            if scraper_process.returncode == 0:
                print(colored("=> Scraper finalizado exitosamente.", "green"))
            else:
                print(colored("=> Scraper finalizó con un error.", "red"))
        except subprocess.TimeoutExpired:
            print(colored("=> Scraper agotó el tiempo de espera.", "red"))
        except Exception as e:
            print(colored("Ocurrió un error al ejecutar el scraper:", "red"))
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
        """Extracts an email address from a website and updates a CSV file with it.

        This method sends a GET request to the specified website, searches for the
        first email address in the HTML content, and appends it to the specified
        row in a CSV file. If no email address is found, no changes are made to
        the CSV file.

        Args:
            index (int): The row index in the CSV file where the email should be appended.
            website (str): The URL of the website to extract the email address from.
            output_file (str): The path to the CSV file to update with the extracted email."""
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
            print(f"=> Configurando email {email} para el sitio web {website}")
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
            error("Go no está instalado. Por favor, instalá Go e intentá de nuevo.")
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
        self.run_scraper_with_args_for_30_seconds(
            f'-input niche.txt -results "{output_path}"', timeout=get_scraper_timeout()
        )

        if not os.path.exists(output_path):
            error(
                f" => No se encontró la salida del scraper en {output_path}. Revisá los logs y la configuración del scraper."
            )
            os.remove("niche.txt")
            return

        # Get the items from the file
        items = self.get_items_from_file(output_path)
        success(f" => Se extrajeron {len(items)} elementos.")

        # Remove the niche file
        os.remove("niche.txt")

        time.sleep(2)

        # Create a yagmail SMTP client outside the loop
        yag = yagmail.SMTP(
            user=self.email_creds["username"],
            password=self.email_creds["password"],
            host=self.email_creds["smtp_server"],
            port=self.email_creds["smtp_port"],
        )

        # Get the email for each business
        for index, item in enumerate(items, start=1):
            try:
                # Check if the item"s website is valid
                website = item.split(",")
                website = [w for w in website if w.startswith("http")]
                website = website[0] if len(website) > 0 else ""
                if website != "":
                    test_r = requests.get(website)
                    if test_r.status_code == 200:
                        self.set_email_for_website(index, website, output_path)

                        # Send emails using the existing SMTP connection
                        receiver_email = item.split(",")[-1]

                        if "@" not in receiver_email:
                            warning(f" => No se proporcionó email. Omitiendo...")
                            continue

                        company_name = item.split(",")[0]
                        subject = message_subject.replace(
                            "{{COMPANY_NAME}}", company_name
                        )
                        body = (
                            open(message_body, "r")
                            .read()
                            .replace("{{COMPANY_NAME}}", company_name)
                        )

                        info(f" => Enviando email a {receiver_email}...")

                        yag.send(
                            to=receiver_email,
                            subject=subject,
                            contents=body,
                        )

                        success(f" => Email enviado a {receiver_email}")
                    else:
                        warning(f" => El sitio web {website} es inválido. Omitiendo...")
            except Exception as err:
                error(f" => Error: {err}...")
                continue
