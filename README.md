# NewsBite

NewsBite is a small Flask web app that turns a topic + time window into:

- a short (≈30s) “viral-style” script based on recent headlines/search results
- an AI voiceover MP3 generated from that script

It uses:

- **Tavily** for web/news search
- **Groq** (LLM) to write the script
- **ElevenLabs** to generate speech audio

## How it works

1. You enter a **topic**, pick a **persona**, and a **time period**.
2. The backend searches for relevant updates in that time window.
3. It prompts an LLM to produce a script (max ~75 words).
4. It generates an MP3 voiceover and serves it back to the page.

Audio is stored **in-memory** and auto-expires after ~5 minutes.

## Project layout

- [app.py](app.py) — local Flask dev server entrypoint
- [api/index.py](api/index.py) — Vercel serverless entrypoint (Python runtime)
- [templates/index.html](templates/index.html) — UI template
- [static/](static/) — CSS/JS/assets
- [vercel.json](vercel.json) — Vercel build + routing configuration
- [requirements.txt](requirements.txt) — Python dependencies

## Requirements

- Python 3.10+ (3.11/3.12 are fine)
- API keys for Tavily, Groq, and ElevenLabs

## Environment variables

Create a `.env` file (it is ignored by git via `.gitignore`) with:

- `TAVILY_API_KEY` — Tavily API key
- `GROQ_API_KEY` — Groq API key
- `ELEVEN_API_KEY` — ElevenLabs API key

Optional:

- `FLASK_DEBUG` — set to `true` to run Flask in debug mode locally
- `ALLOW_PROMPT` — set to `true` to allow interactive key entry in a local TTY (only used by [app.py](app.py))

Example:

```bash
TAVILY_API_KEY=...
GROQ_API_KEY=...
ELEVEN_API_KEY=...
FLASK_DEBUG=true
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open:

- http://localhost:5000

## Deploy to Vercel

This repo is set up for Vercel’s Python serverless runtime.

- The serverless app entrypoint is [api/index.py](api/index.py)
- Routing is configured in [vercel.json](vercel.json)

Steps:

1. Import the repository into Vercel (or deploy with the Vercel CLI).
2. In **Project Settings → Environment Variables**, add:
   - `TAVILY_API_KEY`
   - `GROQ_API_KEY`
   - `ELEVEN_API_KEY`
3. Deploy.

## Notes / customization

- Persona + time period options live in `PERSONAS` and `TIME_PERIODS` in both [app.py](app.py) and [api/index.py](api/index.py).
- The Groq model is currently set to `llama-3.3-70b-versatile`.
- ElevenLabs `voice_id` is hardcoded; change it in the `text_to_speech.convert(...)` call if you want a different voice.
