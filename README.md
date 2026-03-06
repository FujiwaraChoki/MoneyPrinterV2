# MoneyPrinter V2 🤖💰

> **Automate Your Online Income** - A complete automation suite for YouTube Shorts, Twitter bots, affiliate marketing, and business outreach.

[![Made with Love](https://img.shields.io/badge/made_with-%E2%9D%A4-red?style=for-the-badge&labelColor=orange)](https://github.com/FujiwaraChoki/MoneyPrinterV2)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donate-brightgreen?logo=buymeacoffee)](https://www.buymeacoffee.com/fujicodes)
[![GitHub license](https://img.shields.io/github/license/FujiwaraChoki/MoneyPrinterV2?style=for-the-badge)](https://github.com/FujiwaraChoki/MoneyPrinterV2/blob/main/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/FujiwaraChoki/MoneyPrinterV2?style=for-the-badge)](https://github.com/FujiwaraChoki/MoneyPrinterV2/stargazers)
[![Discord](https://img.shields.io/discord/1134848537704804432?style=for-the-badge)](https://dsc.gg/fuji-community)

---

## 📖 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [YouTube Shorts Automater](#1-youtube-shorts-automater)
  - [Twitter Bot](#2-twitter-bot)
  - [Affiliate Marketing](#3-affiliate-marketing)
  - [Business Outreach](#4-business-outreach)
- [CRON Jobs & Scheduling](#cron-jobs--scheduling)
- [Scripts](#scripts)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

**MoneyPrinter V2** is a complete rewrite of the original MoneyPrinter project, designed to automate multiple online income streams:

- 🎬 **YouTube Shorts**: Auto-generate and upload viral short videos
- 🐦 **Twitter Bot**: Schedule and post tweets automatically
- 💼 **Affiliate Marketing**: Create and share Amazon affiliate content
- 📧 **Business Outreach**: Find local businesses and send cold emails

**Why MPV2?**
- Modular architecture for easy customization
- Built-in CRON scheduler for hands-free operation
- Multi-account support for scaling
- LLM-powered content generation

---

## ✨ Features

### YouTube Shorts Automater
- ✅ Auto-generate video scripts using AI (GPT-4, Claude, etc.)
- ✅ Text-to-speech with multiple voice options
- ✅ Automated video upload to YouTube
- ✅ CRON scheduling for consistent posting
- ✅ Multi-account management
- ✅ Niche-specific content generation

### Twitter Bot
- ✅ AI-generated tweets based on your niche
- ✅ Scheduled posting with CRON jobs
- ✅ Multi-account support
- ✅ Engagement automation
- ✅ Hashtag optimization

### Affiliate Marketing
- ✅ Amazon affiliate link integration
- ✅ AI-generated product pitches
- ✅ Automated Twitter posting
- ✅ Performance tracking

### Business Outreach
- ✅ Local business scraping
- ✅ Automated cold email campaigns
- ✅ Customizable email templates
- ✅ Go-based email sender for reliability

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/FujiwaraChoki/MoneyPrinterV2.git
cd MoneyPrinterV2

# Copy and configure
cp config.example.json config.json
# Edit config.json with your API keys

# Install dependencies
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt

# Run the application
python src/main.py
```

---

## 📦 Installation

### Prerequisites

- **Python 3.12+** (required)
- **Firefox** (for YouTube automation)
- **Go** (optional, for email outreach)
- **API Keys**:
  - OpenAI / Anthropic / Other LLM provider
  - YouTube Data API
  - Twitter API
  - Amazon Affiliate API (optional)

### Step-by-Step Installation

#### 1. Install Python 3.12

**macOS/Linux:**
```bash
# Using pyenv (recommended)
pyenv install 3.12.0
pyenv local 3.12.0
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/)

#### 2. Install Go (Optional)

Only needed for email outreach feature.

```bash
# macOS
brew install go

# Linux
sudo apt install golang-go

# Windows
# Download from https://golang.org/dl/
```

#### 3. Clone and Setup

```bash
git clone https://github.com/FujiwaraChoki/MoneyPrinterV2.git
cd MoneyPrinterV2

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## ⚙️ Configuration

### 1. Copy Example Config

```bash
cp config.example.json config.json
```

### 2. Edit `config.json`

```json
{
  "llm_provider": "openai",
  "llm_api_key": "your-api-key-here",
  "llm_model": "gpt-4",
  
  "youtube": {
    "api_key": "your-youtube-api-key",
    "firefox_profile": "/path/to/firefox/profile"
  },
  
  "twitter": {
    "api_key": "your-twitter-api-key",
    "api_secret": "your-twitter-api-secret",
    "access_token": "your-access-token",
    "access_token_secret": "your-access-token-secret"
  },
  
  "affiliate": {
    "amazon_tag": "your-amazon-affiliate-tag"
  },
  
  "outreach": {
    "email_from": "your-email@example.com",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_password": "your-app-password"
  }
}
```

### 3. Get API Keys

#### OpenAI API Key
1. Go to [platform.openai.com](https://platform.openai.com)
2. Create an account and navigate to API keys
3. Generate a new key

#### YouTube Data API
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable YouTube Data API v3
4. Create credentials (API key)

#### Twitter API
1. Go to [developer.twitter.com](https://developer.twitter.com)
2. Apply for developer access
3. Create an app and get your keys

#### Amazon Affiliate
1. Sign up at [affiliate-program.amazon.com](https://affiliate-program.amazon.com)
2. Get your affiliate tag

---

## 🎮 Usage

### Starting the Application

```bash
python src/main.py
```

You'll see a menu:

```
============ OPTIONS ============
 1. YouTube Shorts Automater
 2. Twitter Bot
 3. Affiliate Marketing
 4. Business Outreach
 5. Exit
=================================
```

---

### 1. YouTube Shorts Automater

**What it does:**
- Generates video scripts based on your niche
- Converts text to speech
- Creates short videos
- Uploads to YouTube automatically

**Setup:**

1. Select option `1` from the main menu
2. Create a new account or select existing
3. Provide:
   - **Nickname**: e.g., "Tech Channel"
   - **Firefox Profile Path**: Path to your Firefox profile with YouTube logged in
   - **Niche**: e.g., "AI News", "Crypto", "Fitness"
   - **Language**: e.g., "en", "es", "fr"

**Generate a Video:**

```bash
# From main menu, select YouTube Shorts
# Choose "Generate Video"
# Enter topic or let AI choose
# Video will be generated and saved
```

**Schedule Automatic Uploads:**

```bash
# From YouTube menu, select "Setup CRON Job"
# Choose frequency (daily, twice daily, etc.)
# Videos will be auto-generated and uploaded
```

---

### 2. Twitter Bot

**What it does:**
- Generates tweets based on your niche
- Posts automatically on schedule
- Manages multiple accounts

**Setup:**

1. Select option `2` from main menu
2. Create Twitter account profile
3. Provide:
   - **Nickname**: e.g., "Crypto Bot"
   - **Niche**: e.g., "Cryptocurrency"
   - **Language**: e.g., "en"

**Post a Tweet:**

```bash
# From Twitter menu, select "Post Tweet"
# AI will generate a tweet based on your niche
# Review and confirm
```

**Schedule Tweets:**

```bash
# Select "Setup CRON Job"
# Choose posting frequency
# Tweets will be auto-generated and posted
```

---

### 3. Affiliate Marketing

**What it does:**
- Creates product pitches for Amazon products
- Posts affiliate links on Twitter
- Tracks performance

**Setup:**

1. Select option `3` from main menu
2. Enter Amazon product URL
3. AI generates a compelling pitch
4. Post to Twitter with affiliate link

**Example:**

```bash
# Input: https://amazon.com/product/B08XYZ123
# Output: AI-generated tweet with affiliate link
# Posted to your Twitter account
```

---

### 4. Business Outreach

**What it does:**
- Scrapes local businesses from Google Maps
- Generates personalized cold emails
- Sends emails automatically

**Setup:**

1. Install Go (required for email sender)
2. Configure SMTP settings in `config.json`
3. Select option `4` from main menu

**Run Outreach Campaign:**

```bash
# Enter location (e.g., "New York, NY")
# Enter business type (e.g., "restaurants")
# AI scrapes businesses and generates emails
# Review and send
```

---

## ⏰ CRON Jobs & Scheduling

MPV2 includes a built-in scheduler for hands-free operation.

### How It Works

1. Set up CRON jobs from the menu
2. Scheduler runs in the background
3. Tasks execute automatically at specified times

### Example Schedule

```python
# YouTube: Upload 2 videos per day
schedule.every().day.at("09:00").do(generate_and_upload_video)
schedule.every().day.at("18:00").do(generate_and_upload_video)

# Twitter: Post 5 tweets per day
schedule.every(4).hours.do(post_tweet)
```

### Running the Scheduler

```bash
# Start scheduler in background
python src/cron.py &

# Or use systemd/cron for production
```

---

## 🛠️ Scripts

MPV2 includes standalone scripts for direct access to core functionality.

### Available Scripts

```bash
# Upload a video directly
bash scripts/upload_video.sh

# Post a tweet
bash scripts/post_tweet.sh

# Generate affiliate content
bash scripts/generate_affiliate.sh

# Run outreach campaign
bash scripts/run_outreach.sh
```

**Note:** All scripts must be run from the project root directory.

---

## 🏗️ Architecture

```
MoneyPrinterV2/
├── src/
│   ├── main.py              # Main entry point
│   ├── cron.py              # CRON scheduler
│   ├── config.py            # Configuration loader
│   ├── llm_provider.py      # LLM integration
│   ├── classes/
│   │   ├── YouTube.py       # YouTube automation
│   │   ├── Twitter.py       # Twitter bot
│   │   ├── AFM.py           # Affiliate marketing
│   │   ├── Outreach.py      # Business outreach
│   │   └── Tts.py           # Text-to-speech
│   └── utils.py             # Helper functions
├── scripts/                 # Standalone scripts
├── docs/                    # Documentation
├── config.example.json      # Example configuration
└── requirements.txt         # Python dependencies
```

### Key Components

- **LLM Provider**: Supports OpenAI, Anthropic, and other providers
- **Cache System**: Stores account data and generated content
- **Scheduler**: Built-in CRON for automation
- **Multi-Account**: Manage multiple YouTube/Twitter accounts

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "Python 3.12 required"

**Solution:**
```bash
python --version  # Check version
pyenv install 3.12.0  # Install if needed
```

#### 2. "Firefox profile not found"

**Solution:**
- Open Firefox
- Go to `about:profiles`
- Copy the "Root Directory" path
- Use this path in config

#### 3. "YouTube upload failed"

**Solution:**
- Ensure you're logged into YouTube in Firefox
- Check YouTube API quota
- Verify API key is correct

#### 4. "Twitter API error"

**Solution:**
- Check API keys in `config.json`
- Verify Twitter developer account is active
- Check rate limits

#### 5. "Email sending failed"

**Solution:**
- Use app-specific password (not regular password)
- Enable "Less secure app access" (Gmail)
- Check SMTP settings

---

## 📚 Documentation

Detailed documentation available in the [`docs/`](docs/) directory:

- [Roadmap](docs/Roadmap.md) - Planned features
- [API Reference](docs/API.md) - Code documentation
- [Examples](docs/Examples.md) - Usage examples

---

## 🤝 Contributing

We welcome contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black src/

# Lint
flake8 src/
```

---

## 📄 License

This project is licensed under the **Affero General Public License v3.0**. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [KittenTTS](https://github.com/KittenML/KittenTTS) - Text-to-speech engine
- [gpt4free](https://github.com/xtekky/gpt4free) - Free LLM access

---

## ⚠️ Disclaimer

**This project is for educational purposes only.**

The author is not responsible for any misuse of this software. Use at your own risk. Always comply with:
- YouTube Terms of Service
- Twitter Terms of Service
- Amazon Affiliate Program policies
- Anti-spam laws (CAN-SPAM Act, GDPR, etc.)

---

## 💬 Community & Support

- **Discord**: [Join our community](https://dsc.gg/fuji-community)
- **Twitter**: [@DevBySami](https://x.com/DevBySami)
- **Issues**: [GitHub Issues](https://github.com/FujiwaraChoki/MoneyPrinterV2/issues)
- **Sponsor**: [Buy Me A Coffee](https://www.buymeacoffee.com/fujicodes)

---

## 🎥 Video Tutorial

Watch the full setup guide: [YouTube Tutorial](https://youtu.be/wAZ_ZSuIqfk)

---

## 🌍 Versions

Community versions in other languages:

- **Chinese**: [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo)

Want to create a version? Open an issue describing your changes!

---

**Made with ❤️ by [@DevBySami](https://x.com/DevBySami)**

**Sponsor**: [shiori.ai](https://www.shiori.ai) - The Best AI Chat App
