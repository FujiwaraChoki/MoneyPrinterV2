import os
from typing import Callable
from typing import Optional

from classes.PostBridge import PostBridge
from classes.PostBridge import PostBridgeClientError
from config import POST_BRIDGE_SUPPORTED_PLATFORMS
from config import get_post_bridge_config
from config import get_video_publishing_config
from config import load_config
from config import update_config_section
from status import info
from status import question
from status import success
from status import warning


PromptFn = Callable[[str], str]


def _is_yes(value: str) -> bool:
    return value.strip().lower() in {"y", "yes"}


def _normalize_csv_numbers(
    raw_value: str,
    max_value: int,
) -> list[int]:
    values = []
    seen_values = set()

    for chunk in raw_value.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue

        try:
            selected_index = int(chunk)
        except ValueError:
            return []

        if not 1 <= selected_index <= max_value:
            return []

        if selected_index not in seen_values:
            values.append(selected_index)
            seen_values.add(selected_index)

    return values


def _build_publish_caption(video_path: str, description: str, title: str) -> str:
    cleaned_description = description.strip()
    if cleaned_description:
        return cleaned_description

    cleaned_title = title.strip()
    if cleaned_title:
        return cleaned_title

    return os.path.splitext(os.path.basename(video_path))[0]


def _prompt_for_platforms(
    prompt_fn: PromptFn,
    default_platforms: list[str],
) -> list[str]:
    info("Select the platforms this video publisher should target:")
    for index, platform in enumerate(POST_BRIDGE_SUPPORTED_PLATFORMS, start=1):
        info(f" {index}. {platform}", False)

    default_selection = [
        str(POST_BRIDGE_SUPPORTED_PLATFORMS.index(platform) + 1)
        for platform in default_platforms
        if platform in POST_BRIDGE_SUPPORTED_PLATFORMS
    ]
    default_label = ",".join(default_selection)

    while True:
        response = prompt_fn(
            f"Enter comma-separated platform numbers [{default_label}]: "
        ).strip()

        if not response:
            selected_indexes = [
                int(value) for value in default_selection
            ]
        else:
            selected_indexes = _normalize_csv_numbers(
                response,
                max_value=len(POST_BRIDGE_SUPPORTED_PLATFORMS),
            )

        if not selected_indexes:
            warning("Please select at least one valid platform.")
            continue

        return [
            POST_BRIDGE_SUPPORTED_PLATFORMS[selected_index - 1]
            for selected_index in selected_indexes
        ]


def resolve_social_account_ids(
    client: PostBridge,
    configured_account_ids: list[int],
    platforms: list[str],
    interactive: bool,
    prompt_fn: Optional[PromptFn] = None,
) -> list[int]:
    """
    Resolve the social account IDs to use for a publish.

    Args:
        client (PostBridge): Post Bridge client instance.
        configured_account_ids (list[int]): Preconfigured account IDs.
        platforms (list[str]): Target platforms in config order.
        interactive (bool): Whether prompting is allowed.
        prompt_fn (Callable | None): Optional prompt function override for tests.

    Returns:
        account_ids (list[int]): Resolved target account IDs.
    """
    if configured_account_ids:
        return configured_account_ids

    if prompt_fn is None:
        prompt_fn = question

    accounts = client.list_social_accounts(platforms=platforms)
    accounts_by_platform = {}
    for account in accounts:
        platform = account.get("platform")
        accounts_by_platform.setdefault(platform, []).append(account)

    resolved_account_ids = []

    for platform in platforms:
        platform_accounts = accounts_by_platform.get(platform, [])

        if len(platform_accounts) == 0:
            warning(f"No connected Post Bridge accounts found for {platform}.")
            continue

        if len(platform_accounts) == 1:
            selected_account = platform_accounts[0]
            info(
                f"Using Post Bridge account for {platform}: "
                f"@{selected_account.get('username', '?')}"
            )
            resolved_account_ids.append(selected_account["id"])
            continue

        if not interactive:
            warning(
                f"Multiple Post Bridge accounts found for {platform}. "
                "Configure account_ids in config.json or run interactively."
            )
            return []

        info(f"Multiple Post Bridge accounts found for {platform}:")
        for index, account in enumerate(platform_accounts, start=1):
            info(
                f" {index}. @{account.get('username', '?')} "
                f"(ID: {account['id']})",
                False,
            )

        while True:
            choice = prompt_fn(
                f"Select the {platform} account to use (1-{len(platform_accounts)}): "
            ).strip()
            try:
                selected_index = int(choice) - 1
            except ValueError:
                warning("Invalid selection. Please enter a number.")
                continue

            if 0 <= selected_index < len(platform_accounts):
                selected_account = platform_accounts[selected_index]
                resolved_account_ids.append(selected_account["id"])
                break

            warning("Invalid selection. Please try again.")

    if resolved_account_ids:
        info("Tip: These Post Bridge account IDs can be persisted in config.json:")
        info(f' "account_ids": {resolved_account_ids}', False)

    return resolved_account_ids


