import os
from typing import Callable
from typing import Optional

from classes.PostBridge import PostBridge
from classes.PostBridge import PostBridgeClientError
from config import get_post_bridge_config
from status import info
from status import question
from status import success
from status import warning


def resolve_social_account_ids(
    client: PostBridge,
    configured_account_ids: list[int],
    platforms: list[str],
    interactive: bool,
    prompt_fn: Optional[Callable[[str], str]] = None,
) -> list[int]:
    """
    Resolve the social account IDs to use for a cross-post.

    Args:
        client (PostBridge): Post Bridge client instance.
        configured_account_ids (list[int]): Preconfigured account IDs.
        platforms (list[str]): Target platforms in config order.
        interactive (bool): Whether prompting is allowed.
        prompt_fn (Callable | None): Optional prompt function override for tests.

    Returns:
        account_ids (list[int]): Resolved target account IDs.
    """
    resolved_accounts = resolve_social_accounts(
        client=client,
        configured_account_ids=configured_account_ids,
        platforms=platforms,
        interactive=interactive,
        prompt_fn=prompt_fn,
    )
    return [account["id"] for account in resolved_accounts]


def resolve_social_accounts(
    client: PostBridge,
    configured_account_ids: list[int],
    platforms: list[str],
    interactive: bool,
    prompt_fn: Optional[Callable[[str], str]] = None,
) -> list[dict]:
    """
    Resolve the social account records to use for a cross-post.

    Args:
        client (PostBridge): Post Bridge client instance.
        configured_account_ids (list[int]): Preconfigured account IDs.
        platforms (list[str]): Target platforms in config order.
        interactive (bool): Whether prompting is allowed.
        prompt_fn (Callable | None): Optional prompt function override for tests.

    Returns:
        accounts (list[dict]): Resolved target account records.
    """
    if configured_account_ids:
        resolved_accounts = []
        for index, account_id in enumerate(configured_account_ids):
            platform = platforms[index] if index < len(platforms) else ""
            resolved_accounts.append(
                {
                    "id": int(account_id),
                    "platform": platform,
                }
            )
        return resolved_accounts

    if prompt_fn is None:
        prompt_fn = question

    available_accounts = client.list_social_accounts(platforms=platforms or None)

    accounts_by_platform = {}
    for account in available_accounts:
        platform = account.get("platform")
        accounts_by_platform.setdefault(platform, []).append(account)

    resolved_accounts = []

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
            resolved_accounts.append(selected_account)
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
                resolved_accounts.append(selected_account)
                break

            warning("Invalid selection. Please try again.")

    if resolved_accounts:
        info(
            "Tip: Add these Post Bridge account IDs to config.json to skip prompts:"
        )
        info(f' "account_ids": {[account["id"] for account in resolved_accounts]}', False)

    return resolved_accounts


def build_platform_configurations(
    title: str,
    description: str = "",
    include_youtube: bool = False,
    target_platforms: Optional[set[str]] = None,
) -> dict:
    """
    Build platform-specific post overrides for Post Bridge.

    Args:
        title (str): Video title generated by YouTube flow.
        description (str): Video description generated by YouTube flow.

    Returns:
        platform_configurations (dict): Platform override payload.
    """
    cleaned_title = title.strip()
    if not cleaned_title:
        return {}

    cleaned_description = description.strip()

    platform_configurations = {}

    if target_platforms is None or "tiktok" in target_platforms:
        platform_configurations["tiktok"] = {
            "title": cleaned_title,
        }

    if include_youtube and (target_platforms is None or "youtube" in target_platforms):
        platform_configurations["youtube"] = {
            "title": cleaned_title,
        }
        if cleaned_description:
            platform_configurations["youtube"]["caption"] = cleaned_description

    return platform_configurations


def _filter_platform_targets(
    platforms: list[str],
    configured_account_ids: list[int],
    include_youtube: bool,
    excluded_platforms: Optional[list[str]] = None,
) -> tuple[list[str], list[int]]:
    if not platforms:
        return platforms, configured_account_ids

    excluded_platform_names = {
        str(platform).strip().lower()
        for platform in list(excluded_platforms or [])
        if str(platform).strip()
    }

    filtered_platforms = []
    filtered_account_ids = []

    for index, platform in enumerate(platforms):
        normalized_platform = str(platform).strip().lower()
        if not include_youtube and normalized_platform == "youtube":
            continue

        if normalized_platform in excluded_platform_names:
            continue

        filtered_platforms.append(platform)
        if index < len(configured_account_ids):
            filtered_account_ids.append(configured_account_ids[index])

    if configured_account_ids and len(configured_account_ids) > len(platforms):
        filtered_account_ids.extend(configured_account_ids[len(platforms) :])

    return filtered_platforms, filtered_account_ids


