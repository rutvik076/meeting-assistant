import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import numpy as np
from faster_whisper import WhisperModel
from config import WHISPER_MODEL, WHISPER_DEVICE

class Transcriber:
    def __init__(self):
        # Auto-fallback: try GPU, fall back to CPU if driver mismatch
        device = WHISPER_DEVICE
        compute = "float16" if device == "cuda" else "int8"

        try:
            if device == "cuda":
                import torch
                if not torch.cuda.is_available():
                    raise RuntimeError("CUDA not available")
            print(f"[STT] Loading Whisper {WHISPER_MODEL} on {device} ({compute})...")
            self.model = WhisperModel(
                WHISPER_MODEL,
                device=device,
                compute_type=compute,
                cpu_threads=4,
                num_workers=1,
            )
        except Exception as e:
            print(f"[STT] GPU failed ({e}), falling back to CPU...")
            device = "cpu"
            compute = "int8"
            self.model = WhisperModel(
                WHISPER_MODEL,
                device="cpu",
                compute_type="int8",
                cpu_threads=4,
                num_workers=1,
            )

        print("[STT] Pre-warming model...")
        self.transcribe(np.zeros(16000, dtype=np.float32))
        print(f"[STT] Ready on {device}.")

    def transcribe(self, audio: np.ndarray) -> str:
        segments, _ = self.model.transcribe(
            audio,
            beam_size=1,
            language="en",
            vad_filter=True,
            vad_parameters={
                "min_silence_duration_ms": 300,
                "speech_pad_ms": 100,
            },
        )
        return " ".join(s.text for s in segments).strip()