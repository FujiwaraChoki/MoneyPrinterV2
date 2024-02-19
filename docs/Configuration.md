# Configuration

All your configurations will be in a file in the root directory, called `config.json`, which is a copy of `config.example.json`. You can change the values in `config.json` to your liking.

## Values

- `verbose`: `boolean` - If `true`, the application will print out more information.
- `firefox_profile`: `string` - The path to your Firefox profile. This is used to use your Social Media Accounts without having to log in every time you run the application.
- `headless`: `boolean` - If `true`, the application will run in headless mode. This means that the browser will not be visible.
- `llm`: This will decide the Large Language Model MPV2 uses to generate tweets, scripts, image prompts and more. If left empty, the default model (`gpt35_turbo`) will be used. Here are your choices:
    * `gpt4`
    * `gpt35_turbo`
    * `llama2_7b`
    * `llama2_13b`
    * `llama2_70b`
    * `mixtral_8x7b`
- `image_prompt_llm`: `string` - The Large Language Model that will be used to generate image prompts. If left empty, the default model (`gpt35_turbo`) will be used. Here are your choices:
    * `gpt4`
    * `gpt35_turbo`
    * `llama2_7b`
    * `llama2_13b`
    * `llama2_70b`
    * `mixtral_8x7b`
- `twitter_language`: `string` - The language that will be used to generate & post tweets.
- `image_model`: `string` - What AI Model you want to use to generate images, here are your choices:
    * `v1`
    * `v2`
    * `v3` (DALL-E)
    * `lexica`
    * `prodia`
    * `simurg`
    * `animefy`
    * `raava`
    * `shonin`
- `threads`: `number` - The amount of threads that will be used to execute operations, e.g. writing to a file using MoviePy.
- `is_for_kids`: `boolean` - If `true`, the application will upload the video to YouTube Shorts as a video for kids.
- `google_maps_scraper`: `string` - The URL to the Google Maps scraper. This will be used to scrape Google Maps for local businesses. It is recommended to use the default value.
- `zip_url`: `string` - The URL to the ZIP file that contains the to be used Songs for the YouTube Shorts Automater.
- `email`: `object`:
    - `smtp_server`: `string` - Your SMTP server.
    - `smtp_port`: `number` - The port of your SMTP server.
    - `username`: `string` - Your email address.
    - `password`: `string` - Your email password.
- `google_maps_scraper_niche`: `string` - The niche you want to scrape Google Maps for.
- `scraper_timeout`: `number` - The timeout for the Google Maps scraper.
- `outreach_message_subject`: `string` - The subject of your outreach message. `{{COMPANY_NAME}}` will be replaced with the company name.
- `outreach_message_body_file`: `string` - The file that contains the body of your outreach message, should be HTML. `{{COMPANY_NAME}}` will be replaced with the company name.
- `assembly_ai_api_key`: `string` - Your Assembly AI API key. Get yours from [here](https://www.assemblyai.com/app/).
- `font`: `string` - The font that will be used to generate images. This should be a `.ttf` file in the `fonts/` directory.
- `imagemagick_path`: `string` - The path to the ImageMagick binary. This is used by MoviePy to manipulate images. Install ImageMagick from [here](https://imagemagick.org/script/download.php) and set the path to the `magick.exe` on Windows, or on Linux/MacOS the path to `convert` (usually /usr/bin/convert).

## Example

```json
{
  "verbose": true,
  "firefox_profile": "",
  "headless": false,
  "twitter_language": "English",
  "llm": "gpt4",
  "image_prompt_llm": "gpt35_turbo",
  "image_model": "prodia",
  "threads": 2,
  "zip_url": "",
  "is_for_kids": false,
  "google_maps_scraper": "https://github.com/gosom/google-maps-scraper/archive/refs/tags/v0.9.7.zip",
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "",
    "password": ""
  },
  "google_maps_scraper_niche": "",
  "scraper_timeout": 300,
  "outreach_message_subject": "I have a question...",
  "outreach_message_body_file": "outreach_message.html",
  "assembly_ai_api_key": "",
  "font": "bold_font.ttf",
  "imagemagick_path": "C:\\Program Files\\ImageMagick-7.1.0-Q16\\magick.exe"
}
```
