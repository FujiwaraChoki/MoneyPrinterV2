# MoneyPrinter V2

> ♥︎ If you're interested in using a hosted version, sign up for the waitlist on [shiori.ai](https://www.shiori.ai), an AI tool that combines all other AI tools into one.

---

> 𝕏 Also, follow me on X: [@DevBySami](https://x.com/DevBySami).

[![madewithlove](https://img.shields.io/badge/made_with-%E2%9D%A4-red?style=for-the-badge&labelColor=orange)](https://github.com/FujiwaraChoki/MoneyPrinterV2)

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donate-brightgreen?logo=buymeacoffee)](https://www.buymeacoffee.com/fujicodes)
[![GitHub license](https://img.shields.io/github/license/FujiwaraChoki/MoneyPrinterV2?style=for-the-badge)](https://github.com/FujiwaraChoki/MoneyPrinterV2/blob/main/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/FujiwaraChoki/MoneyPrinterV2?style=for-the-badge)](https://github.com/FujiwaraChoki/MoneyPrinterV2/issues)
[![GitHub stars](https://img.shields.io/github/stars/FujiwaraChoki/MoneyPrinterV2?style=for-the-badge)](https://github.com/FujiwaraChoki/MoneyPrinterV2/stargazers)
[![Discord](https://img.shields.io/discord/1134848537704804432?style=for-the-badge)](https://dsc.gg/fuji-community)

> Follow me on [X](https://x.com/DevBySami).

An Application that automates the process of making money online.
MPV2 (MoneyPrinter Version 2) is, as the name suggests, the second version of the MoneyPrinter project. It is a complete rewrite of the original project, with a focus on a wider range of features and a more modular architecture.

> **Note:** MPV2 needs Python 3.9 to function effectively.
> Watch the YouTube video [here](https://youtu.be/wAZ_ZSuIqfk)

## Features

- [x] Twitter Bot (with CRON Jobs => `scheduler`)
- [x] YouTube Shorts Automater (with CRON Jobs => `scheduler`)
- [x] Affiliate Marketing (Amazon + Twitter)
- [x] Find local businesses & cold outreach

## Versions

MoneyPrinter has different versions for multiple languages developed by the community for the community. Here are some known versions:

- Chinese: [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo)

If you would like to submit your own version/fork of MoneyPrinter, please open an issue describing the changes you made to the fork.

## Installation

Please install [Microsoft Visual C++ build tools](https://visualstudio.microsoft.com/de/visual-cpp-build-tools/) first, so that CoquiTTS can function correctly.

> ⚠️ If you are planning to reach out to scraped businesses per E-Mail, please first install the [Go Programming Language](https://golang.org/).

```bash
git clone https://github.com/FujiwaraChoki/MoneyPrinterV2.git

cd MoneyPrinterV2
# Copy Example Configuration and fill out values in config.json
cp config.example.json config.json

# Create a virtual environment
python -m venv venv

# Activate the virtual environment - Windows
.\venv\Scripts\activate

# Activate the virtual environment - Unix
source venv/bin/activate

# Install the requirements
pip install -r requirements.txt
```

## Usage

```bash
# Run the application
python src/main.py
```

## Documentation

All relevant document can be found [here](docs/).

## Scripts

For easier usage, there are some scripts in the `scripts` directory, that can be used to directly access the core functionality of MPV2, without the need of user interaction.

All scripts need to be run from the root directory of the project, e.g. `bash scripts/upload_video.sh`.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us. Check out [docs/Roadmap.md](docs/Roadmap.md) for a list of features that need to be implemented.

## Code of Conduct

Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details on our code of conduct, and the process for submitting pull requests to us.

## License

MoneyPrinterV2 is licensed under `Affero General Public License v3.0`. See [LICENSE](LICENSE) for more information.

## Acknowledgments

- [CoquiTTS](https://github.com/coqui-ai/TTS)
- [gpt4free](https://github.com/xtekky/gpt4free)

## Disclaimer

This project is for educational purposes only. The author will not be responsible for any misuse of the information provided. All the information on this website is published in good faith and for general information purpose only. The author does not make any warranties about the completeness, reliability, and accuracy of this information. Any action you take upon the information you find on this website (FujiwaraChoki/MoneyPrinterV2), is strictly at your own risk. The author will not be liable for any losses and/or damages in connection with the use of our website.
