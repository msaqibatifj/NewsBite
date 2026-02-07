import os
import sys
import uuid
import time as time_module
from io import BytesIO
from pathlib import Path
from flask import Flask, render_template, request, url_for, send_file, abort
from dotenv import load_dotenv
from tavily import TavilyClient
from groq import Groq
from elevenlabs.client import ElevenLabs

load_dotenv()

# In-memory audio storage with auto-cleanup
audio_cache = {}
AUDIO_TTL = 300  # 5 minutes


def get_api_key(name, env_var):
    key = os.getenv(env_var)
    if key:
        return key
    raise RuntimeError(
        f"Missing {name} API key. Set {env_var} in your environment."
    )


# Initialize Clients (lazy initialization for serverless)
tavily = None
eleven_client = None
groq_client = None


def init_clients():
    global tavily, eleven_client, groq_client
    if tavily is None:
        tavily_key = get_api_key("Tavily", "TAVILY_API_KEY")
        tavily = TavilyClient(api_key=tavily_key)
    if groq_client is None:
        groq_key = get_api_key("Groq", "GROQ_API_KEY")
        groq_client = Groq(api_key=groq_key)
    if eleven_client is None:
        eleven_key = get_api_key("ElevenLabs", "ELEVEN_API_KEY")
        eleven_client = ElevenLabs(api_key=eleven_key)


PERSONAS = {
    "1": "Persona: Gen-Z Critic. Rules: Use high-energy 'hook' first, no corporate jargon, use modern slang naturally (no cap, bet, vibe).",
    "2": "Persona: Gen Alpha. Rules: Use extreme internet slang (skibidi, fanum tax, rizz, gyatt, ohio). Chaotic energy. Call the viewer 'chat'.",
    "3": "Persona: Old Skool Cool. Rules: 90s slang (da bomb, all that, psych, as if). Boom bap rhythm. References to 90s pop culture.",
    "4": "Persona: Simple / ELI5. Rules: Explain like I'm 5. Very simple words, short sentences. Educational and gentle tone. No jargon.",
    "5": "Persona: Breaking News Anchor. Rules: authoritative, dramatic, urgent. Start with 'BREAKING NEWS'. Formal but gripping.",
    "6": "Persona: William Shakespeare. Rules: Early Modern English. Iambic pentameter. Use 'thee', 'thou', 'verily', 'hark'. Dramatic and poetic."
}

TIME_PERIODS = {
    "1": {"label": "24 hours", "query": "in the last 24 hours"},
    "2": {"label": "3 days", "query": "in the last 3 days"},
    "3": {"label": "1 week", "query": "in the last week"},
    "4": {"label": "1 month", "query": "in the last month"},
    "5": {"label": "3 months", "query": "in the last 3 months"},
    "6": {"label": "6 months", "query": "in the last 6 months"},
    "7": {"label": "1 year", "query": "in the last year"},
    "8": {"label": "5 years", "query": "in the last 5 years"},
}

# Get the root directory (parent of api folder)
ROOT_DIR = Path(__file__).parent.parent

app = Flask(
    __name__,
    static_folder=str(ROOT_DIR / "static"),
    template_folder=str(ROOT_DIR / "templates")
)


