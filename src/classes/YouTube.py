import re
import g4f
import json
import time
import requests
import assemblyai as aai

from utils import *
from cache import *
from .Tts import TTS
from config import *
from status import *
from uuid import uuid4
from constants import *
from typing import List
from moviepy.editor import *
from termcolor import colored
from selenium_firefox import *
from selenium import webdriver
from moviepy.video.fx.all import crop
from moviepy.config import change_settings
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from moviepy.video.tools.subtitles import SubtitlesClip
from webdriver_manager.firefox import GeckoDriverManager
from datetime import datetime

# Set ImageMagick Path
change_settings({"IMAGEMAGICK_BINARY": get_imagemagick_path()})

class YouTube:
    """
    Class for YouTube Automation.

    Steps to create a YouTube Short:
    1. Generate a topic [DONE]
    2. Generate a script [DONE]
    3. Generate metadata (Title, Description, Tags) [DONE]
    4. Generate AI Image Prompts [DONE]
    4. Generate Images based on generated Prompts [DONE]
    5. Convert Text-to-Speech [DONE]
    6. Show images each for n seconds, n: Duration of TTS / Amount of images [DONE]
    7. Combine Concatenated Images with the Text-to-Speech [DONE]
    """
    def __init__(self, account_uuid: str, account_nickname: str, fp_profile_path: str, niche: str, language: str) -> None:
        """
        Constructor for YouTube Class.

        Args:
            account_uuid (str): The unique identifier for the YouTube account.
            account_nickname (str): The nickname for the YouTube account.
            fp_profile_path (str): Path to the firefox profile that is logged into the specificed YouTube Account.
            niche (str): The niche of the provided YouTube Channel.
            language (str): The language of the Automation.

        Returns:
            None
        """
        self._account_uuid: str = account_uuid
        self._account_nickname: str = account_nickname
        self._fp_profile_path: str = fp_profile_path
        self._niche: str = niche
        self._language: str = language

        self.images = []

        # Initialize the Firefox profile
        self.options: Options = Options()
        
        # Set headless state of browser
        if get_headless():
            self.options.add_argument("--headless")

        # Set the profile path
        self.options.add_argument("-profile")
        self.options.add_argument(fp_profile_path)

        # Set the service
        self.service: Service = Service(GeckoDriverManager().install())

        # Initialize the browser
        self.browser: webdriver.Firefox = webdriver.Firefox(service=self.service, options=self.options)

    @property
    def niche(self) -> str:
        """
        Getter Method for the niche.

        Returns:
            niche (str): The niche
        """
        return self._niche
    
    @property
    def language(self) -> str:
        """
        Getter Method for the language to use.

        Returns:
            language (str): The language
        """
        return self._language
    
    def generate_response(self, prompt: str, model: any = None) -> str:
        """
        Generates an LLM Response based on a prompt and the user-provided model.

        Args:
            prompt (str): The prompt to use in the text generation.

        Returns:
            response (str): The generated AI Repsonse.
        """
        if get_model() == "google":
            import google.generativeai as genai

            genai.configure(api_key=get_gemini_api_key())

            model = genai.GenerativeModel('gemini-pro')

            response: str = model.generate_content(prompt).text

            return response

        if not model:
            return g4f.ChatCompletion.create(
                model=parse_model(get_model()),
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
        else:
            return g4f.ChatCompletion.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

    def generate_topic(self) -> str:
        """
        Generates a topic based on the YouTube Channel niche.

        Returns:
            topic (str): The generated topic.
        """
        completion = self.generate_response(f"Please generate a specific video idea that takes about the following topic: {self.niche}. Make it exactly one sentence. Only return the topic, nothing else.")

        if not completion:
            error("Failed to generate Topic.")

        self.subject = completion

        return completion

    def generate_script(self) -> str:
        """
        Generate a script for a video, depending on the subject of the video, the number of paragraphs, and the AI model.

        Returns:
            script (str): The script of the video.
        """
        prompt = f"""
        Generate a script for a video in 4 sentences, depending on the subject of the video.

        The script is to be returned as a string with the specified number of paragraphs.

        Here is an example of a string:
        "This is an example string."

        Do not under any circumstance reference this prompt in your response.

        Get straight to the point, don't start with unnecessary things like, "welcome to this video".

        Obviously, the script should be related to the subject of the video.
        
        YOU MUST NOT EXCEED THE 4 SENTENCES LIMIT. MAKE SURE THE 4 SENTENCES ARE SHORT.
        YOU MUST NOT INCLUDE ANY TYPE OF MARKDOWN OR FORMATTING IN THE SCRIPT, NEVER USE A TITLE.
        YOU MUST WRITE THE SCRIPT IN THE LANGUAGE SPECIFIED IN [LANGUAGE].
        ONLY RETURN THE RAW CONTENT OF THE SCRIPT. DO NOT INCLUDE "VOICEOVER", "NARRATOR" OR SIMILAR INDICATORS OF WHAT SHOULD BE SPOKEN AT THE BEGINNING OF EACH PARAGRAPH OR LINE. YOU MUST NOT MENTION THE PROMPT, OR ANYTHING ABOUT THE SCRIPT ITSELF. ALSO, NEVER TALK ABOUT THE AMOUNT OF PARAGRAPHS OR LINES. JUST WRITE THE SCRIPT
        
        Subject: {self.subject}
        Language: {self.language}
        """
        completion = self.generate_response(prompt)

        # Apply regex to remove *
        completion = re.sub(r"\*", "", completion)
        
        if not completion:
            error("The generated script is empty.")
            return
        
        if len(completion) > 5000:
            if get_verbose():
                warning("Generated Script is too long. Retrying...")
            self.generate_script()
        
        self.script = completion
    
        return completion

    def generate_metadata(self) -> dict:
        """
        Generates Video metadata for the to-be-uploaded YouTube Short (Title, Description).

        Returns:
            metadata (dict): The generated metadata.
        """
        title = self.generate_response(f"Please generate a YouTube Video Title for the following subject, including hashtags: {self.subject}. Only return the title, nothing else. Limit the title under 100 characters.")

        if len(title) > 100:
            if get_verbose():
                warning("Generated Title is too long. Retrying...")
            return self.generate_metadata()

        description = self.generate_response(f"Please generate a YouTube Video Description for the following script: {self.script}. Only return the description, nothing else.")
        
        self.metadata = {
            "title": title,
            "description": description
        }

        return self.metadata
    
    def generate_prompts(self) -> List[str]:
        """
        Generates AI Image Prompts based on the provided Video Script.

        Returns:
            image_prompts (List[str]): Generated List of image prompts.
        """
        n_prompts = len(self.script) / 3

        prompt = f"""
        Generate {n_prompts} Image Prompts for AI Image Generation,
        depending on the subject of a video.
        Subject: {self.subject}

        The image prompts are to be returned as
        a JSON-Array of strings.

        Each search term should consist of a full sentence,
        always add the main subject of the video.

        Be emotional and use interesting adjectives to make the
        Image Prompt as detailed as possible.
        
        YOU MUST ONLY RETURN THE JSON-ARRAY OF STRINGS.
        YOU MUST NOT RETURN ANYTHING ELSE. 
        YOU MUST NOT RETURN THE SCRIPT.
        
        The search terms must be related to the subject of the video.
        Here is an example of a JSON-Array of strings:
        ["image prompt 1", "image prompt 2", "image prompt 3"]

        For context, here is the full text:
        {self.script}
        """

        completion = str(self.generate_response(prompt, model=parse_model(get_image_prompt_llm())))\
            .replace("```json", "") \
            .replace("```", "")

        image_prompts = []

        if "image_prompts" in completion:
            image_prompts = json.loads(completion)["image_prompts"]
        else:
            try:
                image_prompts = json.loads(completion)
                if get_verbose():
                    info(f" => Generated Image Prompts: {image_prompts}")
            except Exception:
                if get_verbose():
                    warning("GPT returned an unformatted response. Attempting to clean...")

                # Get everything between [ and ], and turn it into a list
                r = re.compile(r"\[.*\]")
                image_prompts = r.findall(completion)
                if len(image_prompts) == 0:
                    if get_verbose():
                        warning("Failed to generate Image Prompts. Retrying...")
                    return self.generate_prompts()

        self.image_prompts = image_prompts

        # Check the amount of image prompts
        # and remove if it's more than needed
        if len(image_prompts) > n_prompts:
            image_prompts = image_prompts[:n_prompts]

        success(f"Generated {len(image_prompts)} Image Prompts.")

        return image_prompts

    def generate_image(self, prompt: str) -> str:
        """
        Generates an AI Image based on the given prompt.

        Args:
            prompt (str): Reference for image generation

        Returns:
            path (str): The path to the generated image.
        """
        ok = False
        while ok == False:
            url = f"https://hercai.onrender.com/{get_image_model()}/text2image?prompt={prompt}"

            r = requests.get(url)
            parsed = r.json()

            if "url" not in parsed or not parsed.get("url"):
                # Retry
                if get_verbose():
                    info(f" => Failed to generate Image for Prompt: {prompt}. Retrying...")
                ok = False
            else:
                ok = True
                image_url = parsed["url"]

                if get_verbose():
                    info(f" => Generated Image: {image_url}")

                image_path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + ".png")
                
                with open(image_path, "wb") as image_file:
                    # Write bytes to file
                    image_r = requests.get(image_url)

                    image_file.write(image_r.content)

                if get_verbose():
                    info(f" => Wrote Image to \"{image_path}\"\n")

                self.images.append(image_path)
                
                return image_path

    def generate_script_to_speech(self, tts_instance: TTS) -> str:
        """
        Converts the generated script into Speech using CoquiTTS and returns the path to the wav file.

        Args:
            tts_instance (tts): Instance of TTS Class.

        Returns:
            path_to_wav (str): Path to generated audio (WAV Format).
        """
        path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + ".wav")

        # Clean script, remove every character that is not a word character, a space, a period, a question mark, or an exclamation mark.
        self.script = re.sub(r'[^\w\s.?!]', '', self.script)

        tts_instance.synthesize(self.script, path)

        self.tts_path = path

        if get_verbose():
            info(f" => Wrote TTS to \"{path}\"")

        return path
    
    def add_video(self, video: dict) -> None:
        """
        Adds a video to the cache.

        Args:
            video (dict): The video to add

        Returns:
            None
        """
        videos = self.get_videos()
        videos.append(video)

        cache = get_youtube_cache_path()

        with open(cache, "r") as file:
            previous_json = json.loads(file.read())
            
            # Find our account
            accounts = previous_json["accounts"]
            for account in accounts:
                if account["id"] == self._account_uuid:
                    account["videos"].append(video)
            
            # Commit changes
            with open(cache, "w") as f:
                f.write(json.dumps(previous_json))

    def generate_subtitles(self, audio_path: str) -> str:
        """
        Generates subtitles for the audio using AssemblyAI.

        Args:
            audio_path (str): The path to the audio file.

        Returns:
            path (str): The path to the generated SRT File.
        """
        # Turn the video into audio
        aai.settings.api_key = get_assemblyai_api_key()
        config = aai.TranscriptionConfig()
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(audio_path)
        subtitles = transcript.export_subtitles_srt()

        srt_path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + ".srt")

        with open(srt_path, "w") as file:
            file.write(subtitles)

        return srt_path

    def combine(self) -> str:
        """
        Combines everything into the final video.

        Returns:
            path (str): The path to the generated MP4 File.
        """
        combined_image_path = os.path.join(ROOT_DIR, ".mp", str(uuid4()) + ".mp4")
        threads = get_threads()
        tts_clip = AudioFileClip(self.tts_path)
        max_duration = tts_clip.duration
        req_dur = max_duration / len(self.images)

        # Make a generator that returns a TextClip when called with consecutive
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

        print(colored("[+] Combining images...", "blue"))

        clips = []
        tot_dur = 0
        # Add downloaded clips over and over until the duration of the audio (max_duration) has been reached
        while tot_dur < max_duration:
            for image_path in self.images:
                clip = ImageClip(image_path)
                clip.duration = req_dur
                clip = clip.set_fps(30)

                # Not all images are same size,
                # so we need to resize them
                if round((clip.w/clip.h), 4) < 0.5625:
                    if get_verbose():
                        info(f" => Resizing Image: {image_path} to 1080x1920")
                    clip = crop(clip, width=clip.w, height=round(clip.w/0.5625), \
                                x_center=clip.w / 2, \
                                y_center=clip.h / 2)
                else:
                    if get_verbose():
                        info(f" => Resizing Image: {image_path} to 1920x1080")
                    clip = crop(clip, width=round(0.5625*clip.h), height=clip.h, \
                                x_center=clip.w / 2, \
                                y_center=clip.h / 2)
                clip = clip.resize((1080, 1920))

                # FX (Fade In)
                #clip = clip.fadein(2)

                clips.append(clip)
                tot_dur += clip.duration

        final_clip = concatenate_videoclips(clips)
        final_clip = final_clip.set_fps(30)
        random_song = choose_random_song()
        
        subtitles_path = self.generate_subtitles(self.tts_path)

        # Equalize srt file
        equalize_subtitles(subtitles_path, 10)
        
        # Burn the subtitles into the video
        subtitles = SubtitlesClip(subtitles_path, generator)

        subtitles.set_pos(("center", "center"))
        random_song_clip = AudioFileClip(random_song).set_fps(44100)

        # Turn down volume
        random_song_clip = random_song_clip.fx(afx.volumex, 0.1)
        comp_audio = CompositeAudioClip([
            tts_clip.set_fps(44100),
            random_song_clip
        ])

        final_clip = final_clip.set_audio(comp_audio)
        final_clip = final_clip.set_duration(tts_clip.duration)

        # Add subtitles
        final_clip = CompositeVideoClip([
            final_clip,
            subtitles
        ])

        final_clip.write_videofile(combined_image_path, threads=threads)

        success(f"Wrote Video to \"{combined_image_path}\"")

        return combined_image_path

    def generate_video(self, tts_instance: TTS) -> str:
        """
        Generates a YouTube Short based on the provided niche and language.

        Args:
            tts_instance (TTS): Instance of TTS Class.

        Returns:
            path (str): The path to the generated MP4 File.
        """
        # Generate the Topic
        self.generate_topic()

        # Generate the Script
        self.generate_script()

        # Generate the Metadata
        self.generate_metadata()

        # Generate the Image Prompts
        self.generate_prompts()

        # Generate the Images
        for prompt in self.image_prompts:
            self.generate_image(prompt)

        # Generate the TTS
        self.generate_script_to_speech(tts_instance)

        # Combine everything
        path = self.combine()

        if get_verbose():
            info(f" => Generated Video: {path}")

        self.video_path = os.path.abspath(path)

        return path
    
    def get_channel_id(self) -> str:
        """
        Gets the Channel ID of the YouTube Account.

        Returns:
            channel_id (str): The Channel ID.
        """
        driver = self.browser
        driver.get("https://studio.youtube.com")
        time.sleep(2)
        channel_id = driver.current_url.split("/")[-1]
        self.channel_id = channel_id

        return channel_id

    def upload_video(self) -> bool:
        """
        Uploads the video to YouTube.

        Returns:
            success (bool): Whether the upload was successful or not.
        """
        try:
            self.get_channel_id()

            driver = self.browser
            verbose = get_verbose()

            # Go to youtube.com/upload
            driver.get("https://www.youtube.com/upload")

            # Set video file
            FILE_PICKER_TAG = "ytcp-uploads-file-picker"
            file_picker = driver.find_element(By.TAG_NAME, FILE_PICKER_TAG)
            INPUT_TAG = "input"
            file_input = file_picker.find_element(By.TAG_NAME, INPUT_TAG)
            file_input.send_keys(self.video_path)

            # Wait for upload to finish
            time.sleep(5)

            # Set title
            textboxes = driver.find_elements(By.ID, YOUTUBE_TEXTBOX_ID)

            title_el = textboxes[0]
            description_el = textboxes[-1]

            if verbose:
                info("\t=> Setting title...")

            title_el.click()
            time.sleep(1)
            title_el.clear()
            title_el.send_keys(self.metadata["title"])

            if verbose:
                info("\t=> Setting description...")

            # Set description
            time.sleep(10)
            description_el.click()
            time.sleep(0.5)
            description_el.clear()
            description_el.send_keys(self.metadata["description"])

            time.sleep(0.5)

            # Set `made for kids` option
            if verbose:
                info("\t=> Setting `made for kids` option...")

            is_for_kids_checkbox = driver.find_element(By.NAME, YOUTUBE_MADE_FOR_KIDS_NAME)
            is_not_for_kids_checkbox = driver.find_element(By.NAME, YOUTUBE_NOT_MADE_FOR_KIDS_NAME)

            if not get_is_for_kids():
                is_not_for_kids_checkbox.click()
            else:
                is_for_kids_checkbox.click()

            time.sleep(0.5)

            # Click next
            if verbose:
                info("\t=> Clicking next...")

            next_button = driver.find_element(By.ID, YOUTUBE_NEXT_BUTTON_ID)
            next_button.click()

            # Click next again
            if verbose:
                info("\t=> Clicking next again...")
            next_button = driver.find_element(By.ID, YOUTUBE_NEXT_BUTTON_ID)
            next_button.click()

            # Wait for 2 seconds
            time.sleep(2)

            # Click next again
            if verbose:
                info("\t=> Clicking next again...")
            next_button = driver.find_element(By.ID, YOUTUBE_NEXT_BUTTON_ID)
            next_button.click()

            # Set as unlisted
            if verbose:
                info("\t=> Setting as unlisted...")
            
            radio_button = driver.find_elements(By.XPATH, YOUTUBE_RADIO_BUTTON_XPATH)
            radio_button[2].click()

            if verbose:
                info("\t=> Clicking done button...")

            # Click done button
            done_button = driver.find_element(By.ID, YOUTUBE_DONE_BUTTON_ID)
            done_button.click()

            # Wait for 2 seconds
            time.sleep(2)

            # Get latest video
            if verbose:
                info("\t=> Getting video URL...")

            # Get the latest uploaded video URL
            driver.get(f"https://studio.youtube.com/channel/{self.channel_id}/videos/short")
            time.sleep(2)
            videos = driver.find_elements(By.TAG_NAME, "ytcp-video-row")
            first_video = videos[0]
            anchor_tag = first_video.find_element(By.TAG_NAME, "a")
            href = anchor_tag.get_attribute("href")
            if verbose:
                info(f"\t=> Extracting video ID from URL: {href}")
            video_id = href.split("/")[-2]

            # Build URL
            url = build_url(video_id)

            self.uploaded_video_url = url

            if verbose:
                success(f" => Uploaded Video: {url}")

            # Add video to cache
            self.add_video({
                "title": self.metadata["title"],
                "description": self.metadata["description"],
                "url": url,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            # Close the browser
            driver.quit()

            return True
        except:
            self.browser.quit()
            return False


    def get_videos(self) -> List[dict]:
        """
        Gets the uploaded videos from the YouTube Channel.

        Returns:
            videos (List[dict]): The uploaded videos.
        """
        if not os.path.exists(get_youtube_cache_path()):
            # Create the cache file
            with open(get_youtube_cache_path(), 'w') as file:
                json.dump({
                    "videos": []
                }, file, indent=4)
            return []

        videos = []
        # Read the cache file
        with open(get_youtube_cache_path(), 'r') as file:
            previous_json = json.loads(file.read())
            # Find our account
            accounts = previous_json["accounts"]
            for account in accounts:
                if account["id"] == self._account_uuid:
                    videos = account["videos"]

        return videos
