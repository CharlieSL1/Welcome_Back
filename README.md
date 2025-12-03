# WELCOMEBACK
> WelcomeBack is an AI-powered voice system that brings back the voice of a beloved grandfather through technology. Using GPT-4 to generate warm, contextual Chinese messages based on time-of-day, the system automatically triggers at random intervals (2-6 hours) and transforms text into the grandfather's voice using Seed-VC voice conversion technology. Designed for embedded deployment on Raspberry Pi, WelcomeBack creates spontaneous moments of connection throughout the day, preserving memories and bringing comfort through the familiar voice of a loved one.

![GitHub Created At](https://img.shields.io/badge/Created_At-2025-orange) [![GITHUB](https://img.shields.io/badge/github-repo-blue?logo=github)](https://github.com) [![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

![banner](media/banner.png)

## Table of Contents

- [Background](#background)
- [Features](#features)
- [Architecture](#architecture)
- [Install](#install)
- [Configuration](#configuration)
- [Usage](#usage)
- [Version](#version)
- [TODO](#todo)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)
- [License](#license)

## Background

WelcomeBack was created to bridge the emotional gap left when we lose loved ones, deeply personal relative project. Take My grandparents voices and daily presence we deeply miss. This project using a multi-agent concept, caring moments that define intergenerational relationships. Instead of static memories, WelcomeBack generates dynamic, context-aware messages that feel natural and timely—asking about your day in the afternoon, reminding you to rest in the evening, or greeting you warmly in the morning.

The system uses voice cloning technology (Seed-VC) to preserve the unique timbre and speaking style of the grandfather, while GPT-4 ensures that each message is contextually appropriate for the time of day and feels genuinely caring. By running on Raspberry Pi, WelcomeBack becomes a quiet presence in your home, surprising you with moments of connection at random but meaningful intervals throughout the day.

## Features

- **Context-Aware Generation**: Messages adapt to time of day (morning, noon, afternoon, evening, night)
- **Random Triggering**: Spontaneous messages every 2-6 hours for natural interaction
- **Voice Cloning**: Uses Seed-VC to convert text to the grandfather's authentic voice
- **Embedded Deployment**: Designed for Raspberry Pi, runs autonomously 24/7
- **Chinese Language Support**: Native Chinese message generation with culturally appropriate content
- **Automatic Playback**: Generates and plays audio automatically without user interaction

## Architecture

```
TimeTrigger (Scheduler)
    ↓
GPT-4 (Message Generation)
    ↓
OpenAI TTS (Text-to-Speech)
    ↓
Seed-VC (Voice Conversion)
    ↓
AudioPlayer (Raspberry Pi Playback)
```

The system operates in a continuous loop:
1. **Scheduler** monitors time and triggers at random intervals (2-6 hours)
2. **Message Generator** uses GPT-4 to create contextually appropriate Chinese messages
3. **TTS Engine** converts the selected message to speech
4. **Voice Converter** (Seed-VC) transforms the speech to match the grandfather's voice
5. **Audio Player** plays the generated audio on Raspberry Pi speakers

## Install

```bash
# Clone the repo
git clone https://github.com/[username]/WelcomeBack.git

cd WelcomeBack

# Create and activate a virtual environment (Python 3.10+ recommended)
python3.10 -m venv .venv
source .venv/bin/activate
# On Windows use: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install openai

# Install Seed-VC dependencies (see Seed-VC repository for full requirements)
# Ensure Seed-VC is cloned and configured at the path specified in SeedVCSpeaker.py

# For Raspberry Pi audio playback
sudo apt-get update
sudo apt-get install alsa-utils  # for aplay
# or
sudo apt-get install pulseaudio-utils  # for paplay
```

## Configuration

### Environment Variables

Set the following environment variables before running:

```bash
# Required: OpenAI API key for GPT-4 and TTS
export OPENAI_API_KEY="your-openai-api-key-here"

# Required: Path to Seed-VC repository
export SEED_VC_PATH="/path/to/seed-vc"
```

Or create a `.env` file in the project root (make sure it's in `.gitignore`):
```bash
OPENAI_API_KEY=your-openai-api-key-here
SEED_VC_PATH=/path/to/seed-vc
```

### Setting up Seed-VC

1. Clone the Seed-VC repository:
```bash
git clone https://github.com/Plachta/Seed-VC.git
```

2. Follow Seed-VC installation instructions in their repository

3. Set the `SEED_VC_PATH` environment variable to point to the cloned repository

### Reference Audio Setup

Place your grandfather's reference audio files in:
```
seed-vc/data/grandfather/
```

The system will automatically select the best available reference audio in this priority order:
1. Fine-tuned model (`checkpoints/grandfather_vc_model.pt`)
2. Enhanced reference audio
3. Long-form reference audio
4. Standard reference audio

### Trigger Interval Configuration

Modify the random trigger interval in `TimeTrigger.py`:
```python
MIN_INTERVAL_HOURS = 2  # Minimum hours between triggers
MAX_INTERVAL_HOURS = 6  # Maximum hours between triggers
```

## Usage

### Running on Development Machine

```bash
python TimeTrigger.py
```

The scheduler will start and show:
```
WelcomeBack scheduler started with random triggers
Random interval: 2-6 hours
Next trigger scheduled at: 2025-01-XX XX:XX:XX
```

### Running on Raspberry Pi

1. Transfer all files to Raspberry Pi
2. Set up Seed-VC on the device
3. Run as a system service (optional):

Create `/etc/systemd/system/welcomeback.service`:
```ini
[Unit]
Description=WelcomeBack Voice System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/WelcomeBack
ExecStart=/home/pi/WelcomeBack/.venv/bin/python TimeTrigger.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable welcomeback
sudo systemctl start welcomeback
```

## TODO

- [X] Core scheduler implementation with random triggering
- [X] GPT-4 message generation with time-based context
- [X] Seed-VC integration for voice conversion
- [X] Raspberry Pi audio playback support
- [X] Automatic reference audio selection
- [ ] Message history and logging
- [ ] Multi-language support
- [ ] Cloud backup of generated messages

## Contributing

```
Core System

Concept & Design: Li Shi

Voice Conversion Integration: Li Shi

Embedded System Design: Li Shi

Special Thanks

Akito Van Troyer

```

## Acknowledgements

WelcomeBack uses:

- [OpenAI GPT-4](https://openai.com/gpt-4) for intelligent, context-aware message generation.

- [OpenAI TTS](https://openai.com/api/) for high-quality text-to-speech conversion.

- [Seed-VC](https://github.com/Plachta/Seed-VC) by Plachta for zero-shot voice conversion technology.

- [Raspberry Pi](https://www.raspberrypi.org/) for embedded system deployment.

## License

[MIT](LICENSE) © lishi
