import os
import getpass
from dotenv import load_dotenv
from tavily import TavilyClient
import google.generativeai as genai
from elevenlabs import save
from elevenlabs.client import ElevenLabs

# Load environment variables from .env file
load_dotenv()

def get_api_key(name, env_var):
    key = os.getenv(env_var)
    if not key:
        key = getpass.getpass(f"Please enter your {name} API Key: ")
    return key

# Initialize Clients
tavily_key = get_api_key("Tavily", "TAVILY_API_KEY")
tavily = TavilyClient(api_key=tavily_key)

gemini_key = get_api_key("Gemini", "GEMINI_API_KEY")
genai.configure(api_key=gemini_key)

eleven_key = get_api_key("ElevenLabs", "ELEVEN_API_KEY")
eleven_client = ElevenLabs(api_key=eleven_key)

def generate_daily_bite(topic: str, persona_prompt: str):
    print(f"🚀 Scouting trends for: {topic}...")

    # 1. SEARCH: Get the pulse of the last 24 hours
    search_response = tavily.search(
        query=f"breaking news and viral trends about {topic} in the last 24 hours",
        search_depth="advanced"
    )
    
    context = "\n".join([f"{r['title']}: {r['content']}" for r in search_response['results']])

    # 2. BRAIN: Scripting with "Vibe" Control
    system_prompt = f"""
    You are a viral content creator. Create a 30-second video script.
    Simple text only in txt format. No need to add headers.
    {persona_prompt}
    Length: Max 75 words.
    """
    
    model = genai.GenerativeModel("gemini-3-flash-preview")
    response = model.generate_content(
        f"{system_prompt}\n\nContext:\n{context}\n\nDraft the script:"
    )
    
    script = response.text
    print(f"📝 Script: {script}")

    audio_gen = eleven_client.text_to_speech.convert(
        text=script,
        voice_id="iP95p4xoKVk53GoZ742B",
        model_id="eleven_multilingual_v2"
    )

    # 4. SAVE: Store for video processing
    file_path = f"bite_{topic.replace(' ', '_')}.mp3"
    save(audio_gen, file_path)
    
    return {"script": script, "audio_file": file_path}

if __name__ == "__main__":
    # Example Run
    topic = input("Enter a topic: ")
    
    print("Choose a persona:")
    print("1. Gen Z (The default Zoomer vibe)")
    print("2. Gen Alpha (Brainrot energy)")
    print("3. Old Skool (90s cool)")
    print("4. Simple (ELI5)")
    print("5. News Anchor (Serious business)")
    print("6. Shakespearian (The Bard)")
    
    choice = input("Enter your choice (1-6): ").strip()
    
    personas = {
        "1": "Persona: Gen-Z Tech Critic. Rules: Use high-energy 'hook' first, no corporate jargon, use modern slang naturally (no cap, bet, vibe).",
        "2": "Persona: Gen Alpha. Rules: Use extreme internet slang (skibidi, fanum tax, rizz, gyatt, ohio). Chaotic energy. Call the viewer 'chat'.",
        "3": "Persona: Old Skool Cool. Rules: 90s slang (da bomb, all that, psych, as if). Boom bap rhythm. References to 90s pop culture.",
        "4": "Persona: Simple / ELI5. Rules: Explain like I'm 5. Very simple words, short sentences. Educational and gentle tone. No jargon.",
        "5": "Persona: Breaking News Anchor. Rules: authoritative, dramatic, urgent. Start with 'BREAKING NEWS'. Formal but gripping.",
        "6": "Persona: William Shakespeare. Rules: Early Modern English. Iambic pentameter. Use 'thee', 'thou', 'verily', 'hark'. Dramatic and poetic."
    }
    
    selected_persona = personas.get(choice, personas["1"])
    
    result = generate_daily_bite(topic, selected_persona)
    print(f"✅ Ready for video assembly: {result['audio_file']}")