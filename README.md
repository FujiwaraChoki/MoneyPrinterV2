# MoneyPrinter V2

Frank's fork is being repurposed from a generic faceless-content tool into a long-term income asset printer: long-tail content generation, cross-platform distribution, owned-audience capture, and monetization experiments around AI / developer workflows.

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

An application that automates repetitive parts of online monetization.
MPV2 (MoneyPrinter Version 2) is, as the name suggests, the second version of the MoneyPrinter project. This fork keeps the modular core, but is being redirected toward owned content assets, conversion paths, and low-touch revenue experiments instead of pure service lead generation.

> **Note:** MPV2 needs Python 3.12 to function effectively.
> Watch the YouTube video [here](https://youtu.be/wAZ_ZSuIqfk)

## Features

- [x] Twitter Bot (with CRON Jobs => `scheduler`)
- [x] YouTube Shorts Automator (with CRON Jobs => `scheduler`)
- [x] Affiliate Marketing (Amazon + Twitter)
- [x] Find local businesses & cold outreach
- [x] Service-led content profiles for case-study style YouTube / X accounts
- [x] Cross-post YouTube uploads to TikTok / Instagram via Post Bridge

## This Fork's Goal

This fork is being re-optimized around long-term monetizable assets:

- publish reusable content with long-tail utility
- turn distribution into owned audience instead of one-off impressions
- direct attention toward assets such as newsletters, resource packs, templates, and selective affiliate offers
- treat service revenue as optional bootstrap fuel, not the end state

See [docs/FrankMoneyPrinter.md](docs/FrankMoneyPrinter.md) for the specialization strategy and [docs/Roadmap.md](docs/Roadmap.md) for the implementation phases.

## Versions

MoneyPrinter has different versions for multiple languages developed by the community for the community. Here are some known versions:

- Chinese: [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo)

If you would like to submit your own version/fork of MoneyPrinter, please open an issue describing the changes you made to the fork.

## Installation

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
