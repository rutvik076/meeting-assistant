import asyncio
import threading
import time
import uuid
import sys
import uvicorn

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from audio.capture import AudioCapture
from audio.vad import VADProcessor
from stt.transcriber import Transcriber
from brain.agent import classify_utterance, stream_answer, process_utterance
from brain.logger import log_qa
from server.main import app, broadcast, is_listening
from config import SERVER_HOST, SERVER_PORT

_server_loop = None   # reference to server's event loop


def run_server():
    global _server_loop
    _server_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_server_loop)
    config = uvicorn.Config(app, host=SERVER_HOST, port=SERVER_PORT,
                            log_level="warning", loop="asyncio")
    server = uvicorn.Server(config)
    _server_loop.run_until_complete(server.serve())


def broadcast_sync(payload: dict):
    """Thread-safe broadcast from the pipeline loop into the server loop."""
    if _server_loop and _server_loop.is_running():
        future = asyncio.run_coroutine_threadsafe(broadcast(payload), _server_loop)
        try:
            future.result(timeout=2)
        except Exception as e:
            print(f"[Broadcast error] {e}")


async def audio_pipeline():
    vad = VADProcessor()
    stt = Transcriber()
    q: asyncio.Queue = asyncio.Queue()
    cap = AudioCapture(q)
    cap.start()

    import socket
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        ip = "YOUR-PC-IP"

    print(f"\n{'='*54}")
    print(f"  Smart Meeting Assistant — LIVE")
    print(f"  Phone: http://{ip}:{SERVER_PORT}")
    print(f"  Setup: http://{ip}:{SERVER_PORT}/setup")
    print(f"  Logs:  ./logs/")
    print(f"{'='*54}\n")

    try:
        while True:
            chunk = await q.get()
            utterance = vad.process(chunk)
            if utterance is None:
                continue

            if not is_listening():
                continue   # silent drop — no log spam

            t0 = time.perf_counter()
            text = stt.transcribe(utterance)
            if not text or len(text.split()) < 3:
                continue

            print(f"\n[Heard]  {text}")

            classification = await classify_utterance(text)
            action  = classification.get("action", "SKIP")
            reason  = classification.get("reason", "")
            speaker = classification.get("speaker", "unclear")
            ms_classify = int((time.perf_counter() - t0) * 1000)

            if action == "ANSWER":
                print(f"[Agent]  ANSWER | {speaker} ({ms_classify}ms)")
                card_id = str(uuid.uuid4())[:8]

                # Open card on phone
                broadcast_sync({
                    "type":      "stream_start",
                    "card_id":   card_id,
                    "question":  text,
                    "speaker":   speaker,
                    "timestamp": time.time() * 1000,
                })
                print(f"[Phone]  Card opened — streaming answer...")

                # Stream tokens
                full_answer = []
                try:
                    async for token in stream_answer(text, speaker):
                        full_answer.append(token)
                        broadcast_sync({
                            "type":    "stream_token",
                            "card_id": card_id,
                            "token":   token,
                        })
                except Exception as e:
                    print(f"[Stream error] {e}")

                # Close card
                broadcast_sync({"type": "stream_done", "card_id": card_id})

                answer_text = "".join(full_answer)
                ms_total = int((time.perf_counter() - t0) * 1000)
                if answer_text:
                    log_qa(text, answer_text, ms_total)
                print(f"[Done]   {ms_total}ms | {len(answer_text)} chars streamed to phone")

            elif action == "HINT":
                print(f"[Agent]  HINT | {speaker} ({ms_classify}ms) — {reason}")
                result = await process_utterance(text)
                hint = result.get("hint", "")
                if hint:
                    broadcast_sync({
                        "type":      "hint",
                        "question":  text,
                        "answer":    hint,
                        "speaker":   speaker,
                        "timestamp": time.time() * 1000,
                    })
                    print(f"[Hint]   {hint[:80]}")

            else:
                print(f"[Skip]   {speaker} — {reason}")
                # Only broadcast skips to transcript, not as answer cards
                broadcast_sync({
                    "type":      "skip",
                    "question":  text,
                    "answer":    "",
                    "speaker":   speaker,
                    "timestamp": time.time() * 1000,
                })

    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        cap.stop()
        print("\nStopped cleanly.")


if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)   # wait for server loop to start
    try:
        asyncio.run(audio_pipeline())
    except KeyboardInterrupt:
        pass