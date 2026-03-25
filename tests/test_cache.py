import json
import os

import pytest

import cache
import config


@pytest.fixture
def cache_env(patch_root_dir):
    """Sets up cache directory and patches ROOT_DIR in cache module too."""
    import cache as cache_mod

    # cache imports ROOT_DIR from config at import time, so patch it
    original = cache_mod.ROOT_DIR
    cache_mod.ROOT_DIR = str(patch_root_dir)
    yield patch_root_dir
    cache_mod.ROOT_DIR = original


class TestCachePaths:
    def test_get_cache_path(self, cache_env):
        path = cache.get_cache_path()
        assert path.endswith(".mp")

    def test_get_twitter_cache_path(self, cache_env):
        assert cache.get_twitter_cache_path().endswith("twitter.json")

    def test_get_youtube_cache_path(self, cache_env):
        assert cache.get_youtube_cache_path().endswith("youtube.json")

    def test_get_afm_cache_path(self, cache_env):
        assert cache.get_afm_cache_path().endswith("afm.json")


class TestProviderCachePath:
    def test_twitter_provider(self, cache_env):
        assert cache.get_provider_cache_path("twitter") == cache.get_twitter_cache_path()

    def test_youtube_provider(self, cache_env):
        assert cache.get_provider_cache_path("youtube") == cache.get_youtube_cache_path()

    def test_invalid_provider_raises(self, cache_env):
        with pytest.raises(ValueError, match="Unsupported provider"):
            cache.get_provider_cache_path("instagram")


class TestAccounts:
    def test_get_accounts_creates_file_when_missing(self, cache_env):
        accounts = cache.get_accounts("twitter")
        assert accounts == []
        assert os.path.exists(cache.get_twitter_cache_path())

    def test_add_account(self, cache_env):
        account = {"id": "abc-123", "nickname": "test", "posts": []}
        cache.add_account("twitter", account)
        accounts = cache.get_accounts("twitter")
        assert len(accounts) == 1
        assert accounts[0]["id"] == "abc-123"

    def test_add_multiple_accounts(self, cache_env):
        cache.add_account("youtube", {"id": "yt-1", "nickname": "a", "videos": []})
        cache.add_account("youtube", {"id": "yt-2", "nickname": "b", "videos": []})
        accounts = cache.get_accounts("youtube")
        assert len(accounts) == 2

    def test_remove_account(self, cache_env):
        cache.add_account("twitter", {"id": "del-me", "nickname": "gone", "posts": []})
        cache.add_account("twitter", {"id": "keep-me", "nickname": "stay", "posts": []})
        cache.remove_account("twitter", "del-me")
        accounts = cache.get_accounts("twitter")
        assert len(accounts) == 1
        assert accounts[0]["id"] == "keep-me"

    def test_remove_nonexistent_account(self, cache_env):
        cache.add_account("twitter", {"id": "only", "nickname": "one", "posts": []})
        cache.remove_account("twitter", "does-not-exist")
        accounts = cache.get_accounts("twitter")
        assert len(accounts) == 1


class TestProducts:
    def test_get_products_creates_file_when_missing(self, cache_env):
        products = cache.get_products()
        assert products == []
        assert os.path.exists(cache.get_afm_cache_path())

    def test_add_product(self, cache_env):
        product = {"id": "prod-1", "affiliate_link": "https://amzn.to/abc", "twitter_uuid": "tw-1"}
        cache.add_product(product)
        products = cache.get_products()
        assert len(products) == 1
        assert products[0]["id"] == "prod-1"

    def test_add_multiple_products(self, cache_env):
        cache.add_product({"id": "p1", "affiliate_link": "https://a.co/1", "twitter_uuid": "t1"})
        cache.add_product({"id": "p2", "affiliate_link": "https://a.co/2", "twitter_uuid": "t2"})
        products = cache.get_products()
        assert len(products) == 2