def build_platform_configurations(
    title: str,
    description: str,
    platforms: list[str],
) -> dict:
    """
    Build platform-specific post overrides for Post Bridge.

    Args:
        title (str): Generated video title.
        description (str): Generated video description.
        platforms (list[str]): Configured target platforms.

    Returns:
        platform_configurations (dict): Platform override payload.
    """
    cleaned_title = title.strip()
    cleaned_description = description.strip()
    platform_configurations = {}

    if "youtube" in platforms:
        youtube_config = {}
        if cleaned_title:
            youtube_config["title"] = cleaned_title
        if cleaned_description:
            youtube_config["caption"] = cleaned_description
        if youtube_config:
            platform_configurations["youtube"] = youtube_config

    if "tiktok" in platforms and cleaned_title:
        platform_configurations["tiktok"] = {"title": cleaned_title}

    return platform_configurations


def run_post_bridge_setup_wizard(
    prompt_fn: Optional[PromptFn] = None,
) -> Optional[dict]:
    """
    Guide the user through a config-backed Post Bridge publisher setup.

    Args:
        prompt_fn (Callable | None): Optional prompt function override for tests.

    Returns:
        config (dict | None): Persisted Post Bridge config on success.
    """
    if prompt_fn is None:
        prompt_fn = question

    raw_config = load_config()
    raw_post_bridge_config = raw_config.get("post_bridge", {})
    if not isinstance(raw_post_bridge_config, dict):
        raw_post_bridge_config = {}

    current_post_bridge_config = get_post_bridge_config()
    current_video_config = get_video_publishing_config()

    info("Starting the Post Bridge video publishing setup wizard...")
    profile_name = (
        prompt_fn(
            f"Publisher name [{current_video_config['profile_name']}]: "
        ).strip()
        or current_video_config["profile_name"]
    )
    niche = (
        prompt_fn(
            "Video niche/topic "
            f"[{current_video_config['niche'] or 'required'}]: "
        ).strip()
        or current_video_config["niche"]
    )
    language = (
        prompt_fn(
            f"Video language [{current_video_config['language']}]: "
        ).strip()
        or current_video_config["language"]
    )

    stored_api_key = str(raw_post_bridge_config.get("api_key", "")).strip()
    entered_api_key = prompt_fn(
        "Post Bridge API key "
        "[leave blank to keep current value or use POST_BRIDGE_API_KEY]: "
    ).strip()
    if entered_api_key:
        api_key = entered_api_key
    else:
        api_key = current_post_bridge_config["api_key"]

    if not niche:
        warning("A video niche is required to generate content.")
        return None

    if not api_key:
        warning(
            "No Post Bridge API key is configured. Set one in config.json "
            "or export POST_BRIDGE_API_KEY."
        )
        return None

    default_platforms = (
        current_post_bridge_config["platforms"]
        or ["youtube", "tiktok", "instagram"]
    )
    platforms = _prompt_for_platforms(prompt_fn, default_platforms)

    client = PostBridge(api_key)
    try:
        account_ids = resolve_social_account_ids(
            client=client,
            configured_account_ids=[],
            platforms=platforms,
            interactive=True,
            prompt_fn=prompt_fn,
        )
    except PostBridgeClientError as exc:
        warning(f"Unable to fetch Post Bridge accounts: {exc}")
        return None

    if len(account_ids) != len(platforms):
        warning(
            "The setup wizard could not resolve one account for every selected "
            "platform. Connect the missing accounts in Post Bridge and try again."
        )
        return None

    auto_publish_default = "yes" if current_post_bridge_config["auto_publish"] else "no"
    auto_publish = _is_yes(
        prompt_fn(
            f"Auto-publish generated videos without confirmation? "
            f"(Yes/No) [{auto_publish_default}]: "
        ).strip()
        or auto_publish_default
    )

    update_config_section(
        "video_publishing",
        {
            "profile_name": profile_name,
            "niche": niche,
            "language": language,
        },
    )
    updated_config = update_config_section(
        "post_bridge",
        {
            "enabled": True,
            "api_key": entered_api_key or stored_api_key,
            "platforms": platforms,
            "account_ids": account_ids,
            "auto_publish": auto_publish,
        },
    )

    success("Saved Post Bridge video publishing settings to config.json.")
    return updated_config


