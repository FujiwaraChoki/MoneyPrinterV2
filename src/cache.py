import os
import json

from typing import List
from config import ROOT_DIR

def get_cache_path() -> str:
    """
    Gets the path to the cache file.

    Returns:
        path (str): The path to the cache folder
    """
    return os.path.join(ROOT_DIR, '.mp')

def get_afm_cache_path() -> str:
    """
    Gets the path to the Affiliate Marketing cache file.

    Returns:
        path (str): The path to the AFM cache folder
    """
    return os.path.join(get_cache_path(), 'afm.json')

def get_twitter_cache_path() -> str:
    """
    Gets the path to the Twitter cache file.

    Returns:
        path (str): The path to the Twitter cache folder
    """
    return os.path.join(get_cache_path(), 'twitter.json')

def get_youtube_cache_path() -> str:
    """
    Gets the path to the YouTube cache file.

    Returns:
        path (str): The path to the YouTube cache folder
    """
    return os.path.join(get_cache_path(), 'youtube.json')

def get_accounts(provider: str) -> List[dict]:
    """
    Gets the accounts from the cache.

    Args:
        provider (str): The provider to get the accounts for

    Returns:
        account (List[dict]): The accounts
    """
    cache_path = ""

    if provider == "twitter":
        cache_path = get_twitter_cache_path()
    elif provider == "youtube":
        cache_path = get_youtube_cache_path()

    if not os.path.exists(cache_path):
        # Create the cache file
        with open(cache_path, 'w') as file:
            json.dump({
                "accounts": []
            }, file, indent=4)

    with open(cache_path, 'r') as file:
        parsed = json.load(file)

        if parsed is None:
            return []
        
        if 'accounts' not in parsed:
            return []

        # Get accounts dictionary
        return parsed['accounts']

def add_account(provider: str, account: dict) -> None:
    """
    Adds an account to the cache.

    Args:
        account (dict): The account to add

    Returns:
        None
    """
    if provider == "twitter":
        # Get the current accounts
        accounts = get_accounts("twitter")

        # Add the new account
        accounts.append(account)

        # Write the new accounts to the cache
        with open(get_twitter_cache_path(), 'w') as file:
            json.dump({
                "accounts": accounts
            }, file, indent=4)
    elif provider == "youtube":
        # Get the current accounts
        accounts = get_accounts("youtube")

        # Add the new account
        accounts.append(account)

        # Write the new accounts to the cache
        with open(get_youtube_cache_path(), 'w') as file:
            json.dump({
                "accounts": accounts
            }, file, indent=4)

def remove_account(account_id: str) -> None:
    """
    Removes an account from the cache.

    Args:
        account_id (str): The ID of the account to remove

    Returns:
        None
    """
    # Get the current accounts
    accounts = get_accounts()

    # Remove the account
    accounts = [account for account in accounts if account['id'] != account_id]

    # Write the new accounts to the cache
    with open(get_twitter_cache_path(), 'w') as file:
        json.dump({
            "accounts": accounts
        }, file, indent=4)

def get_products() -> List[dict]:
    """
    Gets the products from the cache.

    Returns:
        products (List[dict]): The products
    """
    if not os.path.exists(get_afm_cache_path()):
        # Create the cache file
        with open(get_afm_cache_path(), 'w') as file:
            json.dump({
                "products": []
            }, file, indent=4)

    with open(get_afm_cache_path(), 'r') as file:
        parsed = json.load(file)

        # Get the products
        return parsed["products"]
    
def add_product(product: dict) -> None:
    """
    Adds a product to the cache.

    Args:
        product (dict): The product to add

    Returns:
        None
    """
    # Get the current products
    products = get_products()

    # Add the new product
    products.append(product)

    # Write the new products to the cache
    with open(get_afm_cache_path(), 'w') as file:
        json.dump({
            "products": products
        }, file, indent=4)
    
def get_results_cache_path() -> str:
    """
    Gets the path to the results cache file.

    Returns:
        path (str): The path to the results cache folder
    """
    return os.path.join(get_cache_path(), 'scraper_results.csv')
