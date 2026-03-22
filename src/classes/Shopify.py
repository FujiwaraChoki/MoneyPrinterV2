import re
import os
import json
import base64
import time

from typing import List, Optional
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from cache import get_shopify_cache_path, get_accounts
from config import (
    get_verbose,
    get_shopify_access_token,
    get_shopify_store_name,
    get_shopify_products_per_run,
    get_nanobanana2_api_key,
    get_nanobanana2_api_base_url,
    get_nanobanana2_model,
    ROOT_DIR,
)
from status import info, success, error, warning
from llm_provider import generate_text


class Shopify:
    """Automates Shopify product listing generation using LLM and image generation."""

    def __init__(
        self,
        account_uuid: str,
        account_nickname: str,
        store_name: str,
        access_token: str,
        niche: str,
    ) -> None:
        self.account_uuid: str = account_uuid
        self.account_nickname: str = account_nickname
        self.store_name: str = store_name
        self.access_token: str = access_token
        self.niche: str = niche

        self._base_url: str = f"https://{self.store_name}.myshopify.com"
        self._headers: dict = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": self.access_token,
        }

    # ------------------------------------------------------------------
    # Shopify Admin API helpers
    # ------------------------------------------------------------------

    def _api_request(self, method: str, endpoint: str, data: Optional[dict] = None) -> dict:
        url = f"{self._base_url}/admin/api/2024-01/{endpoint}"
        body = json.dumps(data).encode("utf-8") if data else None

        req = Request(url, data=body, method=method)
        for key, value in self._headers.items():
            req.add_header(key, value)

        try:
            with urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            error(f"Shopify API error ({e.code}): {error_body}")
            raise
        except URLError as e:
            error(f"Network error reaching Shopify: {e.reason}")
            raise

    def get_existing_products(self, limit: int = 50) -> List[dict]:
        params = urlencode({"limit": limit})
        result = self._api_request("GET", f"products.json?{params}")
        return result.get("products", [])

    def create_product(self, product_data: dict) -> dict:
        result = self._api_request("POST", "products.json", {"product": product_data})
        return result.get("product", {})

    def update_product(self, product_id: int, product_data: dict) -> dict:
        result = self._api_request(
            "PUT", f"products/{product_id}.json", {"product": product_data}
        )
        return result.get("product", {})

    def publish_product(self, product_id: int) -> dict:
        return self.update_product(product_id, {"status": "active"})

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def get_collections(self) -> List[dict]:
        result = self._api_request("GET", "custom_collections.json")
        return result.get("custom_collections", [])

    def create_collection(self, title: str, body_html: str = "") -> dict:
        data = {
            "custom_collection": {
                "title": title,
                "body_html": body_html,
                "published": True,
            }
        }
        result = self._api_request("POST", "custom_collections.json", data)
        return result.get("custom_collection", {})

    def add_product_to_collection(self, product_id: int, collection_id: int) -> dict:
        data = {
            "collect": {
                "product_id": product_id,
                "collection_id": collection_id,
            }
        }
        result = self._api_request("POST", "collects.json", data)
        return result.get("collect", {})

    def find_or_create_collection(self, product_type: str) -> int:
        collections = self.get_collections()
        for c in collections:
            if c.get("title", "").lower() == product_type.lower():
                return c["id"]

        info(f"Creating collection: {product_type}")
        desc = generate_text(
            f"Write a short 1-sentence Shopify collection description for a "
            f"'{product_type}' collection in the '{self.niche}' niche. "
            f"Make it SEO-friendly and appeal to buyers. Return only the description text."
        )
        new_collection = self.create_collection(product_type, f"<p>{desc.strip()}</p>")
        return new_collection.get("id", 0)

    # ------------------------------------------------------------------
    # LLM content generation
    # ------------------------------------------------------------------

    def research_trending_products(self, count: int = 5) -> List[str]:
        prompt = (
            f"You are a Shopify dropshipping and e-commerce expert. "
            f"List {count} specific, high-demand product ideas for a '{self.niche}' store "
            f"that are trending right now and have strong profit margins. "
            f"Focus on products that:\n"
            f"- Solve a real problem or fulfill a desire\n"
            f"- Can be priced at $25-$75 for good margins\n"
            f"- Have high perceived value\n"
            f"- Are impulse-buy friendly\n"
            f"- Work well for social media marketing\n\n"
            f"Return ONLY a JSON array of product names, like: "
            f'[\"Product Name 1\", \"Product Name 2\", ...]\n'
            f"No explanations, just the JSON array."
        )
        raw = generate_text(prompt)
        json_match = re.search(r"\[[\s\S]*\]", raw)
        if json_match:
            try:
                ideas = json.loads(json_match.group())
                if isinstance(ideas, list):
                    return [str(i).strip() for i in ideas[:count]]
            except json.JSONDecodeError:
                pass

        # Fallback: split by newlines
        lines = [l.strip().lstrip("0123456789.-) ") for l in raw.strip().split("\n") if l.strip()]
        return [re.sub(r"[\"*]", "", l) for l in lines[:count]]

    def generate_product_idea(self) -> str:
        completion = generate_text(
            f"You are a Shopify e-commerce expert. Suggest one specific, high-demand product "
            f"for a '{self.niche}' store that would sell well online. "
            f"Pick something with high perceived value that's impulse-buy friendly. "
            f"Return only the product name, nothing else."
        )
        completion = re.sub(r"[\"*]", "", completion).strip()
        if get_verbose():
            info(f"Product idea: {completion}")
        return completion

    def generate_product_listing(self, product_name: str) -> dict:
        prompt = (
            f"You are a top Shopify copywriter who writes product listings that CONVERT. "
            f"Write a listing for: \"{product_name}\"\n"
            f"Niche: {self.niche}\n\n"
            f"Return ONLY valid JSON with these exact keys:\n"
            f'{{"title": "...", "body_html": "...", "product_type": "...", '
            f'"tags": "tag1, tag2, tag3, tag4, tag5", "price": "XX.99", '
            f'"compare_at_price": "XX.99", '
            f'"seo_title": "...", "seo_description": "..."}}\n\n'
            f"CRITICAL requirements for the body_html:\n"
            f"- Start with a bold hook that speaks to the customer's pain point or desire\n"
            f"- Use HTML with <h3> subheadings, <ul> bullet lists for features/benefits\n"
            f"- Include 3-4 paragraphs: hook, benefits, features, urgency/CTA\n"
            f"- Use power words: \"transform\", \"premium\", \"exclusive\", \"limited\"\n"
            f"- End with a scarcity/urgency line\n"
            f"- DO NOT use generic filler — every sentence should sell\n\n"
            f"Pricing rules:\n"
            f"- price should end in .99 and feel like a deal\n"
            f"- compare_at_price should be 40-60% higher (the 'original' price for strikethrough)\n"
            f"- Tags: include 5-8 relevant SEO tags comma-separated\n"
            f"- seo_title: under 60 chars, include primary keyword\n"
            f"- seo_description: under 155 chars, compelling with a CTA\n"
            f"- product_type: the category this belongs to"
        )
        raw = generate_text(prompt)

        json_match = re.search(r"\{[\s\S]*\}", raw)
        if json_match:
            try:
                listing = json.loads(json_match.group())
                if get_verbose():
                    info(f"Generated listing for: {listing.get('title', product_name)}")
                return listing
            except json.JSONDecodeError:
                pass

        warning("LLM did not return valid JSON. Using generated text as description.")
        return {
            "title": product_name,
            "body_html": f"<p>{raw}</p>",
            "product_type": self.niche,
            "tags": self.niche,
            "price": "29.99",
            "compare_at_price": "49.99",
            "seo_title": product_name,
            "seo_description": product_name,
        }

    def generate_product_image(self, product_name: str) -> Optional[str]:
        api_key = get_nanobanana2_api_key()
        if not api_key:
            warning("No image generation API key configured. Skipping image generation.")
            return None

        base_url = get_nanobanana2_api_base_url()
        model = get_nanobanana2_model()

        prompt = (
            f"Professional e-commerce product photo of {product_name}. "
            f"Clean white background, soft studio lighting with subtle shadows. "
            f"Product centered, shot at a slight angle to show dimension. "
            f"High-end commercial photography style, 4K quality, sharp focus. "
            f"The product should look premium and desirable."
        )

        url = f"{base_url}/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "responseMimeType": "text/plain",
            },
        }

        try:
            body = json.dumps(payload).encode("utf-8")
            req = Request(url, data=body, method="POST")
            req.add_header("Content-Type", "application/json")

            with urlopen(req) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            candidates = result.get("candidates", [])
            for candidate in candidates:
                parts = candidate.get("content", {}).get("parts", [])
                for part in parts:
                    if "inlineData" in part:
                        img_data = part["inlineData"]["data"]
                        img_path = os.path.join(ROOT_DIR, ".mp", f"shopify_{int(time.time())}.png")
                        with open(img_path, "wb") as f:
                            f.write(base64.b64decode(img_data))
                        if get_verbose():
                            info(f"Generated image: {img_path}")
                        return img_path
        except Exception as e:
            warning(f"Image generation failed: {e}")

        return None

    # ------------------------------------------------------------------
    # Twitter cross-promotion
    # ------------------------------------------------------------------

    def generate_promo_tweet(self, product_title: str, product_url: str) -> str:
        prompt = (
            f"Write a short, engaging tweet to promote this product on Twitter/X:\n"
            f"Product: {product_title}\n"
            f"Store niche: {self.niche}\n"
            f"Product URL: {product_url}\n\n"
            f"Requirements:\n"
            f"- Under 250 characters total (including the URL)\n"
            f"- Create urgency or curiosity\n"
            f"- Include 1-2 relevant hashtags\n"
            f"- Include the product URL at the end\n"
            f"- Sound authentic, not spammy\n"
            f"- Use an emoji or two naturally\n"
            f"Return ONLY the tweet text, nothing else."
        )
        tweet = generate_text(prompt)
        tweet = re.sub(r"[\"*]", "", tweet).strip()

        # Make sure URL is included
        if product_url not in tweet:
            tweet = tweet.rstrip() + " " + product_url

        # Truncate if over 280 chars
        if len(tweet) > 280:
            url_len = len(product_url) + 1
            tweet = tweet[:279 - url_len].rsplit(" ", 1)[0] + " " + product_url

        return tweet

    def cross_promote_on_twitter(self, product_title: str, product_id: int) -> bool:
        twitter_accounts = get_accounts("twitter")
        if not twitter_accounts:
            warning("No Twitter accounts configured. Skipping cross-promotion.")
            return False

        product_url = f"{self._base_url}/products"
        # Try to get the handle from the product
        try:
            result = self._api_request("GET", f"products/{product_id}.json")
            handle = result.get("product", {}).get("handle", "")
            if handle:
                product_url = f"{self._base_url}/products/{handle}"
        except Exception:
            pass

        tweet_text = self.generate_promo_tweet(product_title, product_url)
        info(f"Cross-promoting on Twitter: {tweet_text[:60]}...")

        # Use the first twitter account
        acc = twitter_accounts[0]
        try:
            from classes.Twitter import Twitter
            twitter = Twitter(
                acc["id"],
                acc["nickname"],
                acc["firefox_profile"],
                acc.get("topic", self.niche),
            )
            twitter.post(text=tweet_text)
            success("Cross-promoted product on Twitter!")
            return True
        except Exception as e:
            warning(f"Twitter cross-promotion failed: {e}")
            return False

    # ------------------------------------------------------------------
    # Core workflow
    # ------------------------------------------------------------------

    def generate_and_publish(
        self,
        product_name: Optional[str] = None,
        auto_activate: bool = False,
        cross_promote: bool = False,
    ) -> dict:
        if product_name is None:
            product_name = self.generate_product_idea()

        info(f"Generating listing for: {product_name}")
        listing = self.generate_product_listing(product_name)

        price = listing.pop("price", "29.99")
        compare_at_price = listing.pop("compare_at_price", "")
        seo_title = listing.pop("seo_title", listing.get("title", ""))
        seo_description = listing.pop("seo_description", "")
        product_type = listing.get("product_type", self.niche)

        variant = {"price": price, "inventory_management": None}
        if compare_at_price:
            variant["compare_at_price"] = compare_at_price

        product_data = {
            "title": listing.get("title", product_name),
            "body_html": listing.get("body_html", ""),
            "product_type": product_type,
            "tags": listing.get("tags", ""),
            "status": "active" if auto_activate else "draft",
            "variants": [variant],
            "metafields_global_title_tag": seo_title,
            "metafields_global_description_tag": seo_description,
        }

        # Generate product image
        img_path = self.generate_product_image(product_name)
        if img_path and os.path.exists(img_path):
            with open(img_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
            product_data["images"] = [
                {"attachment": img_b64, "filename": f"{product_name.replace(' ', '_')}.png"}
            ]

        status_label = "active" if auto_activate else "draft"
        info(f"Publishing product to Shopify (as {status_label})...")
        created = self.create_product(product_data)

        if created.get("id"):
            success(f"Product created: {created['title']} (ID: {created['id']})")

            # Auto-add to collection based on product_type
            try:
                collection_id = self.find_or_create_collection(product_type)
                if collection_id:
                    self.add_product_to_collection(created["id"], collection_id)
                    if get_verbose():
                        info(f"Added to collection: {product_type}")
            except Exception as e:
                warning(f"Could not add to collection: {e}")

            self.add_product_to_cache({
                "shopify_id": created["id"],
                "title": created["title"],
                "status": created.get("status", "draft"),
                "price": price,
                "compare_at_price": compare_at_price,
                "product_type": product_type,
                "date": datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
            })

            # Cross-promote on Twitter
            if cross_promote:
                self.cross_promote_on_twitter(created["title"], created["id"])
        else:
            error("Failed to create product on Shopify.")

        return created

    def bulk_generate(
        self,
        count: Optional[int] = None,
        auto_activate: bool = False,
        cross_promote: bool = False,
        use_research: bool = True,
    ) -> List[dict]:
        if count is None:
            count = get_shopify_products_per_run()

        # Research trending products for better ideas
        product_names = []
        if use_research:
            info("Researching trending products in your niche...")
            product_names = self.research_trending_products(count)
            if product_names:
                info(f"Found {len(product_names)} trending product ideas:")
                for i, name in enumerate(product_names):
                    info(f"  {i + 1}. {name}")

        created_products = []
        for i in range(count):
            info(f"Generating product {i + 1}/{count}...")
            name = product_names[i] if i < len(product_names) else None
            try:
                product = self.generate_and_publish(
                    product_name=name,
                    auto_activate=auto_activate,
                    cross_promote=cross_promote,
                )
                created_products.append(product)
            except Exception as e:
                error(f"Failed to generate product {i + 1}: {e}")

        success(f"Generated {len(created_products)}/{count} products.")
        return created_products

    def optimize_existing(self) -> List[dict]:
        info("Fetching existing products from Shopify...")
        products = self.get_existing_products()

        if not products:
            warning("No existing products found on Shopify.")
            return []

        optimized = []
        for product in products:
            title = product.get("title", "Unknown")
            body = product.get("body_html", "")

            if len(body) < 200:
                info(f"Optimizing thin listing: {title}")
                new_listing = self.generate_product_listing(title)

                update_data = {
                    "body_html": new_listing.get("body_html", body),
                    "tags": new_listing.get("tags", product.get("tags", "")),
                }

                # Add compare_at_price if missing
                variants = product.get("variants", [])
                if variants and not variants[0].get("compare_at_price"):
                    compare = new_listing.get("compare_at_price", "")
                    if compare:
                        update_data["variants"] = [{"id": variants[0]["id"], "compare_at_price": compare}]

                # Add SEO if missing
                seo_title = new_listing.get("seo_title", "")
                seo_desc = new_listing.get("seo_description", "")
                if seo_title:
                    update_data["metafields_global_title_tag"] = seo_title
                if seo_desc:
                    update_data["metafields_global_description_tag"] = seo_desc

                try:
                    updated = self.update_product(product["id"], update_data)
                    optimized.append(updated)
                    success(f"Optimized: {title}")
                except Exception as e:
                    error(f"Failed to optimize {title}: {e}")

        success(f"Optimized {len(optimized)} products.")
        return optimized

    def activate_all_drafts(self) -> List[dict]:
        info("Fetching draft products...")
        products = self.get_existing_products(limit=250)
        drafts = [p for p in products if p.get("status") == "draft"]

        if not drafts:
            warning("No draft products found.")
            return []

        activated = []
        for product in drafts:
            try:
                updated = self.publish_product(product["id"])
                activated.append(updated)
                success(f"Activated: {product['title']}")
            except Exception as e:
                error(f"Failed to activate {product['title']}: {e}")

        success(f"Activated {len(activated)}/{len(drafts)} draft products.")
        return activated

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def get_products_from_cache(self) -> List[dict]:
        cache_path = get_shopify_cache_path()
        if not os.path.exists(cache_path):
            with open(cache_path, "w") as file:
                json.dump({"accounts": []}, file, indent=4)

        with open(cache_path, "r") as file:
            parsed = json.load(file)
            accounts = parsed.get("accounts", [])
            for account in accounts:
                if account["id"] == self.account_uuid:
                    return account.get("products", [])
        return []

    def add_product_to_cache(self, product: dict) -> None:
        cache_path = get_shopify_cache_path()

        with open(cache_path, "r") as file:
            previous_json = json.load(file)
            accounts = previous_json.get("accounts", [])
            for account in accounts:
                if account["id"] == self.account_uuid:
                    account.setdefault("products", []).append(product)

            with open(cache_path, "w") as f:
                json.dump(previous_json, f, indent=4)
