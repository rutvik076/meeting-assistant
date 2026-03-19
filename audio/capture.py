import sounddevice as sd
import numpy as np
import asyncio
from config import SAMPLE_RATE, CHUNK_SECONDS, MIC_DEVICE_INDEX, SYSTEM_DEVICE_INDEX

class AudioCapture:
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        self.chunk_size = int(SAMPLE_RATE * CHUNK_SECONDS)
        self._loop = None
        self._streams = []

    def start(self):
        self._loop = asyncio.get_event_loop()

        for device_idx in [MIC_DEVICE_INDEX, SYSTEM_DEVICE_INDEX]:
            try:
                stream = sd.InputStream(
                    device=device_idx,
                    samplerate=SAMPLE_RATE,
                    channels=1,
                    dtype="float32",
                    blocksize=self.chunk_size,
                    callback=self._make_callback(device_idx),
                )
                stream.start()
                self._streams.append(stream)
                print(f"[Audio] Capturing from device {device_idx}")
            except Exception as e:
                print(f"[Audio] WARNING: Could not open device {device_idx}: {e}")

    def stop(self):
        for s in self._streams:
            s.stop()
            s.close()

    def _make_callback(self, device_idx):
        def callback(indata, frames, time, status):
            if status:
                print(f"[Audio] Device {device_idx} status: {status}")
            chunk = indata.copy().flatten()
            # Skip near-silent chunks early — saves VAD processing time
            if np.abs(chunk).max() < 0.001:
                return
            self._loop.call_soon_threadsafe(
                self.queue.put_nowait, chunk
            )
        return callback