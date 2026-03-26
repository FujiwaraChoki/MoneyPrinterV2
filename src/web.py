"""
web.py — Flask backend for MoneyPrinterV2 retro UI.
Run: python src/web.py
"""

import os
import sys
import json
import glob
import threading
import time

# Ensure src/ is on the path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, jsonify, request, send_from_directory
from config import ROOT_DIR, get_gemini_llm_api_key, get_gemini_llm_model, reload_config, _load_config
from cache import get_accounts, get_youtube_cache_path

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)

# ---------- State ----------
_generation_state = {
    "running": False,
    "step": "",
    "progress": 0,
    "error": None,
    "video_path": None,
}


# ---------- Pages ----------
@app.route("/")
def index():
    return render_template("index.html")


# ---------- API ----------
@app.route("/api/accounts")
def api_accounts():
    try:
        accounts = get_accounts("youtube")
        return jsonify(accounts)
    except Exception as e:
        return jsonify([])


@app.route("/api/videos")
def api_videos():
    """Return list of generated video files."""
    videos = []
    # Check output_videos/ and root for mp4 files
    for pattern in [
        os.path.join(ROOT_DIR, "output_video*.mp4"),
        os.path.join(ROOT_DIR, "output_videos", "*.mp4"),
    ]:
        for f in sorted(glob.glob(pattern)):
            stat = os.stat(f)
            videos.append({
                "name": os.path.basename(f),
                "path": f,
                "size_mb": round(stat.st_size / (1024 * 1024), 1),
                "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(stat.st_mtime)),
            })
    return jsonify(videos)


@app.route("/api/config")
def api_config():
    """Returns the full config.json for editing. (Local use only)"""
    config_path = os.path.join(ROOT_DIR, "config.json")
    try:
        with open(config_path, "r") as f:
            cfg = json.load(f)
        return jsonify(cfg)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/config", methods=["POST"])
def api_config_update():
    """Update config.json safely."""
    updates = request.json
    config_path = os.path.join(ROOT_DIR, "config.json")
    try:
        with open(config_path, "r") as f:
            cfg = json.load(f)
            
        # Update flat keys (handle nested ones like "email" if needed, but for now we do deep update)
        for k, v in updates.items():
            if isinstance(v, dict) and k in cfg and isinstance(cfg[k], dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
                
        with open(config_path, "w") as f:
            json.dump(cfg, f, indent=2)
            
        reload_config()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/generate", methods=["POST"])
def api_generate():
    """Start video generation in background thread."""
    if _generation_state["running"]:
        return jsonify({"error": "Generation already running"}), 409

    data = request.json or {}
    account_idx = data.get("account_index", 0)
    upload_video = data.get("upload_video", False)

    def run_generation():
        _generation_state.update(running=True, step="Initializing...", progress=5, error=None, video_path=None)
        try:
            from classes.YouTube import YouTube
            from classes.Tts import TTS

            accounts = get_accounts("youtube")
            if not accounts:
                raise RuntimeError("No YouTube accounts configured.")

            acc = accounts[account_idx]

            _generation_state.update(step="Creating YouTube instance...", progress=10)
            yt = YouTube(acc["id"], acc["nickname"], acc["firefox_profile"], acc["niche"], acc["language"])

            _generation_state.update(step="Generating topic...", progress=15)
            yt.generate_topic()

            _generation_state.update(step="Generating script...", progress=25)
            yt.generate_script()

            _generation_state.update(step="Generating metadata...", progress=35)
            yt.generate_metadata()

            _generation_state.update(step="Generating video search terms...", progress=40)
            yt.generate_video_search_terms()

            _generation_state.update(step="Downloading stock videos from Pexels...", progress=50)
            yt.fetch_stock_videos()

            _generation_state.update(step="Generating hook & CTA overlays...", progress=60)
            yt.generate_hook_text()
            yt.generate_cta_text()

            _generation_state.update(step="Generating speech...", progress=70)
            tts = TTS()
            yt.generate_script_to_speech(tts)

            _generation_state.update(step="Combining video...", progress=85)
            path = yt.combine()

            yt.video_path = os.path.abspath(path)

            if upload_video:
                _generation_state.update(step="Uploading to YouTube...", progress=90)
                try:
                    success = yt.upload_video()
                    if not success:
                        raise RuntimeError("YouTube upload failed.")
                except Exception as e:
                    raise RuntimeError(f"YouTube upload failed: {str(e)}")

            _generation_state.update(step="Done!", progress=100, video_path=yt.video_path)

        except Exception as e:
            _generation_state.update(step="Error", error=str(e))
            import traceback
            traceback.print_exc()
        finally:
            _generation_state["running"] = False

    t = threading.Thread(target=run_generation, daemon=True)
    t.start()
    return jsonify({"ok": True})


@app.route("/api/generation-status")
def api_generation_status():
    return jsonify(_generation_state)


@app.route("/api/assets")
def api_assets():
    """Count assets in .mp directory."""
    mp_dir = os.path.join(ROOT_DIR, ".mp")
    if not os.path.isdir(mp_dir):
        return jsonify({"images": 0, "audio": 0, "srt": 0})
    files = os.listdir(mp_dir)
    return jsonify({
        "images": len([f for f in files if f.endswith(".png")]),
        "audio": len([f for f in files if f.endswith(".wav")]),
        "srt": len([f for f in files if f.endswith(".srt")]),
    })


@app.route("/api/songs")
def api_songs():
    songs_dir = os.path.join(ROOT_DIR, "Songs")
    if not os.path.isdir(songs_dir):
        return jsonify([])
    songs = [f for f in os.listdir(songs_dir) if f.lower().endswith((".mp3", ".wav", ".m4a", ".aac", ".ogg"))]
    return jsonify(songs)


if __name__ == "__main__":
    print("\n🎮 MoneyPrinter V2 — Retro UI")
    print("   http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
