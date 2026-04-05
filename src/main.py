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
WEEKDAY_LABELS = {
    0: "Sun",
    1: "Mon",
    2: "Tue",
    3: "Wed",
    4: "Thu",
    5: "Fri",
    6: "Sat",
}

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
    frequency_option: int | list[str],
    model: str | None = None,
) -> str:
    if isinstance(frequency_option, list):
        schedules = [str(schedule).strip() for schedule in frequency_option if str(schedule).strip()]
    else:
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
    frequency_option: int | list[str],
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


def build_custom_cron_schedules(days_of_week: list[int], times: list[str]) -> list[str]:
    day_values = sorted({int(day) for day in days_of_week})
    if not day_values:
        raise ValueError("At least one weekday must be selected.")

    parsed_times = []
    for time_value in times:
        raw_time = str(time_value).strip()
        if not raw_time:
            continue

        time_parts = raw_time.split(":")
        if len(time_parts) != 2:
            raise ValueError(f"Invalid time format: {raw_time}")

        hour = int(time_parts[0])
        minute = int(time_parts[1])
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            raise ValueError(f"Invalid time value: {raw_time}")

        parsed_times.append((hour, minute))

    if not parsed_times:
        raise ValueError("At least one valid time must be provided.")

    day_expression = "*" if day_values == list(WEEKDAY_LABELS.keys()) else ",".join(
        str(day) for day in day_values
    )
    return [f"{minute} {hour} * * {day_expression}" for hour, minute in parsed_times]


def prompt_for_cron_schedules() -> list[str] | None:
    info("Choose schedule days:")
    info(" 1. Every day", False)
    info(" 2. Weekdays (Mon-Fri)", False)
    info(" 3. Custom weekdays", False)
    info(" 4. Cancel", False)

    day_mode = question("Choose schedule days (1-4): ").strip()
    if day_mode == "4":
        return None

    if day_mode == "1":
        selected_days = [0, 1, 2, 3, 4, 5, 6]
    elif day_mode == "2":
        selected_days = [1, 2, 3, 4, 5]
    elif day_mode == "3":
        info(" Weekday numbers: 0=Sun, 1=Mon, 2=Tue, 3=Wed, 4=Thu, 5=Fri, 6=Sat", False)
        weekday_input = question("Enter weekdays as comma-separated numbers: ").strip()
        try:
            selected_days = sorted(
                {
                    int(part.strip())
                    for part in weekday_input.split(",")
                    if part.strip() != ""
                }
            )
        except ValueError as exc:
            raise ValueError("Weekdays must be numbers between 0 and 6.") from exc

        if not selected_days or any(day < 0 or day > 6 for day in selected_days):
            raise ValueError("Weekdays must be numbers between 0 and 6.")
    else:
        raise ValueError("Invalid schedule day selection.")

    time_input = question("Enter time(s) in HH:MM 24-hour format, comma-separated: ").strip()
    time_values = [part.strip() for part in time_input.split(",") if part.strip()]
    schedules = build_custom_cron_schedules(selected_days, time_values)

    readable_days = "Every day" if selected_days == [0, 1, 2, 3, 4, 5, 6] else ", ".join(
        WEEKDAY_LABELS[day] for day in selected_days
    )
    info(f"Configured schedule for {readable_days}: {', '.join(time_values)}")
    return schedules


def has_successful_cached_crossposts(video: dict | None) -> bool:
    if not isinstance(video, dict):
        return False

    crossposts = video.get("crossposts") or {}
    for details in crossposts.values():
        if isinstance(details, dict) and details.get("status") == "success":
            return True

    return False


def get_successful_cached_platforms(video: dict | None) -> list[str]:
    if not isinstance(video, dict):
        return []

    successful_platforms = []
    if video.get("uploaded"):
        successful_platforms.append("youtube")

    crossposts = video.get("crossposts") or {}
    for platform in sorted(crossposts):
        details = crossposts.get(platform)
        if isinstance(details, dict) and details.get("status") == "success":
            normalized_platform = str(platform).strip().lower()
            if normalized_platform and normalized_platform not in successful_platforms:
                successful_platforms.append(normalized_platform)

    return successful_platforms


def find_cached_video_by_path(videos: list[dict], video_path: str | None) -> dict | None:
    if not video_path:
        return None

    if not isinstance(videos, list):
        return None

    for video in videos:
        if video.get("path") == video_path:
            return video

    return None


def is_post_bridge_primary_youtube_enabled() -> bool:
    post_bridge_config = get_post_bridge_config()
    return bool(
        post_bridge_config.get("enabled")
        and post_bridge_config.get("api_key")
        and "youtube" in list(post_bridge_config.get("platforms") or [])
    )


