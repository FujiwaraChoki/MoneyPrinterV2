"""SpotFinder web server — Flask API wrapping the scan pipeline."""

from __future__ import annotations

import threading
import os
import json
from dataclasses import asdict

from flask import Flask, jsonify, request, send_from_directory

from spotfinder.adapters.db import Database
from spotfinder.adapters.google_maps import GoogleMapsScraper
from spotfinder.adapters.http_client import HttpClient
from spotfinder.core.errors import SpotFinderError
from spotfinder.core.types import INDUSTRIES, ScanRequest, ScanStatus
from spotfinder.services.pipeline import Pipeline

app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)

# Ensure schema exists on startup
_init_db = Database()
_init_db.initialize()
_init_db.close()
del _init_db

# Track running scans
_active_scans: dict[str, str] = {}  # scan_id -> status message
_scan_lock = threading.Lock()


def _get_db() -> Database:
    """Create a fresh DB connection per request (SQLite thread safety)."""
    db = Database()
    db.initialize()
    return db


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/industries")
def list_industries():
    result = []
    for slug, profile in INDUSTRIES.items():
        result.append({
            "slug": slug,
            "name_en": profile.name_en,
            "name_es": profile.name_es,
            "tier": profile.tier,
            "avg_revenue_usd": profile.avg_revenue_usd,
            "gross_margin_pct": profile.gross_margin_pct,
            "website_adoption_pct": profile.website_adoption_pct,
            "search_terms_en": profile.search_terms_en,
            "search_terms_es": profile.search_terms_es,
        })
    return jsonify({"data": result})


@app.route("/api/scan", methods=["POST"])
def start_scan():
    body = request.get_json(force=True)
    location = (body.get("location") or "").strip()
    niche = (body.get("niche") or "").strip()
    country = (body.get("country") or "US").strip().upper()

    if not location:
        return jsonify({"error": {"code": "INVALID_LOCATION", "message": "Location is required"}}), 400
    if not niche:
        return jsonify({"error": {"code": "INVALID_NICHE", "message": "Niche is required"}}), 400

    scan = ScanRequest(
        location_query=location,
        niche=niche,
        country_code=country,
    )

    def run_pipeline(scan_id: str, scan_obj: ScanRequest):
        try:
            db = Database()
            db.initialize()
            scraper = GoogleMapsScraper()
            http_client = HttpClient()
            pipeline = Pipeline(db, scraper, http_client)
            with _scan_lock:
                _active_scans[scan_id] = "discovering"
            pipeline.run(scan_obj)
        except SpotFinderError:
            pass
        finally:
            with _scan_lock:
                _active_scans.pop(scan_id, None)

    thread = threading.Thread(
        target=run_pipeline,
        args=(scan.id, scan),
        daemon=True,
    )
    thread.start()

    return jsonify({"data": {"scan_id": scan.id, "status": "pending"}}), 202


@app.route("/api/scan/<scan_id>")
def get_scan_status(scan_id: str):
    db = _get_db()
    scan = db.get_scan(scan_id)
    if scan is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Scan not found"}}), 404
    return jsonify({"data": {
        "id": scan.id,
        "location": scan.location_query,
        "niche": scan.niche,
        "country": scan.country_code,
        "status": scan.status.value,
        "business_count": scan.business_count,
        "error_message": scan.error_message,
        "created_at": scan.created_at,
        "completed_at": scan.completed_at,
    }})


@app.route("/api/scan/<scan_id>/results")
def get_scan_results(scan_id: str):
    db = _get_db()
    scan = db.get_scan(scan_id)
    if scan is None:
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Scan not found"}}), 404

    scores = db.get_scores(scan_id, limit=200)
    businesses = db.get_businesses(scan_id)
    presences = db.get_digital_presences_by_scan(scan_id)

    biz_map = {b.id: b for b in businesses}
    dp_map = {p.business_id: p for p in presences}

    results = []
    for score in sorted(scores, key=lambda s: s.rank):
        biz = biz_map.get(score.business_id)
        if biz is None:
            continue
        dp = dp_map.get(biz.id)
        results.append({
            "rank": score.rank,
            "name": biz.name,
            "category": biz.category,
            "address": biz.address,
            "phone": biz.phone,
            "email": biz.email,
            "website_url": biz.website_url,
            "google_maps_url": biz.google_maps_url,
            "google_rating": biz.google_rating,
            "google_review_count": biz.google_review_count,
            "has_website": dp.has_website if dp else False,
            "has_ssl": dp.website_has_ssl if dp else None,
            "has_facebook": dp.has_facebook if dp else False,
            "has_instagram": dp.has_instagram if dp else False,
            "has_whatsapp": dp.has_whatsapp if dp else False,
            "has_online_booking": dp.has_online_booking if dp else False,
            "website_technology": dp.website_technology if dp else None,
            "digital_gap_score": score.digital_gap_score,
            "revenue_potential_score": score.revenue_potential_score,
            "accessibility_score": score.accessibility_score,
            "opportunity_score": score.opportunity_score,
            "rationale": score.scoring_rationale,
        })

    return jsonify({"data": results, "meta": {
        "scan_id": scan.id,
        "location": scan.location_query,
        "niche": scan.niche,
        "status": scan.status.value,
        "total": len(results),
    }})


@app.route("/api/scans")
def list_scans():
    db = _get_db()
    scans = db.list_scans(limit=50)
    return jsonify({"data": [{
        "id": s.id,
        "location": s.location_query,
        "niche": s.niche,
        "country": s.country_code,
        "status": s.status.value,
        "business_count": s.business_count,
        "created_at": s.created_at,
    } for s in scans]})


def main():
    app.run(host="0.0.0.0", port=5001, debug=False)


if __name__ == "__main__":
    main()
