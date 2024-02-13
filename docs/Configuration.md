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

## Example

```json
{
    "verbose": true,
    "firefox_profile": "/home/user/.mozilla/firefox/your_profile",
    "headless": true,
    "llm": "gpt4",
    "twitter_language": "English",
    "image_model": "v1",
    "threads": 4
}
