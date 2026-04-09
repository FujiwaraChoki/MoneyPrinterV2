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
from llm_provider import list_models, select_model, get_active_model
from post_bridge_integration import maybe_crosspost_youtube_short


# ------------------------------------------------------------------
# Quick Generate — one-prompt video creation
# ------------------------------------------------------------------

def _pick_number(prompt_text: str, max_val: int, default: int = 1) -> int:
    """Helper to pick a number from 1..max_val with a default."""
    while True:
        raw = input(colored(f"{prompt_text} [{default}]: ", "magenta")).strip()
        if raw == "":
            return default
        try:
            val = int(raw)
            if 1 <= val <= max_val:
                return val
            warning(f"Please enter a number between 1 and {max_val}.")
        except ValueError:
            warning("Please enter a valid number.")


def quick_generate():
    """Interactive one-prompt video generation flow.

    Guides the user through:
    1. Entering a video topic/prompt
    2. Picking a language
    3. Picking a TTS provider and voice
    4. Picking a subtitle style
    5. Generating the complete video
    """
    info("\n=========== QUICK GENERATE ===========", False)
    info("  One prompt -> complete video", False)
    info("======================================\n", False)

    # --- 1. Prompt ---
    topic = ""
    while not topic.strip():
        topic = input(colored("  Describe your video: ", "magenta")).strip()
        if not topic:
            warning("Please enter a topic or idea.")

    # --- 2. Language ---
    info("\n  Language:", False)
    for idx, (lang_name, _code) in enumerate(LANGUAGES):
        print(colored(f"   {idx + 1}. {lang_name}", "cyan"))
    print(colored(f"   {len(LANGUAGES) + 1}. Other (type it)", "cyan"))

    lang_choice = _pick_number("  Select language", len(LANGUAGES) + 1, default=1)
    if lang_choice <= len(LANGUAGES):
        language_name, language_code = LANGUAGES[lang_choice - 1]
    else:
        language_name = input(colored("  Enter language name: ", "magenta")).strip() or "English"
        language_code = input(colored("  Enter language code (e.g. en, es): ", "magenta")).strip() or "en"

    # --- 3. TTS Provider ---
    info("\n  TTS Provider:", False)
    print(colored("   1. Edge TTS  (300+ voices, free, high quality)", "cyan"))
    print(colored("   2. Kitten TTS (8 voices, local, English only)", "cyan"))
    tts_provider_choice = _pick_number("  Select TTS provider", 2, default=1)
    tts_provider = "edge_tts" if tts_provider_choice == 1 else "kitten_tts"

    # --- 4. Voice ---
    info(f"\n  Loading voices for {language_name}...", False)
    voices = TTS.list_voices(provider=tts_provider, language_filter=language_code)

    if not voices:
        warning(f"  No voices found for '{language_code}'. Showing all voices...")
        voices = TTS.list_voices(provider=tts_provider)

    if not voices:
        error("  No voices available for this provider.")
        return

    # Show paginated voice list (max 20)
    display_voices = voices[:20]
    info(f"\n  Available voices ({len(voices)} total, showing top {len(display_voices)}):", False)
    for idx, v in enumerate(display_voices):
        gender_tag = v.get("gender", "")[:1]  # M or F
        label = f"{v['name']} ({gender_tag})"
        print(colored(f"   {idx + 1}. {label}", "cyan"))

    if len(voices) > 20:
        print(colored(f"   ... and {len(voices) - 20} more. Type a voice name directly to search.", "yellow"))

    voice_input = input(colored(f"  Select voice [1]: ", "magenta")).strip()
    selected_voice = display_voices[0]["name"]  # default

    if voice_input:
        try:
            voice_idx = int(voice_input) - 1
            if 0 <= voice_idx < len(display_voices):
                selected_voice = display_voices[voice_idx]["name"]
        except ValueError:
            # User typed a voice name — search for it
            matches = [v for v in voices if voice_input.lower() in v["name"].lower()]
            if matches:
                selected_voice = matches[0]["name"]
                info(f"  Matched: {selected_voice}")
            else:
                warning(f"  Voice '{voice_input}' not found. Using default.")

    # --- 5. Subtitle Style ---
    info("\n  Subtitle Style:", False)
    for idx, (_, display_name) in enumerate(SUBTITLE_STYLE_OPTIONS):
        print(colored(f"   {idx + 1}. {display_name}", "cyan"))
    style_choice = _pick_number("  Select style", len(SUBTITLE_STYLE_OPTIONS), default=1)
    subtitle_style = SUBTITLE_STYLE_OPTIONS[style_choice - 1][0]

    # --- Summary ---
    info("\n  ---- Configuration ----", False)
    info(f"  Topic     : {topic}", False)
    info(f"  Language  : {language_name}", False)
    info(f"  TTS       : {tts_provider} / {selected_voice}", False)
    info(f"  Subtitles : {SUBTITLE_STYLE_OPTIONS[style_choice - 1][1]}", False)
    info("  ----------------------\n", False)

    confirm = input(colored("  Start generating? (Y/n): ", "magenta")).strip().lower()
    if confirm == "n":
        info("  Cancelled.")
        return

    # --- Generate ---
    info("\n  Generating video...\n")

    # Temporarily override subtitle style for this generation
    import config as _cfg
    _original_get_subtitle_style = _cfg.get_subtitle_style
    _cfg.get_subtitle_style = lambda: subtitle_style

    try:
        tts = TTS(provider=tts_provider, voice=selected_voice)
        youtube = YouTube.for_generation(niche=topic, language=language_name)

        # Step 1: Topic
        youtube.generate_topic()
        success(f"  Topic: {youtube.subject[:80]}")

        # Step 2: Script
        youtube.generate_script()
        success(f"  Script generated ({len(youtube.script)} chars)")

        # Step 3: Metadata
        youtube.generate_metadata()
        success(f"  Title: {youtube.metadata['title'][:60]}")

        # Step 4: Image prompts
        youtube.generate_prompts()
        success(f"  {len(youtube.image_prompts)} image prompts generated")

        # Step 5: Images
        for i, prompt in enumerate(youtube.image_prompts):
            youtube.generate_image(prompt)
            success(f"  Image {i + 1}/{len(youtube.image_prompts)} generated")

        # Step 6: TTS
        youtube.generate_script_to_speech(tts)
        success(f"  Audio generated ({tts_provider}: {selected_voice})")

        # Step 7: Combine
        path = youtube.combine()
        youtube.video_path = os.path.abspath(path)

        info("")
        success(f"  Video saved: {youtube.video_path}")
        info("")

        # Optionally upload
        upload = input(colored("  Upload to YouTube? (y/N): ", "magenta")).strip().lower()
        if upload == "y":
            cached_accounts = get_accounts("youtube")
            if not cached_accounts:
                warning("  No YouTube accounts configured. Use 'YouTube Shorts Automation' to add one first.")
            else:
                info("\n  Select YouTube account:", False)
                for idx, acc in enumerate(cached_accounts):
                    print(colored(f"   {idx + 1}. {acc['nickname']} ({acc['niche']})", "cyan"))
                acc_choice = _pick_number("  Account", len(cached_accounts), default=1)
                acc = cached_accounts[acc_choice - 1]

                # Create a full YouTube instance with browser for upload
                yt_upload = YouTube(
                    acc["id"], acc["nickname"], acc["firefox_profile"],
                    acc["niche"], acc["language"]
                )
                yt_upload.video_path = youtube.video_path
                yt_upload.metadata = youtube.metadata
                yt_upload.channel_id = None

                upload_success = yt_upload.upload_video()
                if upload_success:
                    success("  Uploaded to YouTube!")
                    maybe_crosspost_youtube_short(
                        video_path=youtube.video_path,
                        title=youtube.metadata.get("title", ""),
                        interactive=True,
                    )
                else:
                    warning("  Upload failed.")
    finally:
        _cfg.get_subtitle_style = _original_get_subtitle_style


