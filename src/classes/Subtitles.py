import whisper
import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

class Subtitles:
    def __init__(self, model_name="base"):
        self.model = whisper.load_model(model_name)

    def generate_subtitles(self, video_path, output_path):
        
        result = self.model.transcribe(video_path)
        segments = result['segments'] 

        video = VideoFileClip(video_path)
        subtitle_clips = []

        for segment in segments:
            text = segment['text']
            start_time = segment['start']
            end_time = segment['end']
            duration = end_time - start_time

            txt_clip = TextClip(
                text, 
                fontsize=70, 
                color='yellow', 
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=2,
                method='caption',
                size=(video.w * 0.8, None)
            ).set_start(start_time).set_duration(duration).set_position(('center', video.h * 0.8))

            subtitle_clips.append(txt_clip)

        result_video = CompositeVideoClip([video] + subtitle_clips)
        
        result_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
        return output_path