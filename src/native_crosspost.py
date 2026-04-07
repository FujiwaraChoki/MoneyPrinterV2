"""
Native cross-posting to Instagram and TikTok using their official APIs.

This module provides a free alternative to Post Bridge by calling the
Instagram Graph API and TikTok Content Posting API directly.

Instagram requires:
  - A Business/Creator Instagram account linked to a Facebook Page
  - A long-lived access token with ``instagram_content_publish``
  - Video files hosted at a publicly accessible URL

TikTok requires:
  - A registered developer app with ``video.publish`` scope
  - A valid user access token
  - Passing the TikTok app audit for public visibility (until then: SELF_ONLY)
"""

import os
from typing import Callable, Optional

from config import get_instagram_config, get_tiktok_config
from status import info, success, warning, question


def maybe_crosspost_instagram(
    video_path: str,
    video_public_url: str,
    caption: str,
    interactive: bool,
    prompt_fn: Optional[Callable[[str], str]] = None,
) -> Optional[bool]:
    """
    Cross-post a video as an Instagram Reel using the native Graph API.

    Args:
        video_path (str): Local path to the video (used for existence check).
        video_public_url (str): Publicly accessible URL where Meta can fetch the video.
        caption (str): Post caption.
        interactive (bool): Whether to prompt the user for confirmation.
        prompt_fn (Callable | None): Optional prompt override for testing.

    Returns:
        result (bool | None): True on success, False on failure, None if skipped.
    """
    config = get_instagram_config()

    if not config["enabled"]:
        return None

    if not config["access_token"] or not config["account_id"]:
        warning(
            "Instagram is enabled but access_token or account_id is missing. "
            "Set them in config.json or via environment variables."
        )
        return None

    if not os.path.exists(video_path):
        warning(f"Cannot cross-post to Instagram: video not found at {video_path}")
        return False

    if prompt_fn is None:
        prompt_fn = question

    should_post = config["auto_crosspost"]
    if interactive and not should_post:
        response = prompt_fn(
            "Cross-post this video to Instagram as a Reel? (Yes/No): "
        ).strip().lower()
        should_post = response in {"y", "yes"}
    elif not interactive and not config["auto_crosspost"]:
        info(
            "Instagram is enabled but auto_crosspost is off. "
            "Skipping in non-interactive mode."
        )
        return None

    if not should_post:
        return None

    try:
        from classes.Instagram import Instagram, InstagramClientError

        client = Instagram()
        client.post_reel(video_public_url, caption)
        return True
    except Exception as exc:
        warning(f"Instagram cross-post failed: {exc}")
        return False


def maybe_crosspost_tiktok(
    video_path: str,
    title: str,
    interactive: bool,
    prompt_fn: Optional[Callable[[str], str]] = None,
) -> Optional[bool]:
    """
    Cross-post a video to TikTok using the native Content Posting API.

    Args:
        video_path (str): Local path to the MP4 video file.
        title (str): Video title (max 150 chars).
        interactive (bool): Whether to prompt the user for confirmation.
        prompt_fn (Callable | None): Optional prompt override for testing.

    Returns:
        result (bool | None): True on success, False on failure, None if skipped.
    """
    config = get_tiktok_config()

    if not config["enabled"]:
        return None

    if not config["access_token"]:
        warning(
            "TikTok is enabled but access_token is missing. "
            "Set it in config.json or via TIKTOK_ACCESS_TOKEN env var."
        )
        return None

    if not os.path.exists(video_path):
        warning(f"Cannot cross-post to TikTok: video not found at {video_path}")
        return False

    if prompt_fn is None:
        prompt_fn = question

    should_post = config["auto_crosspost"]
    if interactive and not should_post:
        response = prompt_fn(
            "Cross-post this video to TikTok? (Yes/No): "
        ).strip().lower()
        should_post = response in {"y", "yes"}
    elif not interactive and not config["auto_crosspost"]:
        info(
            "TikTok is enabled but auto_crosspost is off. "
            "Skipping in non-interactive mode."
        )
        return None

    if not should_post:
        return None

    try:
        from classes.TikTok import TikTok, TikTokClientError

        client = TikTok()
        client.post_video(video_path, title)
        return True
    except Exception as exc:
        warning(f"TikTok cross-post failed: {exc}")
        return False


def maybe_crosspost_native(
    video_path: str,
    title: str,
    video_public_url: str = "",
    interactive: bool = True,
    prompt_fn: Optional[Callable[[str], str]] = None,
) -> dict:
    """
    Attempt to cross-post to both Instagram and TikTok.

    Args:
        video_path (str): Local path to the video file.
        title (str): Video title / caption.
        video_public_url (str): Public URL for Instagram (not needed for TikTok).
        interactive (bool): Whether prompting is allowed.
        prompt_fn (Callable | None): Optional prompt override for testing.

    Returns:
        results (dict): Mapping of platform name to result (True/False/None).
    """
    results = {}

    results["instagram"] = maybe_crosspost_instagram(
        video_path=video_path,
        video_public_url=video_public_url,
        caption=title,
        interactive=interactive,
        prompt_fn=prompt_fn,
    )

    results["tiktok"] = maybe_crosspost_tiktok(
        video_path=video_path,
        title=title,
        interactive=interactive,
        prompt_fn=prompt_fn,
    )

    return results
