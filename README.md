# Meeting Assistant

Real-time AI assistant that listens to meetings and answers questions on your phone.

## Setup

1. Install dependencies:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Find your audio device indices:
   ```
   python -c "import sounddevice as sd; [print(i, d['name']) for i, d in enumerate(sd.query_devices())]"
   ```

3. Edit `config.py` — set `MIC_DEVICE_INDEX`, `SYSTEM_DEVICE_INDEX`, and `ANTHROPIC_API_KEY`

4. Test audio capture:
   ```
   python test_audio.py
   ```

5. Run the full pipeline:
   ```
   python pipeline.py
   ```
   Or double-click `start.bat` (starts ngrok + pipeline together)

6. Open `http://localhost:8765` on your phone (or use the ngrok URL for remote access)

## VB-Cable (system audio)
Install from https://vb-audio.com/Cable — required to capture Teams/Zoom audio.
In Windows Sound Settings, set your meeting app output to "CABLE Input".
