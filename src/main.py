import os
import sys
import shlex

import subprocess

from art import *
from cache import *
from utils import *
from config import *
from status import *
from uuid import uuid4
from constants import *
from termcolor import colored
from prettytable import PrettyTable
from llm_provider import select_model
from post_bridge_integration import maybe_crosspost_youtube_short


CRON_OPTION_SCHEDULES = {
    1: ["0 10 * * *"],
    2: ["0 10 * * *", "0 16 * * *"],
    3: ["0 8 * * *", "0 12 * * *", "0 18 * * *"],
}
CRON_PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

def bootstrap_runtime() -> None:
    fetch_songs()
    configured_model = get_openrouter_model()
    if not get_openrouter_api_key():
        error("No OpenRouter API key configured. Set openrouter_api_key or OPENROUTER_API_KEY.")
        sys.exit(1)
    if not configured_model:
        error("No OpenRouter model configured. Set openrouter_model or OPENROUTER_MODEL.")
        sys.exit(1)
    select_model(configured_model)
    success(f"Using configured OpenRouter model: {configured_model}")


def build_cron_command(
    purpose: str, account_id: str, model: str | None = None
) -> list[str]:
    command = [sys.executable, os.path.join(ROOT_DIR, "src", "cron.py"), purpose, account_id]
    if model:
        command.append(model)
    return command


def build_crontab_block(
    purpose: str,
    account_id: str,
    frequency_option: int,
    model: str | None = None,
) -> str:
    schedules = CRON_OPTION_SCHEDULES.get(frequency_option)
    if not schedules:
        raise ValueError(f"Unsupported cron frequency option: {frequency_option}")

    os.makedirs(os.path.join(ROOT_DIR, ".mp"), exist_ok=True)

    command = " ".join(
        shlex.quote(part) for part in build_cron_command(purpose, account_id, model)
    )
    log_path = os.path.join(ROOT_DIR, ".mp", f"cron-{purpose}-{account_id}.log")
    marker = f"MONEYPRINTER_V2 {purpose} {account_id}"

    lines = [f"# {marker} BEGIN"]
    for schedule_expression in schedules:
        lines.append(
            f"{schedule_expression} PATH={shlex.quote(CRON_PATH)}; export PATH; "
            f"cd {shlex.quote(ROOT_DIR)} && {command} >> {shlex.quote(log_path)} 2>&1"
        )
    lines.append(f"# {marker} END")

    return "\n".join(lines)


def merge_crontab_block(
    existing_crontab: str,
    purpose: str,
    account_id: str,
    new_block: str,
) -> str:
    begin_marker = f"# MONEYPRINTER_V2 {purpose} {account_id} BEGIN"
    end_marker = f"# MONEYPRINTER_V2 {purpose} {account_id} END"

    merged_lines = []
    skipping = False

    for line in str(existing_crontab or "").splitlines():
        stripped = line.strip()
        if stripped == begin_marker:
            skipping = True
            continue
        if skipping and stripped == end_marker:
            skipping = False
            continue
        if not skipping:
            merged_lines.append(line)

    while merged_lines and not merged_lines[-1].strip():
        merged_lines.pop()

    if merged_lines:
        merged_lines.append("")

    merged_lines.extend(new_block.splitlines())
    return "\n".join(merged_lines).rstrip() + "\n"


def install_cron_job(
    purpose: str,
    account_id: str,
    frequency_option: int,
    model: str | None = None,
) -> str:
    try:
        read_result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "crontab command is not available. Install cron/crontab and ensure it is on PATH."
        ) from exc

    if read_result.returncode == 0:
        existing_crontab = read_result.stdout
    else:
        missing_crontab_text = f"{read_result.stdout}\n{read_result.stderr}".lower()
        if "no crontab" in missing_crontab_text:
            existing_crontab = ""
        else:
            raise RuntimeError(
                f"Failed to read existing crontab: {(read_result.stderr or read_result.stdout).strip()}"
            )

    new_block = build_crontab_block(purpose, account_id, frequency_option, model)
    merged_crontab = merge_crontab_block(
        existing_crontab,
        purpose,
        account_id,
        new_block,
    )

    try:
        write_result = subprocess.run(
            ["crontab", "-"],
            input=merged_crontab,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "crontab command is not available. Install cron/crontab and ensure it is on PATH."
        ) from exc

    if write_result.returncode != 0:
        raise RuntimeError(
            f"Failed to install crontab entry: {(write_result.stderr or write_result.stdout).strip()}"
        )

    return merged_crontab


