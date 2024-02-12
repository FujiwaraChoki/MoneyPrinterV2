import schedule
import subprocess

from art import *
from cache import *
from config import *
from status import *
from uuid import uuid4
from constants import *
from crontab import CronTab
from termcolor import colored
from classes.Twitter import Twitter
from classes.YouTube import YouTube
from prettytable import PrettyTable

def main():
    # Show user options
    info("\n============ OPTIONS ============", False)

    for idx, option in enumerate(OPTIONS):
        print(colored(f" {idx + 1}. {option}", "cyan"))

    info("=================================\n", False)

    # Get user input
    user_input = int(question("Select an option: "))

    # Start the selected option
    if user_input == 1:
        info("Starting Cold Outreach on Local Businesses...")
    elif user_input == 2:
        info("Starting YT Shorts & TikTok Automater...")

        cached_accounts = get_accounts("youtube")
    elif user_input == 3:
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

                add_account({
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

            user_input = question("Select an account to start: ")

            selected_account = None

            for account in cached_accounts:
                if str(cached_accounts.index(account) + 1) == user_input:
                    selected_account = account

            if selected_account is None:
                error("Invalid account selected. Please try again.", "red")
                main()
            else:
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

                        cron_script_path = os.path.join(ROOT_DIR, "src", "cron.py")
                        command = f"python {cron_script_path} twitter {selected_account['id']}"

                        def job():
                            subprocess.run(command)

                        if user_input == 1:
                            # Post Once a day
                            schedule.every(1).day.do(job)
                            success("Set up CRON Job.")
                        elif user_input == 2:
                            # Post twice a day
                            schedule.every().day.at("10:00").do(job)
                            schedule.every().day.at("16:00").do(job)
                            success("Set up CRON Job.")
                        elif user_input == 3:
                            # Post thrice a day
                            schedule.every().day.at("08:00").do(job)
                            schedule.every().day.at("12:00").do(job)
                            schedule.every().day.at("18:00").do(job)
                            success("Set up CRON Job.")
                        else:
                            break

                    elif user_input == 4:
                        if get_verbose():
                            info(" => Climbing Options Ladder...", False)
                        break
    elif user_input == 4:
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

    while True:
        main()
