# Deploying the phone UI server to the cloud

This lets your phone access answers outside your home WiFi — useful for real interviews.

## Architecture when deployed

```
Your laptop (local)          Cloud server
──────────────────           ────────────────────
Mic → Whisper → Claude  →→→  FastAPI + WebSocket  ←  Your phone
                  (WebSocket tunnel)
```

The laptop pipeline connects to the cloud server via WebSocket and pushes answers there. The phone connects to the cloud server to receive them.

## Option 1: Railway (recommended, free tier available)

1. Push your repo to GitHub
2. Go to railway.app → New Project → Deploy from GitHub
3. Select your repo
4. Add environment variables in Railway dashboard:
   - `PORT` = 8765
5. Railway gives you a URL like `https://meeting-assistant-production.up.railway.app`

## Option 2: Render (free tier, sleeps after 15min inactivity)

1. Go to render.com → New Web Service
2. Connect your GitHub repo
3. Build command: `pip install -r requirements.txt`
4. Start command: `python server/run_cloud.py`
5. Set environment variable `PORT` from Render dashboard

## Option 3: ngrok (simplest, no deployment needed)

Keep everything local but expose via HTTPS tunnel:

```bash
# Install ngrok from ngrok.com
ngrok http 8765
```

Use the HTTPS URL on your phone. Free tier gives random URLs; paid gives stable URLs.

## server/run_cloud.py (cloud-only server)

When deployed to cloud, run `server/run_cloud.py` instead of `pipeline.py`.
The laptop pipeline connects to it via `CLOUD_WS_URL` in config.py.
