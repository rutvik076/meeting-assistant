from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import logging, json, time

logger = logging.getLogger("server")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="server/static"), name="static")

connected_clients: set = set()
listening_enabled: bool = True

# Cache-bust version — changes every server restart so phone always gets fresh HTML
_VERSION = str(int(time.time()))

NO_CACHE = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


class ProfileData(BaseModel):
    name: str = ""
    role: str = ""
    experience: str = ""
    skills: str = ""
    projects: str = ""
    education: str = ""
    goal: str = ""
    extra: str = ""


@app.get("/")
async def serve_pwa():
    html = Path("server/static/index.html").read_text(encoding="utf-8")
    # Inject version so browser never serves stale cached page
    html = html.replace("</head>", f'<meta name="version" content="{_VERSION}"></head>')
    return HTMLResponse(html, headers=NO_CACHE)


@app.get("/setup")
async def serve_setup():
    return HTMLResponse(
        Path("server/static/setup.html").read_text(encoding="utf-8"),
        headers=NO_CACHE)


@app.get("/api/profile")
async def get_profile():
    from brain.profile import load_profile
    return JSONResponse(load_profile())


@app.post("/api/profile")
async def update_profile(data: ProfileData):
    from brain.profile import save_profile
    save_profile(data.dict())
    return JSONResponse({"status": "saved"})


@app.get("/api/listening")
async def get_listening():
    return JSONResponse({"listening": listening_enabled})


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    global listening_enabled
    await ws.accept()
    connected_clients.add(ws)
    logger.info(f"Phone connected ({len(connected_clients)} total)")
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
                if msg.get("cmd") == "pause":
                    listening_enabled = False
                    logger.info("Listening PAUSED")
                elif msg.get("cmd") == "resume":
                    listening_enabled = True
                    logger.info("Listening RESUMED")
            except Exception:
                pass
    except WebSocketDisconnect:
        connected_clients.discard(ws)
        logger.info("Phone disconnected")


async def broadcast(payload: dict):
    if not connected_clients:
        return
    dead = set()
    for ws in connected_clients:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.add(ws)
    for ws in dead:
        connected_clients.discard(ws)


def is_listening() -> bool:
    return listening_enabled