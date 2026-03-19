SAMPLE_RATE      = 16000
CHUNK_SECONDS    = 0.5       # process audio every 500ms
VAD_THRESHOLD    = 0.5       # 0.0–1.0, raise if too many false triggers
SILENCE_TIMEOUT  = 1.2       # seconds of silence = utterance complete

# --- SET THESE TO YOUR VALUES FROM STEP 1 ---
MIC_DEVICE_INDEX    = 0      # your microphone
SYSTEM_DEVICE_INDEX = 2      # VB-Cable Output (captures Teams/Zoom audio)

CONTEXT_TURNS    = 5
WHISPER_MODEL   = "base"    # was "large-v3-turbo"
WHISPER_DEVICE   = "cuda"    # or "cpu" if no Nvidia GPU
CLAUDE_MODEL     = "claude-haiku-4-5-20251001"
ANTHROPIC_API_KEY = "sk-ant-YOUR_KEY_HERE"
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8765
WHISPER_DEVICE = "cpu" 
SILENCE_TIMEOUT = 0.8