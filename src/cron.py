# RUN THIS N AMOUNT OF TIMES
import sys

from status import *
from cache import get_accounts
from config import get_ollama_model
from config import get_verbose
from config import get_video_publishing_config
from classes.Tts import TTS
from classes.Twitter import Twitter
from classes.YouTube import YouTube
from llm_provider import select_model
from post_bridge_integration import ensure_post_bridge_publishing_ready
from post_bridge_integration import publish_video

def main():
    """Main function to post content to Twitter or publish generated videos.

    This function determines its operation based on command-line arguments:
    - If the purpose is "twitter", it initializes a Twitter account and posts a message.
    - If the purpose is "publish", it generates a video and publishes it via Post Bridge.

    Command-line arguments:
        sys.argv[1]: A string indicating the purpose, either "twitter" or "publish".
        sys.argv[2]: Twitter account UUID for twitter mode, or optional model name for publish mode.

    The function also handles verbose output based on user settings and reports success or errors as appropriate.

    Args:
        None. The function uses command-line arguments accessed via sys.argv.

    Returns:
        None. The function performs operations based on the purpose and account UUID and does not return any value."""
    if len(sys.argv) < 2:
        error("No cron purpose provided.")
        sys.exit(1)

    purpose = str(sys.argv[1])
    account_id = str(sys.argv[2]) if len(sys.argv) > 2 else ""
    configured_model = get_ollama_model()

    if purpose == "twitter":
        model = str(sys.argv[3]) if len(sys.argv) > 3 else configured_model
    else:
        model = str(sys.argv[2]) if len(sys.argv) > 2 else configured_model

    if model:
        select_model(model)
    else:
        error("No Ollama model specified. Set ollama_model or pass it as a cron argument.")
        sys.exit(1)

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
    elif purpose == "publish":
        if not ensure_post_bridge_publishing_ready(interactive=False):
            error(
                "Video publishing is not configured. Run the interactive Post Bridge "
                "setup wizard from src/main.py first."
            )
            sys.exit(1)

        tts = TTS()
        video_config = get_video_publishing_config()

        if verbose:
            info("Initializing Video Publishing...")

        video_generator = YouTube(
            "post-bridge-publisher",
            video_config["profile_name"],
            "",
            video_config["niche"],
            video_config["language"],
        )
        video_generator.generate_video(tts)
        publish_success = publish_video(
            video_path=video_generator.video_path,
            title=video_generator.metadata.get("title", ""),
            description=video_generator.metadata.get("description", ""),
            interactive=False,
        )
        if publish_success and verbose:
            success("Published video.")
    elif purpose == "youtube":
        error(
            "The 'youtube' cron mode has been removed. Use 'publish' instead."
        )
        sys.exit(1)
    else:
        error("Invalid Purpose, exiting...")
        sys.exit(1)

if __name__ == "__main__":
    main()