def maybe_crosspost_youtube_short(
    video_path: str,
    title: str,
    interactive: bool,
    description: str = "",
    prompt_fn: Optional[Callable[[str], str]] = None,
    return_details: bool = False,
    include_youtube: bool = False,
    skip_confirmation: bool = False,
    excluded_platforms: Optional[list[str]] = None,
) -> Optional[bool | dict]:
    """
    Cross-post a successfully uploaded YouTube Short via Post Bridge.

    Args:
        video_path (str): Path to generated video file.
        title (str): Generated YouTube title.
        interactive (bool): Whether prompting is allowed.
        prompt_fn (Callable | None): Optional prompt function override for tests.

    Returns:
        result (bool | dict | None): True/False/None by default, or a detailed
            result dictionary when return_details is enabled.
    """
    config = get_post_bridge_config()

    if not config["enabled"]:
        info("Post Bridge cross-post is disabled. Skipping.")
        return None

    if not config["api_key"]:
        warning(
            "Post Bridge is enabled but no API key is configured. "
            "Set post_bridge.api_key or POST_BRIDGE_API_KEY."
        )
        return None

    if not os.path.exists(video_path):
        warning(f"Cannot cross-post because the video file was not found: {video_path}")
        return False

    platforms, configured_account_ids = _filter_platform_targets(
        config["platforms"],
        config["account_ids"],
        include_youtube=include_youtube,
        excluded_platforms=excluded_platforms,
    )
    if excluded_platforms and not platforms and not configured_account_ids:
        info("This Short is already posted to all configured Post Bridge platforms. Skipping.")
        if return_details:
            return {
                "posted": False,
                "skipped": True,
                "platforms": {},
            }
        return True

    if not platforms and not configured_account_ids:
        warning("Post Bridge is enabled but no supported platforms are configured.")
        return None

    if prompt_fn is None:
        prompt_fn = question

    platform_label = ", ".join(platforms) if platforms else "configured Post Bridge accounts"

    if interactive:
        should_crosspost = config["auto_crosspost"] or skip_confirmation
        if should_crosspost:
            info(f"Auto-cross-posting this video to {platform_label} via Post Bridge.")
        else:
            response = prompt_fn(
                f"Cross-post this video to {platform_label} via Post Bridge? (Yes/No): "
            ).strip().lower()
            should_crosspost = response in {"y", "yes"}
    else:
        if not config["auto_crosspost"]:
            info(
                "Post Bridge is enabled, but auto_crosspost is disabled. "
                "Skipping cross-post in cron mode."
            )
            return None
        should_crosspost = True

    if not should_crosspost:
        info("Skipped Post Bridge cross-post.")
        return None

    post_caption = title.strip()
    if not post_caption:
        post_caption = os.path.splitext(os.path.basename(video_path))[0]

    client = PostBridge(config["api_key"])

    try:
        accounts = resolve_social_accounts(
            client=client,
            configured_account_ids=configured_account_ids,
            platforms=platforms,
            interactive=interactive,
            prompt_fn=prompt_fn,
        )
        account_ids = [account["id"] for account in accounts]
        if not account_ids:
            warning("No Post Bridge accounts were resolved. Skipping cross-post.")
            return None

        media_id = client.upload_media(video_path)
        result = client.create_post(
            caption=post_caption,
            social_account_ids=account_ids,
            media_ids=[media_id],
            platform_configurations=build_platform_configurations(
                title,
                description=description,
                include_youtube=include_youtube,
                target_platforms={
                    str(platform).strip().lower() for platform in platforms
                } if platforms else None,
            ),
        )

        platform_statuses = {}
        post_id = result.get("id", "unknown")
        for account in accounts:
            platform = str(account.get("platform", "")).strip().lower()
            if not platform:
                continue
            platform_statuses[platform] = {
                "status": "success",
                "post_id": post_id,
            }

        success(f"Cross-posted via Post Bridge (post ID: {result.get('id', 'unknown')}).")
        for warning_message in result.get("warnings", []):
            warning(f"Post Bridge warning: {warning_message}")
        if return_details:
            return {
                "posted": True,
                "post_id": post_id,
                "platforms": platform_statuses,
            }
        return True
    except PostBridgeClientError as exc:
        warning(f"Post Bridge cross-post failed: {exc}")
        if return_details:
            return {
                "posted": False,
                "platforms": {},
                "error": str(exc),
            }
        return False
