"""
add_subtitles.py
----------------
Mevcut output_video.mp4 üzerine WAV'dan otomatik altyazı üretip yazar.
Çıktı: output_video_subtitled.mp4
"""

import os
import sys
import glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from config import (
    ROOT_DIR, get_threads, get_fonts_dir, get_font,
    get_whisper_model, get_whisper_device, get_whisper_compute_type,
    equalize_subtitles, get_imagemagick_path,
)
from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": get_imagemagick_path()})

MP_DIR     = os.path.join(ROOT_DIR, ".mp")
VIDEO_IN   = os.path.join(ROOT_DIR, "output_video.mp4")
VIDEO_OUT  = os.path.join(ROOT_DIR, "output_video_subtitled.mp4")
SRT_PATH   = os.path.join(MP_DIR, "subtitles.srt")

# --- WAV dosyasını bul ---
wav_files = sorted(glob.glob(os.path.join(MP_DIR, "*.wav")))
if not wav_files:
    raise RuntimeError("WAV dosyası bulunamadı! (.mp klasöründe olmalı)")
wav_path = wav_files[0]
print(f"[+] Ses dosyası: {wav_path}")

# --- Whisper ile transkript oluştur (SRT yoksa) ---
if os.path.exists(SRT_PATH):
    print(f"[+] SRT zaten mevcut, Whisper atlanıyor: {SRT_PATH}")
else:
    print("[+] Altyazı üretiliyor (Whisper)...")

    from faster_whisper import WhisperModel

    whisper_model = WhisperModel(
        get_whisper_model(),
        device=get_whisper_device(),
        compute_type=get_whisper_compute_type(),
    )
    segments, _ = whisper_model.transcribe(wav_path, vad_filter=True)


    def fmt_ts(seconds: float) -> str:
        ms = max(0, int(round(seconds * 1000)))
        h  = ms // 3600000
        m  = (ms % 3600000) // 60000
        s  = (ms % 60000) // 1000
        ms = ms % 1000
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


    lines = []
    for idx, seg in enumerate(segments, start=1):
        text = str(seg.text).strip()
        if not text:
            continue
        lines.append(str(idx))
        lines.append(f"{fmt_ts(seg.start)} --> {fmt_ts(seg.end)}")
        lines.append(text)
        lines.append("")

    with open(SRT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[+] SRT oluşturuldu: {SRT_PATH}")

    # Altyazıları eşitle (max 10 karakter/satır)
    equalize_subtitles(SRT_PATH, 10)

# --- Altyazıyı videoya yaz ---
print("[+] Altyazı videoya işleniyor...")

from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip
from moviepy.video.tools.subtitles import SubtitlesClip

font_path = os.path.join(get_fonts_dir(), get_font())

generator = lambda txt: TextClip(
    txt,
    font=font_path,
    fontsize=120,
    color="#FFFF00",
    stroke_color="black",
    stroke_width=8,
    size=(1080, 1920),
    method="caption",
)

video = VideoFileClip(VIDEO_IN)
subtitles = SubtitlesClip(SRT_PATH, generator)

# Videonun üstüne yerleştir (yatay merkez, dikey üst 1/4)
subtitles = subtitles.set_pos(("center", 80))

final = CompositeVideoClip([video, subtitles])
final = final.set_duration(video.duration)

final.write_videofile(
    VIDEO_OUT,
    threads=get_threads(),
    codec="libx264",
    audio_codec="aac",
)

print(f"\n[✓] Tamamlandı: {VIDEO_OUT}")
