# Meeting Assistant — Real-Time AI Interview Coach

A real-time AI assistant that listens to your meetings and interviews, detects questions, and streams answers privately to your phone in seconds.

## How it works

```
Microphone → VAD → Whisper STT → Smart Agent (Claude) → WebSocket → Phone PWA
```

- **Voice Activity Detection** (Silero VAD) — filters silence, captures only speech
- **Speech-to-Text** (faster-whisper) — transcribes locally, no audio sent to cloud
- **Smart Agent** (Claude Haiku) — understands conversation context, decides when to answer
- **Streaming answers** — first words appear on phone in ~300ms
- **Persona mode** — answers as YOU using your profile, not as "I am an AI"
- **Local storage** — all answers saved on your phone, exportable as .txt

## Features

- Real-time answer streaming word by word
- Smart SKIP when you are already answering confidently
- HINT cards when you miss a key point
- Toggle listening on/off from your phone
- Three-tab phone UI: Answers / Transcript / Profile
- Session-grouped history with local persistence
- Export answers and transcript as .txt
- Profile editor built into phone UI
- Auto-save Q&A log to `logs/` folder daily

## Requirements

- Python 3.11+
- Windows 10/11 (Mac/Linux supported with minor changes)
- Anthropic API key (get one at console.anthropic.com)
- VB-Cable (free, for system audio capture on Windows)

## Setup

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/meeting-assistant.git
cd meeting-assistant
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure

```bash
cp config.example.py config.py
```

Edit `config.py`:
- Set `ANTHROPIC_API_KEY` to your key from console.anthropic.com
- Set `MIC_DEVICE_INDEX` and `SYSTEM_DEVICE_INDEX` (run `python scripts/list_devices.py` to find them)
- Set `WHISPER_DEVICE = "cuda"` if you have an Nvidia GPU, else `"cpu"`

### 3. Find your audio devices

```bash
python scripts/list_devices.py
```

### 4. Run

```bash
python pipeline.py
```

Open the URL shown on your phone browser. Fill in your profile at `/setup`.

## Phone setup

1. Make sure phone and PC are on the same WiFi
2. Open `http://YOUR-PC-IP:8765` in Chrome or Safari
3. Go to Profile tab → fill in your name, role, skills, projects
4. Tap the toggle to start listening

## Windows system audio (Teams/Zoom/Meet)

Install [VB-Cable](https://vb-audio.com/Cable) (free). In Windows Sound Settings → App Volume, set your meeting app output to "CABLE Input". Set `SYSTEM_DEVICE_INDEX` to the "CABLE Output" device index.

## Cloud deployment (optional)

See [DEPLOY.md](DEPLOY.md) for instructions on deploying the phone UI server to Railway/Render so your phone works outside home WiFi.

## Project structure

```
meeting-assistant/
├── pipeline.py          # Main entry point
├── config.example.py    # Config template (copy to config.py)
├── requirements.txt
├── audio/
│   ├── capture.py       # Dual mic + system audio capture
│   └── vad.py           # Silero VAD utterance segmenter
├── stt/
│   └── transcriber.py   # faster-whisper STT
├── brain/
│   ├── agent.py         # Smart conversation agent (classify + stream)
│   ├── profile.py       # User profile loader/builder
│   ├── context.py       # Conversation memory
│   └── logger.py        # Daily Q&A log writer
├── server/
│   ├── main.py          # FastAPI + WebSocket server
│   └── static/
│       ├── index.html   # Phone PWA (3-tab UI)
│       └── setup.html   # Profile setup page
├── scripts/
│   └── list_devices.py  # Audio device discovery helper
└── logs/                # Auto-created, daily Q&A logs
```

## Latency

| Setup | Whisper | Claude | Total |
|---|---|---|---|
| CPU (base model) | ~0.5s | ~1.5s | ~2-3s |
| CPU (small model) | ~1.5s | ~1.5s | ~3-4s |
| GPU (large-v3-turbo) | ~0.3s | ~0.4s | ~1s |

## Cost

Claude Haiku costs ~$0.001 per answer. $5 credit = ~5000 answers.

## License

MIT
