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

from cache import get_shopify_cache_path
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

    # ------------------------------------------------------------------
    # LLM content generation
    # ------------------------------------------------------------------

    def generate_product_idea(self) -> str:
        completion = generate_text(
            f"You are a Shopify store product researcher. Suggest one specific, trending product idea "
            f"for a store in the '{self.niche}' niche. Return only the product name, nothing else."
        )
        completion = re.sub(r"[\"*]", "", completion).strip()
        if get_verbose():
            info(f"Product idea: {completion}")
        return completion

    def generate_product_listing(self, product_name: str) -> dict:
        prompt = (
            f"Generate a Shopify product listing for: \"{product_name}\"\n"
            f"Niche: {self.niche}\n\n"
            f"Return ONLY valid JSON with these exact keys:\n"
            f'{{"title": "...", "body_html": "...", "product_type": "...", '
            f'"tags": "tag1, tag2, tag3", "price": "29.99", '
            f'"seo_title": "...", "seo_description": "..."}}\n\n'
            f"The body_html should be compelling HTML product description (2-3 paragraphs). "
            f"The price should be realistic. Tags should be comma-separated."
        )
        raw = generate_text(prompt)

        # Extract JSON from the response
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if json_match:
            try:
                listing = json.loads(json_match.group())
                if get_verbose():
                    info(f"Generated listing for: {listing.get('title', product_name)}")
                return listing
            except json.JSONDecodeError:
                pass

        # Fallback if LLM didn't return valid JSON
        warning("LLM did not return valid JSON. Using generated text as description.")
        return {
            "title": product_name,
            "body_html": f"<p>{raw}</p>",
            "product_type": self.niche,
            "tags": self.niche,
            "price": "29.99",
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
            f"Professional product photography of {product_name}, "
            f"white background, studio lighting, e-commerce style, high quality"
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
    # Core workflow
    # ------------------------------------------------------------------

    def generate_and_publish(self, product_name: Optional[str] = None) -> dict:
        if product_name is None:
            product_name = self.generate_product_idea()

        info(f"Generating listing for: {product_name}")
        listing = self.generate_product_listing(product_name)

        price = listing.pop("price", "29.99")
        seo_title = listing.pop("seo_title", listing.get("title", ""))
        seo_description = listing.pop("seo_description", "")

        product_data = {
            "title": listing.get("title", product_name),
            "body_html": listing.get("body_html", ""),
            "product_type": listing.get("product_type", self.niche),
            "tags": listing.get("tags", ""),
            "status": "draft",
            "variants": [{"price": price, "inventory_management": None}],
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

        info("Publishing product to Shopify (as draft)...")
        created = self.create_product(product_data)

        if created.get("id"):
            success(f"Product created: {created['title']} (ID: {created['id']})")
            self.add_product_to_cache({
                "shopify_id": created["id"],
                "title": created["title"],
                "status": created.get("status", "draft"),
                "date": datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
            })
        else:
            error("Failed to create product on Shopify.")

        return created

    def bulk_generate(self, count: Optional[int] = None) -> List[dict]:
        if count is None:
            count = get_shopify_products_per_run()

        created_products = []
        for i in range(count):
            info(f"Generating product {i + 1}/{count}...")
            try:
                product = self.generate_and_publish()
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

            if len(body) < 100:
                info(f"Optimizing: {title}")
                new_listing = self.generate_product_listing(title)
                update_data = {
                    "body_html": new_listing.get("body_html", body),
                    "tags": new_listing.get("tags", product.get("tags", "")),
                }
                try:
                    updated = self.update_product(product["id"], update_data)
                    optimized.append(updated)
                    success(f"Optimized: {title}")
                except Exception as e:
                    error(f"Failed to optimize {title}: {e}")

        success(f"Optimized {len(optimized)} products.")
        return optimized

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