def generate_daily_bite(topic: str, persona_prompt: str, time_query: str, time_label: str):
    global tavily, eleven_client, groq_client
    init_clients()
    
    # 1) Search: Get comprehensive news for the selected time period
    search_response = tavily.search(
        query=f"{topic} trends, changes, developments, and key events {time_query}",
        search_depth="advanced",
    )

    context = "\n".join([f"{r['title']}: {r['content']}" for r in search_response["results"]])

    # 2) Brain: Scripting with vibe control
    system_prompt = f"""
    You are a viral content creator. Create a 30-second video script.
    Simple text only in txt format. No need to add headers.
    {persona_prompt}
    Length: Max 75 words.
    
    IMPORTANT: You are summarizing news/trends from the ENTIRE {time_label} period.
    Focus on the overall journey, major shifts, and key milestones during this time only, no need to mention the before.
    If there were ups and downs, mention both. Show the full picture, not just the latest event.
    Example: "Over the past week, gold started strong at $2000, dipped 10% mid-week, then rebounded 25% to close higher."
    Example: "Over the last 24 hours, gold decided to dive nose down into the 4800s waters, where its currently resting and probably holding for the weekend"
    Example: "Over the past 5 years, NVDA stocks were the underdogs, the AI boom brought them so high, and they don't seem to be stopping any time soon"  
    
    Note: If you are mentioning numbers, don't add commas.
    """

    prompt = f"{system_prompt}\n\nContext from {time_label}:\n{context}\n\nDraft the script covering the full {time_label} period:"
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )

    script = response.choices[0].message.content

    # Generate audio and store in memory buffer
    audio_gen = eleven_client.text_to_speech.convert(
        text=script,
        voice_id="iP95p4xoKVk53GoZ742B",
        model_id="eleven_multilingual_v2",
    )

    # Collect audio bytes into buffer
    audio_buffer = BytesIO()
    for chunk in audio_gen:
        audio_buffer.write(chunk)
    audio_buffer.seek(0)

    # Store in cache with unique ID
    audio_id = uuid.uuid4().hex
    slug = topic.replace(" ", "_") or "bite"
    filename = f"bite_{slug}_{audio_id[:8]}.mp3"
    
    audio_cache[audio_id] = {
        "data": audio_buffer.getvalue(),
        "filename": filename,
        "created": time_module.time(),
    }

    return {
        "script": script,
        "audio_id": audio_id,
        "filename": filename,
    }


@app.route("/audio/<audio_id>")
def serve_audio(audio_id):
    """Serve audio from memory buffer."""
    if audio_id not in audio_cache:
        abort(404)
    
    audio_data = audio_cache[audio_id]
    return send_file(
        BytesIO(audio_data["data"]),
        mimetype="audio/mpeg",
        as_attachment=False,
        download_name=audio_data["filename"],
    )


@app.route("/audio/<audio_id>/download")
def download_audio(audio_id):
    """Download audio and remove from cache."""
    if audio_id not in audio_cache:
        abort(404)
    
    audio_data = audio_cache.pop(audio_id)
    return send_file(
        BytesIO(audio_data["data"]),
        mimetype="audio/mpeg",
        as_attachment=True,
        download_name=audio_data["filename"],
    )


@app.route("/", methods=["GET", "POST"])
def index():
    topic = ""
    selected_persona = "1"
    selected_time = "1"
    result = None
    error = None

    if request.method == "POST":
        topic = (request.form.get("topic") or "").strip()
        selected_persona = request.form.get("persona", "1")
        selected_time = request.form.get("time_period", "1")

        if not topic:
            error = "Topic is required."
        else:
            persona_prompt = PERSONAS.get(selected_persona, PERSONAS["1"])
            time_data = TIME_PERIODS.get(selected_time, TIME_PERIODS["1"])
            try:
                generation = generate_daily_bite(topic, persona_prompt, time_data["query"], time_data["label"])
                persona_label = persona_prompt.split(".")[0].replace("Persona:", "").strip()
                audio_url = url_for("serve_audio", audio_id=generation["audio_id"])
                download_url = url_for("download_audio", audio_id=generation["audio_id"])
                result = {
                    "script": generation["script"],
                    "audio_url": audio_url,
                    "download_url": download_url,
                    "filename": generation["filename"],
                    "persona_label": persona_label,
                    "topic": topic,
                    "time_label": time_data["label"],
                }
            except Exception as exc:  # pragma: no cover - network/API errors
                error = f"Failed to generate bite: {exc}"

    return render_template(
        "index.html",
        personas=PERSONAS,
        time_periods=TIME_PERIODS,
        selected_persona=selected_persona,
        selected_time=selected_time,
        topic=topic,
        result=result,
        error=error,
    )


# Vercel expects the app to be named 'app'
# No need for if __name__ == "__main__" for serverless