def ensure_post_bridge_publishing_ready(
    interactive: bool,
    prompt_fn: Optional[PromptFn] = None,
) -> bool:
    """
    Ensure the app has enough config to generate and publish videos.

    Args:
        interactive (bool): Whether the user can be prompted.
        prompt_fn (Callable | None): Optional prompt function override for tests.

    Returns:
        ready (bool): Whether publishing can proceed.
    """
    if prompt_fn is None:
        prompt_fn = question

    post_bridge_config = get_post_bridge_config()
    video_config = get_video_publishing_config()

    missing_settings = []
    if not post_bridge_config["enabled"]:
        missing_settings.append("post_bridge.enabled")
    if not post_bridge_config["api_key"]:
        missing_settings.append("post_bridge.api_key")
    if (
        not post_bridge_config["platforms"]
        and not post_bridge_config["account_ids"]
    ):
        missing_settings.append("post_bridge.platforms")
    if not video_config["niche"]:
        missing_settings.append("video_publishing.niche")

    if not missing_settings:
        return True

    warning(
        "Video publishing is not configured yet. Missing: "
        + ", ".join(missing_settings)
    )
    if not interactive:
        return False

    if _is_yes(prompt_fn("Run the Post Bridge setup wizard now? (Yes/No): ")):
        return run_post_bridge_setup_wizard(prompt_fn=prompt_fn) is not None

    return False


def publish_video(
    video_path: str,
    title: str,
    description: str,
    interactive: bool,
    prompt_fn: Optional[PromptFn] = None,
) -> Optional[bool]:
    """
    Publish a generated video via Post Bridge.

    Args:
        video_path (str): Path to generated video file.
        title (str): Generated video title.
        description (str): Generated video description.
        interactive (bool): Whether prompting is allowed.
        prompt_fn (Callable | None): Optional prompt function override for tests.

    Returns:
        result (bool | None): True when published, False when attempted and failed,
            None when skipped.
    """
    if prompt_fn is None:
        prompt_fn = question

    if not ensure_post_bridge_publishing_ready(
        interactive=interactive,
        prompt_fn=prompt_fn,
    ):
        return None

    post_bridge_config = get_post_bridge_config()

    if not os.path.exists(video_path):
        warning(f"Cannot publish because the video file was not found: {video_path}")
        return False

    if interactive:
        should_publish = post_bridge_config["auto_publish"]
        if not should_publish:
            platform_label = ", ".join(post_bridge_config["platforms"])
            response = prompt_fn(
                f"Publish this video to {platform_label} via Post Bridge? (Yes/No): "
            ).strip()
            should_publish = _is_yes(response)
    else:
        if not post_bridge_config["auto_publish"]:
            info(
                "Post Bridge is enabled, but auto_publish is disabled. "
                "Skipping publish in cron mode."
            )
            return None
        should_publish = True

    if not should_publish:
        return None

    caption = _build_publish_caption(video_path, description, title)
    client = PostBridge(post_bridge_config["api_key"])

    try:
        account_ids = resolve_social_account_ids(
            client=client,
            configured_account_ids=post_bridge_config["account_ids"],
            platforms=post_bridge_config["platforms"],
            interactive=interactive,
            prompt_fn=prompt_fn,
        )
        if not account_ids:
            warning("No Post Bridge accounts were resolved. Skipping publish.")
            return None

        media_id = client.upload_media(video_path)
        result = client.create_post(
            caption=caption,
            social_account_ids=account_ids,
            media_ids=[media_id],
            platform_configurations=build_platform_configurations(
                title=title,
                description=description,
                platforms=post_bridge_config["platforms"],
            ),
        )

        success(
            f"Published via Post Bridge (post ID: {result.get('id', 'unknown')})."
        )
        for warning_message in result.get("warnings", []):
            warning(f"Post Bridge warning: {warning_message}")
        return True
    except PostBridgeClientError as exc:
        warning(f"Post Bridge publishing failed: {exc}")
        return False


