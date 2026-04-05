# RUN THIS N AMOUNT OF TIMES
import sys

from status import *
from cache import get_accounts
from config import get_openrouter_api_key, get_openrouter_model, get_post_bridge_config, get_verbose
from classes.Tts import TTS
from classes.Twitter import Twitter
from classes.YouTube import YouTube
from llm_provider import select_model
from post_bridge_integration import maybe_crosspost_youtube_short

def main():
    """Main function to post content to Twitter or upload videos to YouTube.

    This function determines its operation based on command-line arguments:
    - If the purpose is "twitter", it initializes a Twitter account and posts a message.
    - If the purpose is "youtube", it initializes a YouTube account, generates a video with TTS, and uploads it.

    Command-line arguments:
        sys.argv[1]: A string indicating the purpose, either "twitter" or "youtube".
        sys.argv[2]: A string representing the account UUID.

    The function also handles verbose output based on user settings and reports success or errors as appropriate.

    Args:
        None. The function uses command-line arguments accessed via sys.argv.

    Returns:
        None. The function performs operations based on the purpose and account UUID and does not return any value."""
    purpose = str(sys.argv[1])
    account_id = str(sys.argv[2])
    model = str(sys.argv[3]) if len(sys.argv) > 3 else get_openrouter_model()

    if not get_openrouter_api_key():
        error("No OpenRouter API key configured. Set openrouter_api_key or OPENROUTER_API_KEY.")
        sys.exit(1)
    if not model:
        error("No OpenRouter model configured. Set openrouter_model or OPENROUTER_MODEL.")
        sys.exit(1)
    select_model(model)

    verbose = get_verbose()

    if purpose == "twitter":
        accounts = get_accounts("twitter")

        if not account_id:
            error("Account UUID cannot be empty.")

        for acc in accounts:
            if acc["id"] == account_id:
                if verbose:
                    info("Initializing Twitter...")
                twitter = Twitter(
                    acc["id"],
                    acc["nickname"],
                    acc["firefox_profile"],
                    acc["topic"]
                )
                twitter.post()
                if verbose:
                    success("Done posting.")
                break
    elif purpose == "youtube":
        tts = TTS()

        accounts = get_accounts("youtube")

        if not account_id:
            error("Account UUID cannot be empty.")

        for acc in accounts:
            if acc["id"] == account_id:
                if verbose:
                    info("Initializing YouTube...")
                youtube = YouTube(
                    acc["id"],
                    acc["nickname"],
                    acc["firefox_profile"],
                    acc["niche"],
                    acc["language"]
                )
                youtube.generate_video(tts)
                post_bridge_config = get_post_bridge_config()
                use_post_bridge_for_youtube = (
                    post_bridge_config.get("enabled")
                    and post_bridge_config.get("api_key")
                    and "youtube" in list(post_bridge_config.get("platforms") or [])
                )

                if use_post_bridge_for_youtube:
                    publish_result = maybe_crosspost_youtube_short(
                        video_path=youtube.video_path,
                        title=youtube.metadata.get("title", ""),
                        description=youtube.metadata.get("description", ""),
                        interactive=False,
                        return_details=True,
                        include_youtube=True,
                        skip_confirmation=True,
                    )
                    if isinstance(publish_result, dict) and publish_result.get("posted"):
                        youtube.record_post_bridge_publish_result(publish_result)
                        if verbose:
                            success("Uploaded Short.")
                    else:
                        warning("Post Bridge YouTube publish failed.")
                else:
                    upload_success = youtube.upload_video()
                    if upload_success:
                        if verbose:
                            success("Uploaded Short.")
                        crosspost_kwargs = {
                            "video_path": youtube.video_path,
                            "title": youtube.metadata.get("title", ""),
                            "interactive": False,
                        }
                        description_value = youtube.metadata.get("description", "")
                        if description_value:
                            crosspost_kwargs["description"] = description_value

                        maybe_crosspost_youtube_short(**crosspost_kwargs)
                    else:
                        warning("YouTube upload failed. Skipping Post Bridge cross-post.")
                break
    else:
        error("Invalid Purpose, exiting...")
        sys.exit(1)

if __name__ == "__main__":
    main()