def maybe_upload_youtube_video(youtube) -> bool:
    upload_to_yt = question("Do you want to upload this video to YouTube? (Yes/No): ")
    if upload_to_yt.strip().lower() != "yes":
        return False

    while True:
        upload_success = youtube.upload_video()
        if upload_success:
            maybe_crosspost_youtube_short(
                video_path=youtube.video_path,
                title=youtube.metadata.get("title", ""),
                interactive=True,
            )
            return True

        if not getattr(youtube, "last_upload_retry_allowed", True):
            warning(
                "YouTube upload may already exist in Studio. Skipping automatic retry and Post Bridge cross-post."
            )
            return False

        retry_upload = question(
            "Retry YouTube upload with the same video? (Yes/No): "
        )
        if retry_upload.strip().lower() != "yes":
            warning("YouTube upload failed. Skipping Post Bridge cross-post.")
            return False


def main():
    """Main entry point for the application, providing a menu-driven interface
    to manage YouTube, Twitter bots, Affiliate Marketing, and Outreach tasks.

    This function allows users to:
    1. Start the YouTube Shorts Automater to manage YouTube accounts, 
       generate and upload videos, and set up CRON jobs.
    2. Start a Twitter Bot to manage Twitter accounts, post tweets, and 
       schedule posts using CRON jobs.
    3. Manage Affiliate Marketing by creating pitches and sharing them via 
       Twitter accounts.
    4. Initiate an Outreach process for engagement and promotion tasks.
    5. Exit the application.

    The function continuously prompts users for input, validates it, and 
    executes the selected option until the user chooses to quit.

    Args:
        None

    Returns:
        None"""

    # Get user input
    # user_input = int(question("Select an option: "))
    valid_input = False
    while not valid_input:
        try:
    # Show user options
            info("\n============ OPTIONS ============", False)

            for idx, option in enumerate(OPTIONS):
                print(colored(f" {idx + 1}. {option}", "cyan"))

            info("=================================\n", False)
            user_input = input("Select an option: ").strip()
            if user_input == '':
                print("\n" * 100)
                raise ValueError("Empty input is not allowed.")
            user_input = int(user_input)
            valid_input = True
        except ValueError as e:
            print("\n" * 100)
            print(f"Invalid input: {e}")


    # Start the selected option
    if user_input == 1:
        info("Starting YT Shorts Automater...")

        cached_accounts = get_accounts("youtube")

        if len(cached_accounts) == 0:
            warning("No accounts found in cache. Create one now?")
            user_input = question("Yes/No: ")

            if user_input.lower() == "yes":
                generated_uuid = str(uuid4())

                success(f" => Generated ID: {generated_uuid}")
                nickname = question(" => Enter a nickname for this account: ")
                fp_profile = question(" => Enter the path to the Firefox profile: ")
                niche = question(" => Enter the account niche: ")
                language = question(" => Enter the account language: ")

                account_data = {
                    "id": generated_uuid,
                    "nickname": nickname,
                    "firefox_profile": fp_profile,
                    "niche": niche,
                    "language": language,
                    "videos": [],
                }

                add_account("youtube", account_data)

                success("Account configured successfully!")
        else:
            table = PrettyTable()
            table.field_names = ["ID", "UUID", "Nickname", "Niche"]

            for account in cached_accounts:
                table.add_row([cached_accounts.index(account) + 1, colored(account["id"], "cyan"), colored(account["nickname"], "blue"), colored(account["niche"], "green")])

            print(table)
            info("Type 'd' to delete an account.", False)

            user_input = question("Select an account to start (or 'd' to delete): ").strip()

            if user_input.lower() == "d":
                delete_input = question("Enter account number to delete: ").strip()
                account_to_delete = None

                for account in cached_accounts:
                    if str(cached_accounts.index(account) + 1) == delete_input:
                        account_to_delete = account
                        break

                if account_to_delete is None:
                    error("Invalid account selected. Please try again.", "red")
                else:
                    confirm = question(f"Are you sure you want to delete '{account_to_delete['nickname']}'? (Yes/No): ").strip().lower()

                    if confirm == "yes":
                        remove_account("youtube", account_to_delete["id"])
                        success("Account removed successfully!")
                    else:
                        warning("Account deletion canceled.", False)

                return

            selected_account = None

            for account in cached_accounts:
                if str(cached_accounts.index(account) + 1) == user_input:
                    selected_account = account

            if selected_account is None:
                error("Invalid account selected. Please try again.", "red")
                main()
            else:
                from classes.YouTube import YouTube

                youtube = YouTube(
                    selected_account["id"],
                    selected_account["nickname"],
                    selected_account["firefox_profile"],
                    selected_account["niche"],
                    selected_account["language"]
                )

                while True:
                    rem_temp_files()
                    info("\n============ OPTIONS ============", False)

                    for idx, youtube_option in enumerate(YOUTUBE_OPTIONS):
                        print(colored(f" {idx + 1}. {youtube_option}", "cyan"))

                    info("=================================\n", False)

                    # Get user input
                    user_input = int(question("Select an option: "))
                    from classes.Tts import TTS
                    tts = TTS()

                    if user_input == 1:
                        youtube.generate_video(tts)
                        maybe_upload_youtube_video(youtube)
                    elif user_input == 2:
                        videos = youtube.get_videos()

                        if len(videos) > 0:
                            videos_table = PrettyTable()
                            videos_table.field_names = ["ID", "Date", "Title"]

                            for video in videos:
                                videos_table.add_row([
                                    videos.index(video) + 1,
                                    colored(video["date"], "blue"),
                                    colored(video["title"][:60] + "...", "green")
                                ])

                            print(videos_table)
                        else:
                            warning(" No videos found.")
                    elif user_input == 3:
                        info("How often do you want to upload?")

                        info("\n============ OPTIONS ============", False)
                        for idx, cron_option in enumerate(YOUTUBE_CRON_OPTIONS):
                            print(colored(f" {idx + 1}. {cron_option}", "cyan"))

                        info("=================================\n", False)

                        user_input = int(question("Select an Option: "))

                        if user_input in CRON_OPTION_SCHEDULES:
                            install_cron_job("youtube", selected_account["id"], user_input)
                            success("Set up CRON Job.")
                        else:
                            break
                    elif user_input == 4:
                        if get_verbose():
                            info(" => Climbing Options Ladder...", False)
                        break
    elif user_input == 2:
        info("Starting Twitter Bot...")

        cached_accounts = get_accounts("twitter")

        if len(cached_accounts) == 0:
            warning("No accounts found in cache. Create one now?")
            user_input = question("Yes/No: ")

            if user_input.lower() == "yes":
                generated_uuid = str(uuid4())

                success(f" => Generated ID: {generated_uuid}")
                nickname = question(" => Enter a nickname for this account: ")
                fp_profile = question(" => Enter the path to the Firefox profile: ")
                topic = question(" => Enter the account topic: ")

                add_account("twitter", {
                    "id": generated_uuid,
                    "nickname": nickname,
                    "firefox_profile": fp_profile,
                    "topic": topic,
                    "posts": []
                })
        else:
            table = PrettyTable()
            table.field_names = ["ID", "UUID", "Nickname", "Account Topic"]

            for account in cached_accounts:
                table.add_row([cached_accounts.index(account) + 1, colored(account["id"], "cyan"), colored(account["nickname"], "blue"), colored(account["topic"], "green")])

            print(table)
            info("Type 'd' to delete an account.", False)

            user_input = question("Select an account to start (or 'd' to delete): ").strip()

            if user_input.lower() == "d":
                delete_input = question("Enter account number to delete: ").strip()
                account_to_delete = None

                for account in cached_accounts:
                    if str(cached_accounts.index(account) + 1) == delete_input:
                        account_to_delete = account
                        break

                if account_to_delete is None:
                    error("Invalid account selected. Please try again.", "red")
                else:
                    confirm = question(f"Are you sure you want to delete '{account_to_delete['nickname']}'? (Yes/No): ").strip().lower()

                    if confirm == "yes":
                        remove_account("twitter", account_to_delete["id"])
                        success("Account removed successfully!")
                    else:
                        warning("Account deletion canceled.", False)

                return

            selected_account = None

            for account in cached_accounts:
                if str(cached_accounts.index(account) + 1) == user_input:
                    selected_account = account

            if selected_account is None:
                error("Invalid account selected. Please try again.", "red")
                main()
            else:
                from classes.Twitter import Twitter

                twitter = Twitter(selected_account["id"], selected_account["nickname"], selected_account["firefox_profile"], selected_account["topic"])

                while True:
                    
                    info("\n============ OPTIONS ============", False)

                    for idx, twitter_option in enumerate(TWITTER_OPTIONS):
                        print(colored(f" {idx + 1}. {twitter_option}", "cyan"))

                    info("=================================\n", False)

                    # Get user input
                    user_input = int(question("Select an option: "))

                    if user_input == 1:
                        twitter.post()
                    elif user_input == 2:
                        posts = twitter.get_posts()

                        posts_table = PrettyTable()

                        posts_table.field_names = ["ID", "Date", "Content"]

                        for post in posts:
                            posts_table.add_row([
                                posts.index(post) + 1,
                                colored(post["date"], "blue"),
                                colored(post["content"][:60] + "...", "green")
                            ])

                        print(posts_table)
                    elif user_input == 3:
                        info("How often do you want to post?")

                        info("\n============ OPTIONS ============", False)
                        for idx, cron_option in enumerate(TWITTER_CRON_OPTIONS):
                            print(colored(f" {idx + 1}. {cron_option}", "cyan"))

                        info("=================================\n", False)

                        user_input = int(question("Select an Option: "))

                        if user_input in CRON_OPTION_SCHEDULES:
                            install_cron_job("twitter", selected_account["id"], user_input)
                            success("Set up CRON Job.")
                        else:
                            break
                    elif user_input == 4:
                        if get_verbose():
                            info(" => Climbing Options Ladder...", False)
                        break
    elif user_input == 3:
        info("Starting Affiliate Marketing...")

        cached_products = get_products()

        if len(cached_products) == 0:
            warning("No products found in cache. Create one now?")
            user_input = question("Yes/No: ")

            if user_input.lower() == "yes":
                affiliate_link = question(" => Enter the affiliate link: ")
                twitter_uuid = question(" => Enter the Twitter Account UUID: ")

                # Find the account
                account = None
                for acc in get_accounts("twitter"):
                    if acc["id"] == twitter_uuid:
                        account = acc

                add_product({
                    "id": str(uuid4()),
                    "affiliate_link": affiliate_link,
                    "twitter_uuid": twitter_uuid
                })

                from classes.AFM import AffiliateMarketing

                afm = AffiliateMarketing(affiliate_link, account["firefox_profile"], account["id"], account["nickname"], account["topic"])

                afm.generate_pitch()
                afm.share_pitch("twitter")
        else:
            table = PrettyTable()
            table.field_names = ["ID", "Affiliate Link", "Twitter Account UUID"]

            for product in cached_products:
                table.add_row([cached_products.index(product) + 1, colored(product["affiliate_link"], "cyan"), colored(product["twitter_uuid"], "blue")])

            print(table)

            user_input = question("Select a product to start: ")

            selected_product = None

            for product in cached_products:
                if str(cached_products.index(product) + 1) == user_input:
                    selected_product = product

            if selected_product is None:
                error("Invalid product selected. Please try again.", "red")
                main()
            else:
                # Find the account
                account = None
                for acc in get_accounts("twitter"):
                    if acc["id"] == selected_product["twitter_uuid"]:
                        account = acc

                from classes.AFM import AffiliateMarketing

                afm = AffiliateMarketing(selected_product["affiliate_link"], account["firefox_profile"], account["id"], account["nickname"], account["topic"])

                afm.generate_pitch()
                afm.share_pitch("twitter")

    elif user_input == 4:
        info("Starting Outreach...")

        from classes.Outreach import Outreach

        outreach = Outreach()

        outreach.start()
    elif user_input == 5:
        if get_verbose():
            print(colored(" => Quitting...", "blue"))
        sys.exit(0)
    else:
        error("Invalid option selected. Please try again.", "red")
        main()
    

if __name__ == "__main__":
    # Print ASCII Banner
    print_banner()

    first_time = get_first_time_running()

    if first_time:
        print(colored("Hey! It looks like you're running MoneyPrinter V2 for the first time. Let's get you setup first!", "yellow"))

    # Setup file tree
    assert_folder_structure()

    # Remove temporary files
    rem_temp_files()

    bootstrap_runtime()

    while True:
        main()