def get_publish_history(limit: int = 10) -> list[dict]:
    """
    Fetch recent publish history from Post Bridge.

    Args:
        limit (int): Number of posts to load.

    Returns:
        history (list[dict]): Recent posts enriched with post results.
    """
    post_bridge_config = get_post_bridge_config()
    if not post_bridge_config["enabled"] or not post_bridge_config["api_key"]:
        warning(
            "Post Bridge publishing is not configured. Run the setup wizard first."
        )
        return []

    client = PostBridge(post_bridge_config["api_key"])
    posts = client.list_posts(
        platforms=post_bridge_config["platforms"],
        statuses=["posted", "scheduled", "processing"],
        limit=limit,
    )
    if not posts:
        return []

    social_accounts = client.list_social_accounts(platforms=post_bridge_config["platforms"])
    platform_by_social_account_id = {}
    for social_account in social_accounts:
        social_account_id = social_account.get("id")
        platform = social_account.get("platform")
        if social_account_id is None or not platform:
            continue
        try:
            platform_by_social_account_id[int(social_account_id)] = platform
        except (TypeError, ValueError):
            continue

    post_ids = [post.get("id") for post in posts if post.get("id")]
    result_limit = max(limit * max(len(post_bridge_config["platforms"]), 1), limit)
    post_results = client.list_post_results(
        post_ids=post_ids,
        platforms=post_bridge_config["platforms"],
        limit=result_limit,
    )

    results_by_post_id = {}
    for post_result in post_results:
        post_id = post_result.get("post_id")
        if not post_id:
            continue
        results_by_post_id.setdefault(post_id, []).append(post_result)

    history = []
    for post in posts:
        target_platforms = []
        seen_platforms = set()
        for social_account_id in post.get("social_accounts") or []:
            try:
                normalized_account_id = int(social_account_id)
            except (TypeError, ValueError):
                continue

            platform = platform_by_social_account_id.get(normalized_account_id)
            if platform and platform not in seen_platforms:
                target_platforms.append(platform)
                seen_platforms.add(platform)

        if not target_platforms:
            platform_configurations = post.get("platform_configurations") or {}
            for platform in platform_configurations.keys():
                if platform not in seen_platforms:
                    target_platforms.append(platform)
                    seen_platforms.add(platform)

        if not target_platforms:
            target_platforms = post_bridge_config["platforms"]

        results = results_by_post_id.get(post.get("id"), [])
        urls = []
        failures = []
        for result in results:
            platform_data = result.get("platform_data") or {}
            if platform_data.get("url"):
                urls.append(platform_data["url"])
            if not result.get("success"):
                error_payload = result.get("error") or {}
                failures.append(str(error_payload or "Unknown publishing error"))

        history.append(
            {
                "id": post.get("id", ""),
                "created_at": post.get("created_at", ""),
                "status": post.get("status", "unknown"),
                "caption": post.get("caption", ""),
                "platforms": target_platforms,
                "urls": urls,
                "failures": failures,
            }
        )

    return history


def maybe_crosspost_youtube_short(
    video_path: str,
    title: str,
    interactive: bool,
    prompt_fn: Optional[PromptFn] = None,
) -> Optional[bool]:
    """
    Backward-compatible alias for legacy tests and callers.
    """
    return publish_video(
        video_path=video_path,
        title=title,
        description=title,
        interactive=interactive,
        prompt_fn=prompt_fn,
    )
