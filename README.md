# MoneyPrinter V2

Sponsored by Post Bridge

<a href="https://www.post-bridge.com/?ref=moneyprinter">
  <img src="docs/repo/PostBridgeBanner.png" alt="Post Bridge integration banner" width="720" />
</a>


[![madewithlove](https://img.shields.io/badge/made_with-%E2%9D%A4-red?style=for-the-badge&labelColor=orange)](https://github.com/FujiwaraChoki/MoneyPrinterV2)

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donate-brightgreen?logo=buymeacoffee)](https://www.buymeacoffee.com/fujicodes)
[![GitHub license](https://img.shields.io/github/license/FujiwaraChoki/MoneyPrinterV2?style=for-the-badge)](https://github.com/FujiwaraChoki/MoneyPrinterV2/blob/main/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/FujiwaraChoki/MoneyPrinterV2?style=for-the-badge)](https://github.com/FujiwaraChoki/MoneyPrinterV2/issues)
[![GitHub stars](https://img.shields.io/github/stars/FujiwaraChoki/MoneyPrinterV2?style=for-the-badge)](https://github.com/FujiwaraChoki/MoneyPrinterV2/stargazers)
[![Discord](https://img.shields.io/discord/1134848537704804432?style=for-the-badge)](https://dsc.gg/fuji-community)

An Application that automates the process of making money online.
MPV2 (MoneyPrinter Version 2) is, as the name suggests, the second version of the MoneyPrinter project. It is a complete rewrite of the original project, with a focus on a wider range of features and a more modular architecture.

> **Note:** MPV2 targets Python 3.12 and uses OpenRouter for text generation. No local model server is required.
> Watch the YouTube video [here](https://youtu.be/wAZ_ZSuIqfk)

## Features

- [x] Twitter Bot (with CRON Jobs => `scheduler`)
- [x] YouTube Shorts Automator (with CRON Jobs => `scheduler`)
- [x] Affiliate Marketing (Amazon + Twitter)
- [x] Find local businesses & cold outreach
- [x] Etsy digital products workflow for planner, tracker, and worksheet listings

## Versions

MoneyPrinter has different versions for multiple languages developed by the community for the community. Here are some known versions:

- Chinese: [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo)

If you would like to submit your own version/fork of MoneyPrinter, please open an issue describing the changes you made to the fork.

## Installation

> ⚠️ If you are planning to reach out to scraped businesses per E-Mail, please first install the [Go Programming Language](https://golang.org/).

### Manual setup

```bash
git clone https://github.com/FujiwaraChoki/MoneyPrinterV2.git
cd MoneyPrinterV2

cp config.example.json config.json

python3.12 -m venv venv
```

Activate the virtual environment:

- Windows (PowerShell): `.\venv\Scripts\Activate.ps1`
- macOS / Linux: `source venv/bin/activate`

Then install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Then update `config.json` with the values your workflow needs. At minimum, configure:

- `openrouter_api_key`
- `openrouter_model`

`openrouter_base_url` is optional and defaults to `https://openrouter.ai/api/v1`.
You can also provide `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` as fallbacks, but the app still expects an OpenRouter-backed setup.

### macOS convenience setup

```bash
bash scripts/setup_local.sh
```

`scripts/setup_local.sh` is a convenience script for local development. It will:

- create `config.json` from `config.example.json` when needed
- create `venv/` if it does not exist
- install Python dependencies
- install a `money` launcher into `~/.local/bin`
- seed local defaults such as `openrouter_base_url`, `imagemagick_path`, and a detected Firefox profile when available
- run `scripts/preflight_local.py`

It does **not** provision OpenRouter credentials or choose a model for you. You still need to set `openrouter_api_key` and `openrouter_model` before starting the CLI. If you want `scripts/preflight_local.py` to pass, also configure Nano Banana 2 credentials (`nanobanana2_api_key` or `GEMINI_API_KEY`) and make sure the selected STT provider dependencies are installed.

## Usage

Run everything from the project root:

```bash
bash scripts/setup_local.sh
money
```

If you prefer the manual path, this still works:

```bash
source venv/bin/activate
python scripts/preflight_local.py
python src/main.py
```

`python scripts/preflight_local.py` validates more than OpenRouter: it also checks ImageMagick, Firefox profile, Nano Banana 2 credentials, and local Whisper imports when `stt_provider` is `local_whisper`.

A minimal OpenRouter-backed text-generation setup looks like this:

```json
{
  "openrouter_api_key": "your-openrouter-api-key",
  "openrouter_model": "google/gemma-4-26b-a4b-it",
  "openrouter_fallback_models": [
    "google/gemma-4-31b-it",
    "qwen/qwen3.6-plus:free"
  ],
  "openrouter_base_url": "https://openrouter.ai/api/v1"
}
```

Recommended low-cost text setup for this repo:

- primary: `google/gemma-4-26b-a4b-it`
- first fallback: `google/gemma-4-31b-it`
- second fallback: `qwen/qwen3.6-plus:free`

You can also set fallbacks through `OPENROUTER_FALLBACK_MODELS` as a comma-separated list.

If you prefer environment fallbacks for local testing:

```bash
export OPENROUTER_API_KEY="your-openrouter-api-key"
export OPENROUTER_MODEL="openai/gpt-4.1-mini"
source venv/bin/activate
python scripts/preflight_local.py
python src/main.py
```

### Etsy workflow

Choose `Etsy Digital Products` from the main menu to start the Etsy pipeline.

The current MVP flow:

- researches a planner, tracker, or worksheet opportunity
- generates a normalized product spec
- renders a PDF plus preview image
- creates five PNG listing mockups
- writes seller-ready listing files for titles, description, tags, and a checklist

Outputs are stored under `.mp/etsy/<timestamp>-<slug>/` with separate `artifacts/`, `product/`, `mockups/`, and `listing/` folders. The CLI also supports resuming incomplete Etsy runs from the first unfinished stage.

## Documentation

All relevant documents can be found [here](docs/).

## Scripts

For easier usage, there are some scripts in the `scripts` directory that can be used to directly access the core functionality of MPV2 without the need for user interaction.

All scripts need to be run from the root directory of the project, e.g. `bash scripts/upload_video.sh`.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us. Check out [docs/Roadmap.md](docs/Roadmap.md) for a list of features that need to be implemented.

## Code of Conduct

Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details on our code of conduct, and the process for submitting pull requests to us.

## License

MoneyPrinterV2 is licensed under `Affero General Public License v3.0`. See [LICENSE](LICENSE) for more information.

## Acknowledgments

- [KittenTTS](https://github.com/KittenML/KittenTTS)
- [gpt4free](https://github.com/xtekky/gpt4free)

## Disclaimer

This project is for educational purposes only. The author will not be responsible for any misuse of the information provided. All the information on this website is published in good faith and for general information purposes only. The author does not make any warranties about the completeness, reliability, and accuracy of this information. Any action you take upon the information you find on this website (FujiwaraChoki/MoneyPrinterV2) is strictly at your own risk. The author will not be liable for any losses and/or damages in connection with the use of our website.
