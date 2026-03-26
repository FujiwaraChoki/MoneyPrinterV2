"""
resume_combine.py
-----------------
Mevcut .mp klasöründeki PNG ve WAV dosyalarını kullanarak
doğrudan video birleştirme (combine) adımını çalıştırır.
Böylece API'ye tekrar request atmak gerekmez.
"""

import os
import sys
import glob

# src dizinini path'e ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from config import ROOT_DIR, get_threads, get_fonts_dir, get_font, get_verbose, equalize_subtitles
from status import info, warning, success, error
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeAudioClip,
    CompositeVideoClip, concatenate_videoclips,
    AudioFileClip,
)
from moviepy.video.fx.all import crop
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy import audio as afx
from moviepy.editor import TextClip
import moviepy.audio.fx.all as afx
from uuid import uuid4

MP_DIR = os.path.join(ROOT_DIR, ".mp")

# --- Dosyaları bul ---
png_files = sorted(glob.glob(os.path.join(MP_DIR, "*.png")))
wav_files = sorted(glob.glob(os.path.join(MP_DIR, "*.wav")))

if not png_files:
    raise RuntimeError("Hiç PNG dosyası bulunamadı!")
if not wav_files:
    raise RuntimeError("Hiç WAV dosyası bulunamadı!")

tts_path = wav_files[0]
images = png_files

print(f"[+] Kullanılacak TTS: {tts_path}")
print(f"[+] Kullanılacak görsel sayısı: {len(images)}")

# --- Combine ---
output_path = os.path.join(ROOT_DIR, "output_video.mp4")
threads = get_threads()

tts_clip = AudioFileClip(tts_path)
max_duration = tts_clip.duration
req_dur = max_duration / len(images)

generator = lambda txt: TextClip(
    txt,
    font=os.path.join(get_fonts_dir(), get_font()),
    fontsize=100,
    color="#FFFF00",
    stroke_color="black",
    stroke_width=5,
    size=(1080, 1920),
    method="caption",
)

print("[+] Görseller birleştiriliyor...")

clips = []
tot_dur = 0
while tot_dur < max_duration:
    for image_path in images:
        clip = ImageClip(image_path)
        clip.duration = req_dur
        clip = clip.set_fps(30)

        if round((clip.w / clip.h), 4) < 0.5625:
            clip = crop(
                clip,
                width=clip.w,
                height=round(clip.w / 0.5625),
                x_center=clip.w / 2,
                y_center=clip.h / 2,
            )
        else:
            clip = crop(
                clip,
                width=round(0.5625 * clip.h),
                height=clip.h,
                x_center=clip.w / 2,
                y_center=clip.h / 2,
            )

        clip = clip.resize((1080, 1920))
        clips.append(clip)
        tot_dur += clip.duration
        if tot_dur >= max_duration:
            break
    if tot_dur >= max_duration:
        break

final_clip = concatenate_videoclips(clips)
final_clip = final_clip.set_fps(30)

# Altyazı (varsa)
srt_files = sorted(glob.glob(os.path.join(MP_DIR, "*.srt")))
subtitles = None
if srt_files:
    try:
        equalize_subtitles(srt_files[0], 10)
        subtitles = SubtitlesClip(srt_files[0], generator)
        subtitles.set_pos(("center", "center"))
    except Exception as e:
        print(f"[!] Altyazı yüklenemedi, devam ediliyor: {e}")

# Arka plan müziği (opsiyonel)
songs_dir = os.path.join(ROOT_DIR, "Songs")
song_files = []
if os.path.isdir(songs_dir):
    for ext in ("*.mp3", "*.wav", "*.m4a", "*.aac", "*.ogg"):
        song_files.extend(glob.glob(os.path.join(songs_dir, ext)))

if song_files:
    import random
    song = random.choice(song_files)
    song_clip = AudioFileClip(song).set_fps(44100)
    song_clip = song_clip.fx(afx.volumex, 0.1)
    comp_audio = CompositeAudioClip([tts_clip.set_fps(44100), song_clip])
    print(f"[+] Arka plan müziği: {os.path.basename(song)}")
else:
    comp_audio = tts_clip.set_fps(44100)
    print("[!] Arka plan müziği bulunamadı, sadece TTS kullanılıyor.")

final_clip = final_clip.set_audio(comp_audio)
final_clip = final_clip.set_duration(tts_clip.duration)

if subtitles is not None:
    final_clip = CompositeVideoClip([final_clip, subtitles])

print(f"[+] Video yazılıyor: {output_path}")
final_clip.write_videofile(output_path, threads=threads)
print(f"[✓] Video tamamlandı: {output_path}")
