import torch
import numpy as np
from config import SAMPLE_RATE, VAD_THRESHOLD, SILENCE_TIMEOUT, CHUNK_SECONDS

# Silero VAD requires exactly 512 samples per call at 16000 Hz
SILERO_WINDOW = 512

class VADProcessor:
    def __init__(self):
        print("[VAD] Loading Silero model...")
        self.model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            trust_repo=True,
            onnx=False,
        )
        self.model.eval()
        print("[VAD] Ready.")

        self._buffer        = []
        self._silence_count = 0
        self._speaking      = False
        self._silence_limit = int(SILENCE_TIMEOUT / CHUNK_SECONDS)

        # Leftover samples that didn't fill a full 512-window yet
        self._remainder = np.array([], dtype=np.float32)

    def process(self, chunk: np.ndarray):
        """
        Feed one audio chunk (any size).
        Internally slices into 512-sample windows for Silero.
        Returns complete utterance array when speech ends, else None.
        """
        # Combine any leftover samples from last call with new chunk
        audio = np.concatenate([self._remainder, chunk])

        # Walk through in 512-sample steps
        speech_detected = False
        i = 0
        while i + SILERO_WINDOW <= len(audio):
            window = audio[i : i + SILERO_WINDOW]
            tensor = torch.from_numpy(window).float()

            # Normalise if clipping
            peak = tensor.abs().max()
            if peak > 1.0:
                tensor = tensor / peak

            with torch.no_grad():
                prob = self.model(tensor, SAMPLE_RATE).item()

            if prob >= VAD_THRESHOLD:
                speech_detected = True

            i += SILERO_WINDOW

        # Save any leftover samples (< 512) for next call
        self._remainder = audio[i:]

        # Now update state machine based on whether this chunk had speech
        if speech_detected:
            self._buffer.append(chunk)
            self._silence_count = 0
            self._speaking = True

        elif self._speaking:
            self._buffer.append(chunk)
            self._silence_count += 1

            if self._silence_count >= self._silence_limit:
                utterance = np.concatenate(self._buffer)
                self._reset()
                return utterance

        return None

    def _reset(self):
        self._buffer        = []
        self._silence_count = 0
        self._speaking      = False
        self._remainder     = np.array([], dtype=np.float32)