def maybe_upload_youtube_video(
    youtube,
    cached_video: dict | None = None,
    require_confirmation: bool = True,
) -> bool:
    use_post_bridge_for_youtube = is_post_bridge_primary_youtube_enabled()

    if require_confirmation:
        if use_post_bridge_for_youtube:
            upload_to_yt = question(
                "Do you want to publish this video to all configured platforms? (Yes/No): "
            )
        else:
            upload_to_yt = question("Do you want to upload this video to YouTube? (Yes/No): ")
        if not is_affirmative_response(upload_to_yt):
            return False

    if use_post_bridge_for_youtube:
        excluded_platforms = get_successful_cached_platforms(cached_video)
        publish_kwargs = {
            "video_path": youtube.video_path,
            "title": youtube.metadata.get("title", ""),
            "description": youtube.metadata.get("description", ""),
            "interactive": True,
            "return_details": True,
            "include_youtube": True,
            "skip_confirmation": True,
        }
        if excluded_platforms:
            publish_kwargs["excluded_platforms"] = excluded_platforms

        publish_result = maybe_crosspost_youtube_short(
            **publish_kwargs,
        )
        if isinstance(publish_result, dict) and publish_result.get("posted"):
            published_platforms = set((publish_result.get("platforms") or {}).keys())
            if cached_video is not None and "youtube" not in published_platforms:
                youtube.record_crosspost_result(cached_video, publish_result)
            else:
                youtube.record_post_bridge_publish_result(publish_result)
            return True

        if isinstance(publish_result, dict) and publish_result.get("skipped"):
            return True

        warning("Post Bridge YouTube publish failed.")
        return False

    current_cached_video = cached_video
    if current_cached_video is None:
        current_cached_video = find_cached_video_by_path(
            youtube.get_videos(),
            getattr(youtube, "video_path", None),
        )

    if current_cached_video and current_cached_video.get("uploaded"):
        crosspost_kwargs = {
            "video_path": youtube.video_path,
            "title": youtube.metadata.get("title", ""),
            "interactive": True,
            "return_details": True,
        }
        description_value = youtube.metadata.get("description", "")
        if description_value:
            crosspost_kwargs["description"] = description_value

        excluded_platforms = get_successful_cached_platforms(current_cached_video)
        if excluded_platforms:
            crosspost_kwargs["excluded_platforms"] = excluded_platforms

        crosspost_result = maybe_crosspost_youtube_short(**crosspost_kwargs)
        if isinstance(crosspost_result, dict):
            if crosspost_result.get("posted"):
                youtube.record_crosspost_result(current_cached_video, crosspost_result)
                return True
            if crosspost_result.get("skipped"):
                return True
            return False

        return bool(crosspost_result)

    while True:
        upload_success = youtube.upload_video()
        if upload_success:
            if has_successful_cached_crossposts(current_cached_video):
                info(
                    "This Short already has successful Post Bridge cross-posts. Skipping automatic cross-post."
                )
                return True

            crosspost_kwargs = {
                "video_path": youtube.video_path,
                "title": youtube.metadata.get("title", ""),
                "interactive": True,
                "return_details": True,
            }
            description_value = youtube.metadata.get("description", "")
            if description_value:
                crosspost_kwargs["description"] = description_value

            crosspost_result = maybe_crosspost_youtube_short(**crosspost_kwargs)
            if isinstance(crosspost_result, dict):
                youtube.record_crosspost_result(
                    {
                        "path": youtube.video_path,
                        "url": getattr(youtube, "uploaded_video_url", None),
                    },
                    crosspost_result,
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
        if not is_affirmative_response(retry_upload):
            warning("YouTube upload failed. Skipping Post Bridge cross-post.")
            return False


def is_affirmative_response(response: str) -> bool:
    normalized_response = str(response or "").strip().lower()
    return normalized_response in {"y", "yes"}


def resolve_cached_short_selection(
    initial_response: str,
    followup_prompt: str,
    invalid_message: str,
) -> int | None:
    normalized_response = str(initial_response or "").strip()

    if normalized_response.isdigit():
        return int(normalized_response) - 1

    if not is_affirmative_response(normalized_response):
        return None

    selected_video_input = question(followup_prompt).strip()

    try:
        return int(selected_video_input) - 1
    except ValueError:
        warning(invalid_message)
        return None


def maybe_retry_selected_youtube_short(youtube, videos: list[dict]) -> bool:
    retry_existing = question(
        "Retry upload for one of these Shorts? (Yes/No): "
    )
    selected_index = resolve_cached_short_selection(
        initial_response=retry_existing,
        followup_prompt="Enter the short number to retry upload: ",
        invalid_message="Invalid Short selection. Skipping upload retry.",
    )
    if selected_index is None:
        return False

    if selected_index < 0 or selected_index >= len(videos):
        warning("Invalid Short selection. Skipping upload retry.")
        return False

    selected_video = videos[selected_index]
    video_path = selected_video.get("path")

    if not video_path or not os.path.exists(video_path):
        warning("The selected Short file no longer exists on disk. Skipping upload retry.")
        return False

    show_cached_short_preview(selected_video)
    youtube.load_cached_video(selected_video)
    return maybe_upload_youtube_video(youtube, cached_video=selected_video)


def maybe_publish_selected_youtube_short(youtube, videos: list[dict]) -> bool:
    publish_existing = question(
        "Publish one of these Shorts to all configured platforms? (Yes/No): "
    )
    selected_index = resolve_cached_short_selection(
        initial_response=publish_existing,
        followup_prompt="Enter the short number to publish: ",
        invalid_message="Invalid Short selection. Skipping publish.",
    )
    if selected_index is None:
        return False

    if selected_index < 0 or selected_index >= len(videos):
        warning("Invalid Short selection. Skipping publish.")
        return False

    selected_video = videos[selected_index]
    video_path = selected_video.get("path")

    if not video_path or not os.path.exists(video_path):
        warning("The selected Short file no longer exists on disk. Skipping publish.")
        return False

    show_cached_short_preview(selected_video)
    youtube.load_cached_video(selected_video)
    return maybe_upload_youtube_video(
        youtube,
        cached_video=selected_video,
        require_confirmation=False,
    )


def get_cached_short_crosspost_status(video: dict) -> str:
    crossposts = video.get("crossposts") or {}
    successful_platforms = []
    for platform, details in crossposts.items():
        if isinstance(details, dict) and details.get("status") == "success":
            successful_platforms.append(platform)

    if not successful_platforms:
        return "-"

    return ", ".join(platform.title() for platform in sorted(successful_platforms))


def show_cached_short_preview(video: dict) -> None:
    title = str(video.get("title", "") or "").strip() or "Untitled"
    description = str(video.get("description", "") or "").strip()
    if not description:
        description = str(video.get("script", "") or "").strip()

    info(f"Selected Short title: {title}")
    if description:
        preview_description = description[:140]
        if len(description) > 140:
            preview_description += "..."
        info(f"Selected Short description: {preview_description}")


def maybe_crosspost_selected_youtube_short(youtube, videos: list[dict]) -> bool:
    should_crosspost = question(
        "Do you want to cross-post one of these Shorts via Post Bridge? (Yes/No): "
    )
    selected_index = resolve_cached_short_selection(
        initial_response=should_crosspost,
        followup_prompt="Enter the short number to cross-post: ",
        invalid_message="Invalid Short selection. Skipping cross-post.",
    )
    if selected_index is None:
        return False

    if selected_index < 0 or selected_index >= len(videos):
        warning("Invalid Short selection. Skipping cross-post.")
        return False

    selected_video = videos[selected_index]
    video_path = selected_video.get("path")

    if not video_path or not os.path.exists(video_path):
        warning("The selected Short file no longer exists on disk. Skipping cross-post.")
        return False

    show_cached_short_preview(selected_video)
    crosspost_kwargs = {
        "video_path": video_path,
        "title": selected_video.get("title", ""),
        "interactive": True,
        "return_details": True,
    }
    excluded_platforms = get_successful_cached_platforms(selected_video)
    if excluded_platforms:
        crosspost_kwargs["excluded_platforms"] = excluded_platforms

    crosspost_result = maybe_crosspost_youtube_short(**crosspost_kwargs)

    if isinstance(crosspost_result, dict):
        youtube.record_crosspost_result(selected_video, crosspost_result)
        return bool(crosspost_result.get("posted"))

    return bool(crosspost_result)


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
                            videos_table.field_names = ["ID", "Date", "Title", "YouTube", "Cross-posts"]

                            for video in videos:
                                videos_table.add_row([
                                    videos.index(video) + 1,
                                    colored(video["date"], "blue"),
                                    colored(video["title"][:60] + "...", "green"),
                                    colored("Yes" if video.get("uploaded") else "No", "cyan"),
                                    colored(get_cached_short_crosspost_status(video), "magenta"),
                                ])

                            print(videos_table)
                            maybe_publish_selected_youtube_short(youtube, videos)
                        else:
                            warning(" No videos found.")
                    elif user_input == 3:
                        try:
                            schedules = prompt_for_cron_schedules()
                        except ValueError as exc:
                            warning(str(exc))
                            continue

                        if schedules is None:
                            continue

                        install_cron_job("youtube", selected_account["id"], schedules)
                        success("Set up CRON Job.")
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
                        try:
                            schedules = prompt_for_cron_schedules()
                        except ValueError as exc:
                            warning(str(exc))
                            continue

                        if schedules is None:
                            continue

                        install_cron_job("twitter", selected_account["id"], schedules)
                        success("Set up CRON Job.")
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
