"""
This file contains all the constants used in the program.
"""
import g4f

TWITTER_TEXTAREA_CLASS = "public-DraftStyleDefault-block public-DraftStyleDefault-ltr"
TWITTER_POST_BUTTON_XPATH = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/div[3]/div/div[2]/div[1]/div/div/div/div[2]/div[2]/div[2]/div/div/div/div[3]"

OPTIONS = [
    "Do Cold Outreach on Local Businesses",
    "YouTube Shorts Automation",
    "Twitter Bot",
    "Quit"
]

TWITTER_OPTIONS = [
    "Post something",
    "Show all Posts",
    "Setup CRON Job",
    "Quit"
]

TWITTER_CRON_OPTIONS = [
    "Once a day",
    "Twice a day",
    "Thrice a day",
    "Quit"
]

YOUTUBE_OPTIONS = [
    "Upload Short",
    "Show all Shorts",
    "Setup CRON Job",
    "Quit"
]

YOUTUBE_CRON_OPTIONS = [
    "Once a day",
    "Twice a day",
    "Thrice a day",
    "Quit"
]

YOUTUBE_UPLOAD_BUTTON_XPATH = "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-uploads-file-picker/div/input"

YOUTUBE_TITLE_INPUT_XPATH = "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-ve/ytcp-video-metadata-editor/div/ytcp-video-metadata-editor-basics/div[1]/ytcp-video-title/ytcp-social-suggestions-textbox/ytcp-form-input-container/div[1]/div[2]/div/ytcp-social-suggestion-input/div"

YOUTUBE_DESCRIPTION_INPUT_XPATH = "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-ve/ytcp-video-metadata-editor/div/ytcp-video-metadata-editor-basics/div[2]/ytcp-video-description/div/ytcp-social-suggestions-textbox/ytcp-form-input-container/div[1]/div[2]/div/ytcp-social-suggestion-input/div"

YOUTUBE_NOT_MADE_FOR_KIDS_XPATH = "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-ve/ytcp-video-metadata-editor/div/ytcp-video-metadata-editor-basics/div[5]/ytkc-made-for-kids-select/div[4]/tp-yt-paper-radio-group/tp-yt-paper-radio-button[2]/div[2]/ytcp-ve"

YOUTUBE_NEXT_BUTTON_XPATH = "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[2]/div/div[2]/ytcp-button[2]/div"

YOUTUBE_SECOND_NEXT_BUTTON_XPATH = "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[2]/div/div[2]/ytcp-button[2]"

YOUTUBE_THIRD_NEXT_BUTTON_XPATH = "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[2]/div/div[2]/ytcp-button[2]"

YOUTUBE_PUBLIC_BUTTON_XPATH = "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-uploads-review/div[2]/div[1]/ytcp-video-visibility-select/div[2]/tp-yt-paper-radio-group/tp-yt-paper-radio-button[3]/div[1]/div[1]"

YOUTUBE_DONE_BUTTON_XPATH = "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[2]/div/div[2]/ytcp-button[3]"

def parse_model(model_name: str) -> any:
    if model_name == "gpt4":
        return g4f.models.gpt_4
    elif model_name == "gpt35_turbo":
        return g4f.models.gpt_35_turbo
    elif model_name == "llama2_7b":
        return g4f.models.llama2_7b
    elif model_name == "llama2_13b":
        return g4f.models.llama2_13b
    elif model_name == "llama2_70b":
        return g4f.models.llama2_70b
    elif model_name == "mixtral_8x7b":
        return g4f.models.mixtral_8x7b
    else:
        # Default model is gpt3.5-turbo
        return g4f.models.gpt_35_turbo
