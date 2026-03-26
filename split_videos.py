"""
split_videos.py
---------------
.mp klasöründeki PNG dosyalarını 10 gruba böler,
her gruptan ~30 saniyelik bir video üretir.
"""

import os
import sys
import glob
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from config import ROOT_DIR, get_threads, get_fonts_dir, get_font
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeAudioClip,
    concatenate_videoclips,
)
from moviepy.video.fx.all import crop
import moviepy.audio.fx.all as afx

TARGET_DURATION = 30   # saniye
NUM_VIDEOS      = 10
MP_DIR          = os.path.join(ROOT_DIR, ".mp")
OUT_DIR         = os.path.join(ROOT_DIR, "output_videos")
SONGS_DIR       = os.path.join(ROOT_DIR, "Songs")

os.makedirs(OUT_DIR, exist_ok=True)

# --- Görselleri topla ---
all_pngs = sorted(glob.glob(os.path.join(MP_DIR, "*.png")))
if not all_pngs:
    raise RuntimeError("Hiç PNG bulunamadı!")

print(f"[+] Toplam görsel: {len(all_pngs)}")

# --- Müzik dosyalarını bul ---
song_files = []
if os.path.isdir(SONGS_DIR):
    for ext in ("*.mp3", "*.wav", "*.m4a", "*.aac", "*.ogg"):
        song_files.extend(glob.glob(os.path.join(SONGS_DIR, ext)))

if song_files:
    print(f"[+] {len(song_files)} müzik dosyası bulundu.")
else:
    print("[!] Müzik bulunamadı — sessiz videolar üretilecek.")

# --- Görselleri 10 gruba böl ---
chunk_size = max(1, len(all_pngs) // NUM_VIDEOS)
groups = []
for i in range(NUM_VIDEOS):
    start = i * chunk_size
    # Son grup kalan tüm görselleri alır
    end = start + chunk_size if i < NUM_VIDEOS - 1 else len(all_pngs)
    group = all_pngs[start:end]
    if group:
        groups.append(group)

print(f"[+] {len(groups)} grup oluşturuldu (grup başına ortalama {chunk_size} görsel)")


def make_clip(image_path: str, duration: float):
    """Görseli 1080x1920 boyutuna getirir ve belirtilen süreyle döndürür."""
    clip = ImageClip(image_path).set_duration(duration).set_fps(30)
    w, h = clip.w, clip.h
    if round(w / h, 4) < 0.5625:
        clip = crop(clip, width=w, height=round(w / 0.5625),
                    x_center=w / 2, y_center=h / 2)
    else:
        clip = crop(clip, width=round(0.5625 * h), height=h,
                    x_center=w / 2, y_center=h / 2)
    return clip.resize((1080, 1920))


# --- Her grup için video üret ---
threads = get_threads()

for idx, group in enumerate(groups, start=1):
    print(f"\n[+] Video {idx}/{len(groups)} üretiliyor ({len(group)} görsel)...")

    img_dur = TARGET_DURATION / len(group)
    clips = [make_clip(p, img_dur) for p in group]
    video = concatenate_videoclips(clips).set_fps(30)

    # Sesi ekle
    if song_files:
        song_path = random.choice(song_files)
        song_clip = AudioFileClip(song_path).set_fps(44100)
        # 30 saniyelik kesit al (gerekirse döngüye al)
        if song_clip.duration < TARGET_DURATION:
            loops = int(TARGET_DURATION / song_clip.duration) + 1
            from moviepy.editor import concatenate_audioclips
            song_clip = concatenate_audioclips([song_clip] * loops)
        song_clip = song_clip.subclip(0, TARGET_DURATION)
        song_clip = song_clip.fx(afx.volumex, 0.15)
        video = video.set_audio(song_clip)

    out_path = os.path.join(OUT_DIR, f"video_{idx:02d}.mp4")
    video.write_videofile(out_path, threads=threads, logger=None)
    print(f"    [✓] Kaydedildi: {out_path}")

print(f"\n[✓] Tüm videolar tamamlandı → {OUT_DIR}")
