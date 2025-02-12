import schedule
import subprocess

from art import *
from cache import *
from utils import *
from config import *
from status import *
from uuid import uuid4
from constants import *
from classes.Tts import TTS
from termcolor import colored
from classes.Twitter import Twitter
from classes.YouTube import YouTube
from prettytable import PrettyTable
from classes.Outreach import Outreach
from classes.AFM import AffiliateMarketing

def main():

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
                
                # Add image generation options
                info("\n============ IMAGE GENERATION ============", False)
                print(colored(" 1. Cloudflare Worker", "cyan"))
                print(colored(" 2. G4F (SDXL Turbo)", "cyan"))
                info("=======================================\n", False)
                
                image_gen_choice = question(" => Select image generation method (1/2): ")
                
                account_data = {
                    "id": generated_uuid,
                    "nickname": nickname,
                    "firefox_profile": fp_profile,
                    "niche": niche,
                    "language": language,
                    "use_g4f": image_gen_choice == "2",
                    "videos": []
                }
                
                if image_gen_choice == "1":
                    worker_url = question(" => Enter your Cloudflare worker URL for image generation: ")
                    account_data["worker_url"] = worker_url

                add_account("youtube", account_data)

                success("Account configured successfully!")
        else:
            table = PrettyTable()
            table.field_names = ["ID", "UUID", "Nickname", "Niche"]

            for account in cached_accounts:
                table.add_row([cached_accounts.index(account) + 1, colored(account["id"], "cyan"), colored(account["nickname"], "blue"), colored(account["niche"], "green")])

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
                    tts = TTS()

                    if user_input == 1:
                        youtube.generate_video(tts)
                        upload_to_yt = question("Do you want to upload this video to YouTube? (Yes/No): ")
                        if upload_to_yt.lower() == "yes":
                            youtube.upload_video()
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

                        cron_script_path = os.path.join(ROOT_DIR, "src", "cron.py")
                        command = f"python {cron_script_path} youtube {selected_account['id']}"

                        def job():
                            subprocess.run(command)

                        if user_input == 1:
                            # Upload Once
                            schedule.every(1).day.do(job)
                            success("Set up CRON Job.")
                        elif user_input == 2:
                            # Upload Twice a day
                            schedule.every().day.at("10:00").do(job)
                            schedule.every().day.at("16:00").do(job)
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

                        twitter_cron_choice = int(question("Select an Option: "))

                        if twitter_cron_choice == 5:
                            break

                        cron_script_path = os.path.join(ROOT_DIR, "src", "cron.py")
                        command = f"python {cron_script_path} twitter {selected_account['id']}"

                        def job():
                            subprocess.run(command)

                        if twitter_cron_choice == 1:
                            # Post Once a day
                            schedule.every(1).day.do(job)
                            success("Set up CRON Job for posting once a day.")
                        elif twitter_cron_choice == 2:
                            # Post Twice a day (for example, 10:00 and 16:00)
                            schedule.every().day.at("10:00").do(job)
                            schedule.every().day.at("16:00").do(job)
                            success("Set up CRON Job for posting twice a day.")
                        elif twitter_cron_choice == 3:
                            # Post Thrice a day (for example, 08:00, 12:00, and 18:00)
                            schedule.every().day.at("08:00").do(job)
                            schedule.every().day.at("12:00").do(job)
                            schedule.every().day.at("18:00").do(job)
                            success("Set up CRON Job for posting thrice a day.")
                        elif twitter_cron_choice == 4:
                            custom_tweets = int(question("Enter number of tweets per day (1-30): "))
                            if custom_tweets < 1 or custom_tweets > 30:
                                error("Invalid number of tweets. Choose a value between 1 and 30.", "red")
                            else:
                                from datetime import datetime, timedelta
                                # Define allowed posting window: 05:00 to 23:00
                                window_start = datetime.strptime("05:00", "%H:%M")
                                window_end = datetime.strptime("23:00", "%H:%M")
                                total_minutes = (window_end - window_start).seconds // 60  # 1080 minutes
                                scheduled_times = []
                                if custom_tweets == 1:
                                    tweet_time = window_start.strftime("%H:%M")
                                    schedule.every().day.at(tweet_time).do(job)
                                    scheduled_times.append(tweet_time)
                                else:
                                    # Divide the window into (custom_tweets - 1) intervals
                                    interval = total_minutes / (custom_tweets - 1)
                                    for i in range(custom_tweets):
                                        tweet_time_dt = window_start + timedelta(minutes=i * interval)
                                        tweet_time = tweet_time_dt.strftime("%H:%M")
                                        scheduled_times.append(tweet_time)
                                        schedule.every().day.at(tweet_time).do(job)
                                success(f"Set up CRON Job for {custom_tweets} tweets a day at times: {', '.join(scheduled_times)}")
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

                afm = AffiliateMarketing(selected_product["affiliate_link"], account["firefox_profile"], account["id"], account["nickname"], account["topic"])

                afm.generate_pitch()
                afm.share_pitch("twitter")

    elif user_input == 4:
        info("Starting Outreach...")

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

    # Fetch MP3 Files
    fetch_songs()

    while True:
        main()