# ------------------------------------------------------------------
# Main menu
# ------------------------------------------------------------------

def main():
    """Main entry point providing a menu-driven interface."""

    valid_input = False
    while not valid_input:
        try:
            info("\n========== MONEYPRINTER V2 ==========", False)

            for idx, option in enumerate(OPTIONS):
                print(colored(f"  {idx + 1}. {option}", "cyan"))

            info("=====================================\n", False)
            user_input = input(colored("  Select an option: ", "magenta")).strip()
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
        quick_generate()
    elif user_input == 2:
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
                            upload_success = youtube.upload_video()
                            if upload_success:
                                maybe_crosspost_youtube_short(
                                    video_path=youtube.video_path,
                                    title=youtube.metadata.get("title", ""),
                                    interactive=True,
                                )
                            else:
                                warning("YouTube upload failed. Skipping Post Bridge cross-post.")
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
                        command = ["python", cron_script_path, "youtube", selected_account['id'], get_active_model()]

                        def job():
                            result = subprocess.run(command)
                            if result.returncode != 0:
                                warning(f"CRON job exited with code {result.returncode}")

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
                        command = ["python", cron_script_path, "twitter", selected_account['id'], get_active_model()]

                        def job():
                            result = subprocess.run(command)
                            if result.returncode != 0:
                                warning(f"CRON job exited with code {result.returncode}")

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

    elif user_input == 5:
        info("Starting Outreach...")

        outreach = Outreach()

        outreach.start()
    elif user_input == 6:
        if get_verbose():
            info(" => Quitting...")
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

    # Select Ollama model — use config value if set, otherwise pick interactively
    configured_model = get_ollama_model()
    if configured_model:
        select_model(configured_model)
        success(f"Using configured model: {configured_model}")
    else:
        try:
            models = list_models()
        except Exception as e:
            error(f"Could not connect to Ollama: {e}")
            sys.exit(1)

        if not models:
            error("No models found on Ollama. Pull a model first (e.g. 'ollama pull llama3.2:3b').")
            sys.exit(1)

        info("\n========== OLLAMA MODELS =========", False)
        for idx, model_name in enumerate(models):
            print(colored(f" {idx + 1}. {model_name}", "cyan"))
        info("==================================\n", False)

        model_choice = None
        while model_choice is None:
            raw = input(colored("Select a model: ", "magenta")).strip()
            try:
                choice_idx = int(raw) - 1
                if 0 <= choice_idx < len(models):
                    model_choice = models[choice_idx]
                else:
                    warning("Invalid selection. Try again.")
            except ValueError:
                warning("Please enter a number.")

        select_model(model_choice)
        success(f"Using model: {model_choice}")

    while True:
        main()
