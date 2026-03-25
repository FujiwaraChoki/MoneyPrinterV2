import os
import json
import fcntl
import tempfile

from typing import List
from config import ROOT_DIR


def get_cache_path() -> str:
    """Gets the path to the cache folder."""
    return os.path.join(ROOT_DIR, '.mp')


def get_afm_cache_path() -> str:
    """Gets the path to the Affiliate Marketing cache file."""
    return os.path.join(get_cache_path(), 'afm.json')


def get_twitter_cache_path() -> str:
    """Gets the path to the Twitter cache file."""
    return os.path.join(get_cache_path(), 'twitter.json')


def get_youtube_cache_path() -> str:
    """Gets the path to the YouTube cache file."""
    return os.path.join(get_cache_path(), 'youtube.json')


def get_provider_cache_path(provider: str) -> str:
    """
    Gets the cache path for a supported account provider.

    Args:
        provider (str): The provider name ("twitter" or "youtube")

    Returns:
        path (str): The provider-specific cache path

    Raises:
        ValueError: If the provider is unsupported
    """
    if provider == "twitter":
        return get_twitter_cache_path()
    if provider == "youtube":
        return get_youtube_cache_path()

    raise ValueError(f"Unsupported provider '{provider}'. Expected 'twitter' or 'youtube'.")


def _read_json_locked(path: str) -> dict:
    """
    Reads a JSON file with a shared (read) lock.
    Prevents reading while another process is writing.
    """
    with open(path, 'r') as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        try:
            return json.load(f)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def _write_json_atomic(path: str, data: dict) -> None:
    """
    Writes a JSON file atomically using a temp file + rename.
    Uses an exclusive lock to prevent concurrent writes.

    The write goes to a temporary file in the same directory,
    then atomically replaces the target via os.replace().
    This prevents partial/corrupt reads from concurrent processes.
    """
    dir_name = os.path.dirname(path)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                json.dump(data, f, indent=4)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
        os.replace(tmp_path, path)
    except BaseException:
        # Clean up temp file on any failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _ensure_cache_file(path: str, default_data: dict) -> None:
    """Creates a cache file with default_data if it does not exist."""
    if not os.path.exists(path):
        _write_json_atomic(path, default_data)


def get_accounts(provider: str) -> List[dict]:
    """
    Gets the accounts from the cache.

    Args:
        provider (str): The provider to get the accounts for

    Returns:
        accounts (List[dict]): The accounts
    """
    cache_path = get_provider_cache_path(provider)
    _ensure_cache_file(cache_path, {"accounts": []})

    parsed = _read_json_locked(cache_path)

    if parsed is None:
        return []

    if 'accounts' not in parsed:
        return []

    return parsed['accounts']


def add_account(provider: str, account: dict) -> None:
    """
    Adds an account to the cache.

    Args:
        provider (str): The provider to add the account to ("twitter" or "youtube")
        account (dict): The account to add
    """
    cache_path = get_provider_cache_path(provider)
    accounts = get_accounts(provider)
    accounts.append(account)
    _write_json_atomic(cache_path, {"accounts": accounts})


def remove_account(provider: str, account_id: str) -> None:
    """
    Removes an account from the cache.

    Args:
        provider (str): The provider to remove the account from ("twitter" or "youtube")
        account_id (str): The ID of the account to remove
    """
    accounts = get_accounts(provider)
    accounts = [account for account in accounts if account['id'] != account_id]
    cache_path = get_provider_cache_path(provider)
    _write_json_atomic(cache_path, {"accounts": accounts})


def get_products() -> List[dict]:
    """Gets the products from the cache."""
    _ensure_cache_file(get_afm_cache_path(), {"products": []})

    parsed = _read_json_locked(get_afm_cache_path())
    return parsed.get("products", [])


def add_product(product: dict) -> None:
    """
    Adds a product to the cache.

    Args:
        product (dict): The product to add
    """
    products = get_products()
    products.append(product)
    _write_json_atomic(get_afm_cache_path(), {"products": products})


def get_results_cache_path() -> str:
    """Gets the path to the results cache file."""
    return os.path.join(get_cache_path(), 'scraper_results.csv')
