import speech_recognition as sr
import pyttsx3
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
import operator
import webbrowser
import os
from dotenv import load_dotenv
import time
import urllib.parse
import subprocess
import platform
from datetime import datetime, timedelta
import pytz
import json
import re
import threading
from pathlib import Path
import psutil
import requests
from typing import Dict, List, Optional
import wikipedia

load_dotenv()

# IMPROVED: Enhanced recognizer with optimized parameters for better accuracy
recognizer = sr.Recognizer()
recognizer.energy_threshold = 300  # Lower threshold for better detection
recognizer.dynamic_energy_threshold = True
recognizer.dynamic_energy_adjustment_damping = 0.15
recognizer.dynamic_energy_ratio = 1.5
recognizer.pause_threshold = 1.0  # Increased for complete sentences
recognizer.phrase_threshold = 0.3
recognizer.non_speaking_duration = 0.5

# IMPROVED: Google Assistant/Alexa-like TTS with gTTS
tts_engine = None
tts_lock = threading.Lock()
USE_GTTS = True  # Use Google TTS for natural voice

try:
    from gtts import gTTS
    from io import BytesIO
    import pygame
    pygame.mixer.init()
    USE_GTTS = True
    print("✅ Google TTS (gTTS) loaded - Will use natural voice")
except ImportError:
    USE_GTTS = False
    print("⚠️  gTTS not available, using pyttsx3. Install with: pip install gtts pygame")

# NEW: Multilingual support configuration
SUPPORTED_LANGUAGES = {
    # Indian Regional Languages
    "hindi": {"code": "hi", "name": "Hindi", "speech_code": "hi-IN"},
    "bengali": {"code": "bn", "name": "Bengali", "speech_code": "bn-IN"},
    "tamil": {"code": "ta", "name": "Tamil", "speech_code": "ta-IN"},
    "telugu": {"code": "te", "name": "Telugu", "speech_code": "te-IN"},
    "marathi": {"code": "mr", "name": "Marathi", "speech_code": "mr-IN"},
    "gujarati": {"code": "gu", "name": "Gujarati", "speech_code": "gu-IN"},
    "kannada": {"code": "kn", "name": "Kannada", "speech_code": "kn-IN"},
    "malayalam": {"code": "ml", "name": "Malayalam", "speech_code": "ml-IN"},
    "punjabi": {"code": "pa", "name": "Punjabi", "speech_code": "pa-IN"},
    "odia": {"code": "or", "name": "Odia", "speech_code": "or-IN"},
    
    # Frequently Spoken World Languages
    "spanish": {"code": "es", "name": "Spanish", "speech_code": "es-ES"},
    "french": {"code": "fr", "name": "French", "speech_code": "fr-FR"},
    "german": {"code": "de", "name": "German", "speech_code": "de-DE"},
    "chinese": {"code": "zh-CN", "name": "Chinese", "speech_code": "zh-CN"},
    "japanese": {"code": "ja", "name": "Japanese", "speech_code": "ja-JP"},
    "korean": {"code": "ko", "name": "Korean", "speech_code": "ko-KR"},
    "arabic": {"code": "ar", "name": "Arabic", "speech_code": "ar-SA"},
    "russian": {"code": "ru", "name": "Russian", "speech_code": "ru-RU"},
    "portuguese": {"code": "pt", "name": "Portuguese", "speech_code": "pt-PT"},
    "italian": {"code": "it", "name": "Italian", "speech_code": "it-IT"},
    "turkish": {"code": "tr", "name": "Turkish", "speech_code": "tr-TR"},
    "dutch": {"code": "nl", "name": "Dutch", "speech_code": "nl-NL"},
    "polish": {"code": "pl", "name": "Polish", "speech_code": "pl-PL"},
    "thai": {"code": "th", "name": "Thai", "speech_code": "th-TH"},
    "vietnamese": {"code": "vi", "name": "Vietnamese", "speech_code": "vi-VN"},
    "indonesian": {"code": "id", "name": "Indonesian", "speech_code": "id-ID"},
    "english": {"code": "en", "name": "English", "speech_code": "en-US"}
}

# NEW: Current language state
current_language = {
    "code": "en",
    "name": "English",
    "speech_code": "en-US"
}

def init_tts_engine():
    """Initialize TTS engine - Google Assistant style voice"""
    global tts_engine
    
    if USE_GTTS:
        # gTTS provides Google Assistant-like voice
        print("✅ Using Google Text-to-Speech (Natural Voice)")
        return True
    
    # Fallback to pyttsx3
    try:
        tts_engine = pyttsx3.init()
        voices = tts_engine.getProperty('voices')
        
        # Find natural, universal English voice (female preferred like Alexa/Google)
        best_voice = None
        
        # Priority: Female voices sound more like Google Assistant/Alexa
        preferred_voices = [
            'zira',       # Microsoft Zira (US English Female) - Most Alexa-like
            'hazel',      # Natural female voice
            'susan',      # macOS female voice
            'samantha',   # macOS female voice
            'female',     # Any female voice
            'david',      # Fallback male
        ]
        
        # Find best voice
        for preferred in preferred_voices:
            for voice in voices:
                voice_name = voice.name.lower()
                voice_id_lower = voice.id.lower()
                
                if preferred in voice_name or preferred in voice_id_lower:
                    if 'indian' not in voice_name and 'hindi' not in voice_name:
                        best_voice = voice.id
                        print(f"🎙️  Selected voice: {voice.name}")
                        break
            if best_voice:
                break
        
        # Fallback to first English voice
        if not best_voice:
            for voice in voices:
                voice_name = voice.name.lower()
                if 'english' in voice_name and 'female' in voice_name:
                    best_voice = voice.id
                    print(f"🎙️  Selected voice: {voice.name}")
                    break
        
        if not best_voice and voices:
            best_voice = voices[0].id
            print(f"🎙️  Using default voice: {voices[0].name}")
        
        if best_voice:
            tts_engine.setProperty('voice', best_voice)
        
        # Google Assistant/Alexa-like settings
        tts_engine.setProperty('rate', 170)  # Slightly faster, more natural
        tts_engine.setProperty('volume', 0.95)
        
        print(f"✅ TTS Engine initialized (pyttsx3 fallback)")
        return True
    except Exception as e:
        print(f"❌ TTS initialization error: {e}")
        return False

# Initialize TTS at startup
init_tts_engine()

# Advanced reminder system
reminders = []
reminder_lock = threading.Lock()

# Conversation context for better understanding
conversation_context = {
    "last_search": None,
    "last_location": None,
    "preferences": {}
}

class ConversationState(TypedDict):
    messages: Annotated[list, operator.add]
    user_input: str
    should_continue: bool
    skip_processing: bool
    iteration_count: int
    response_to_speak: str
    context: dict

# NEW: Language detection and switching function
def detect_language_switch(text: str) -> Optional[dict]:
    """Detect if user wants to switch language"""
    text_lower = text.lower().strip()
    
    # Check for language switch patterns
    switch_patterns = [
        r'switch (?:to )?(\w+)',
        r'change (?:to )?(\w+)',
        r'speak (?:in )?(\w+)',
        r'talk (?:in )?(\w+)',
        r'use (\w+)',
        r'(\w+) (?:language|mode)'
    ]
    
    for pattern in switch_patterns:
        match = re.search(pattern, text_lower)
        if match:
            lang_name = match.group(1).strip()
            if lang_name in SUPPORTED_LANGUAGES:
                return SUPPORTED_LANGUAGES[lang_name]
    
    return None

# NEW: Get language-specific greeting
def get_smart_greeting_multilingual(lang_code: str = "en") -> str:
    """Intelligent greeting based on time and language"""
    indian_tz = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(indian_tz)
    hour = current_time.hour
    day = current_time.strftime("%A")
    time_str = current_time.strftime("%I:%M %p")
    
    # Language-specific greetings
    greetings = {
        "en": {
            "morning": f"Good morning! It's {time_str} on {day}. Hope you had a great sleep! How can I help you?",
            "afternoon": f"Good afternoon! It's {time_str} on {day}. Hope your day is going well! How can I help you?",
            "evening": f"Good evening! It's {time_str} on {day}. How was your day? How can I help you?",
            "night": f"Good night! It's {time_str} on {day}. Working late? How can I help you?"
        },
        "hi": {
            "morning": f"सुप्रभात! अभी {time_str} बजे हैं {day} को। आपकी नींद अच्छी रही होगी! मैं आपकी कैसे मदद कर सकता हूं?",
            "afternoon": f"नमस्ते! अभी {time_str} बजे हैं {day} को। आपका दिन अच्छा जा रहा होगा! मैं आपकी कैसे मदद कर सकता हूं?",
            "evening": f"शुभ संध्या! अभी {time_str} बजे हैं {day} को। आपका दिन कैसा रहा? मैं आपकी कैसे मदद कर सकता हूं?",
            "night": f"शुभ रात्रि! अभी {time_str} बजे हैं {day} को। देर तक काम कर रहे हैं? मैं आपकी कैसे मदद कर सकता हूं?"
        },
        "es": {
            "morning": f"¡Buenos días! Son las {time_str} del {day}. ¡Espero que hayas dormido bien! ¿Cómo puedo ayudarte?",
            "afternoon": f"¡Buenas tardes! Son las {time_str} del {day}. ¡Espero que tu día vaya bien! ¿Cómo puedo ayudarte?",
            "evening": f"¡Buenas tardes! Son las {time_str} del {day}. ¿Cómo estuvo tu día? ¿Cómo puedo ayudarte?",
            "night": f"¡Buenas noches! Son las {time_str} del {day}. ¿Trabajando hasta tarde? ¿Cómo puedo ayudarte?"
        },
        "fr": {
            "morning": f"Bonjour! Il est {time_str} le {day}. J'espère que vous avez bien dormi! Comment puis-je vous aider?",
            "afternoon": f"Bon après-midi! Il est {time_str} le {day}. J'espère que votre journée se passe bien! Comment puis-je vous aider?",
            "evening": f"Bonsoir! Il est {time_str} le {day}. Comment s'est passée votre journée? Comment puis-je vous aider?",
            "night": f"Bonne nuit! Il est {time_str} le {day}. Vous travaillez tard? Comment puis-je vous aider?"
        }
    }
    
    # Get time-based greeting
    if 5 <= hour < 12:
        time_key = "morning"
    elif 12 <= hour < 17:
        time_key = "afternoon"
    elif 17 <= hour < 21:
        time_key = "evening"
    else:
        time_key = "night"
    
    # Return greeting in current language or English fallback
    if lang_code in greetings:
        return greetings[lang_code][time_key]
    else:
        return greetings["en"][time_key]

def get_smart_greeting():
    """Intelligent greeting based on time and context"""
    return get_smart_greeting_multilingual(current_language["code"])

def speak_text(text: str, priority: bool = False):
    """IMPROVED: Enhanced text-to-speech with multilingual support"""
    global tts_engine, tts_lock, USE_GTTS, current_language
    
    if not text or text.strip() == "":
        return
    
    print(f"🔊 Assistant: {text}")
    
    with tts_lock:
        try:
            # Clean text for better speech
            text = text.replace("&", "and").replace("@", "at").replace("₹", "rupees")
            text = re.sub(r'http\S+', 'link', text)  # Replace URLs
            text = re.sub(r'\*+', '', text)  # Remove asterisks
            text = text.replace("_", " ")  # Replace underscores
            
            # NEW: Use gTTS with current language
            if USE_GTTS:
                try:
                    # Use gTTS for multilingual support
                    tts = gTTS(text=text, lang=current_language["code"], slow=False)
                    
                    # Save to temporary buffer
                    fp = BytesIO()
                    tts.write_to_fp(fp)
                    fp.seek(0)
                    
                    # Play using pygame
                    pygame.mixer.music.load(fp)
                    pygame.mixer.music.play()
                    
                    # Wait for playback to finish
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                    
                    return
                except Exception as e:
                    print(f"⚠️ gTTS error: {e}, falling back to pyttsx3")
            
            # Fallback to pyttsx3
            # Ensure engine is initialized
            if tts_engine is None:
                init_tts_engine()
            
            if priority:
                try:
                    tts_engine.stop()
                except:
                    pass
            
            # Speak with error recovery
            tts_engine.say(text)
            tts_engine.runAndWait()
            
        except Exception as e:
            print(f"⚠️ Speech error: {e}")
            # Try to reinitialize and retry
            try:
                time.sleep(0.3)
                if init_tts_engine():
                    tts_engine.say(text)
                    tts_engine.runAndWait()
            except Exception as e2:
                print(f"❌ Could not speak response: {e2}")

def get_weather(city: str = "Delhi") -> str:
    """Get weather information"""
    try:
        # Using OpenWeatherMap API (you'll need to add API key in .env)
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if api_key:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if response.status_code == 200:
                temp = data['main']['temp']
                feels_like = data['main']['feels_like']
                description = data['weather'][0]['description']
                humidity = data['main']['humidity']
                
                return f"Weather in {city}: {temp}°C, feels like {feels_like}°C. {description}. Humidity: {humidity}%"
        
        # Fallback: Open weather website
        webbrowser.open(f"https://www.google.com/search?q=weather+in+{city}")
        return f"Opening weather information for {city}"
    except Exception as e:
        print(f"Weather error: {e}")
        return f"Sorry, couldn't fetch weather. Opening web search."

def get_news(topic: str = "latest") -> str:
    """Get latest news"""
    try:
        news_sites = [
            "https://news.google.com",
            "https://www.bbc.com/news",
            "https://timesofindia.indiatimes.com"
        ]
        
        if topic and topic != "latest":
            search_url = f"https://news.google.com/search?q={urllib.parse.quote(topic)}"
            webbrowser.open(search_url)
            return f"Opening latest news about {topic}"
        else:
            webbrowser.open(news_sites[0])
            return "Opening latest news for you"
    except Exception as e:
        return f"Sorry, couldn't fetch news. Error: {str(e)}"

def search_web(query: str) -> str:
    """Enhanced web search with multiple engines"""
    try:
        # Try to get quick answer from Wikipedia first
        try:
            summary = wikipedia.summary(query, sentences=2)
            return f"Here's what I found: {summary}. Would you like more details?"
        except:
            pass
        
        # Open web search
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(search_url)
        conversation_context["last_search"] = query
        return f"Searching for: {query}"
    except Exception as e:
        return f"Sorry, search failed. Error: {str(e)}"

def get_system_info() -> str:
    """Get system information"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        battery = psutil.sensors_battery()
        
        info = f"CPU usage: {cpu_percent}%. Memory usage: {memory.percent}%."
        
        if battery:
            info += f" Battery: {battery.percent}%"
            if battery.power_plugged:
                info += " (charging)"
        
        return info
    except Exception as e:
        return "Sorry, couldn't fetch system information"

def open_application(app_name: str) -> str:
    """Open desktop applications intelligently"""
    system = platform.system()
    app_name = app_name.lower()
    
    apps = {
        "calculator": {
            "Darwin": "Calculator",
            "Windows": "calc.exe",
            "Linux": "gnome-calculator"
        },
        "notepad": {
            "Darwin": "TextEdit",
            "Windows": "notepad.exe",
            "Linux": "gedit"
        },
        "terminal": {
            "Darwin": "Terminal",
            "Windows": "cmd.exe",
            "Linux": "gnome-terminal"
        }
    }
    
    try:
        if app_name in apps:
            app = apps[app_name].get(system)
            if system == "Darwin":
                subprocess.Popen(["open", "-a", app])
            elif system == "Windows":
                subprocess.Popen(app)
            else:
                subprocess.Popen(app)
            return f"Opening {app_name}"
        else:
            return f"Sorry, I don't know how to open {app_name}"
    except Exception as e:
        return f"Couldn't open {app_name}. Error: {str(e)}"

def search_flights(origin: str, destination: str, date: Optional[str] = None) -> str:
    """Enhanced flight search with multiple options"""
    try:
        sites = [
            f"https://www.google.com/travel/flights?q=flights+from+{origin}+to+{destination}",
            f"https://www.skyscanner.com/transport/flights/{origin}/{destination}",
            f"https://www.makemytrip.com/flight/search?fromCity={origin}&toCity={destination}"
        ]
        
        conversation_context["last_location"] = {"origin": origin, "destination": destination}
        
        for i, site in enumerate(sites[:2]):
            webbrowser.open(site)
            if i < len(sites) - 1:
                time.sleep(1)
        
        return f"Searching flights from {origin} to {destination}. I've opened comparison sites for best deals."
    except Exception as e:
        return f"Flight search failed: {str(e)}"

def search_trains(origin: str, destination: str, date: Optional[str] = None) -> str:
    """Enhanced train search"""
    try:
        sites = [
            "https://www.irctc.co.in/nget/train-search",
            f"https://www.confirmtkt.com/trains/{origin}-to-{destination}",
            f"https://www.railyatri.in/train-ticket/trains-from-{origin}-to-{destination}"
        ]
        
        for i, site in enumerate(sites[:2]):
            webbrowser.open(site)
            if i < len(sites) - 1:
                time.sleep(1)
        
        return f"Searching trains from {origin} to {destination}. Check the tabs for schedules and availability."
    except Exception as e:
        return f"Train search failed: {str(e)}"

def search_cabs(origin: str, destination: str) -> str:
    """Smart cab booking"""
    try:
        services = ["Uber", "Ola", "Rapido"]
        sites = [
            "https://www.uber.com",
            "https://www.olacabs.com",
            "https://www.rapido.bike"
        ]
        
        for i, site in enumerate(sites):
            webbrowser.open(site)
            if i < len(sites) - 1:
                time.sleep(0.5)
        
        return f"I've opened {', '.join(services)} for you. Compare prices and book the best option!"
    except Exception as e:
        return f"Cab search failed: {str(e)}"

def search_buses(origin: str, destination: str, date: Optional[str] = None) -> str:
    """Enhanced bus search"""
    try:
        sites = [
            f"https://www.redbus.in/bus-tickets/{origin.lower()}-to-{destination.lower()}",
            f"https://www.abhibus.com/{origin}-to-{destination}",
            f"https://www.makemytrip.com/bus-tickets/{origin}-to-{destination}"
        ]
        
        for i, site in enumerate(sites[:2]):
            webbrowser.open(site)
            if i < len(sites) - 1:
                time.sleep(1)
        
        return f"Searching buses from {origin} to {destination}. Check both tabs for best prices."
    except Exception as e:
        return f"Bus search failed: {str(e)}"

def set_reminder(reminder_text: str, minutes_from_now: int) -> str:
    """Enhanced reminder system"""
    global reminders
    
    reminder_time = datetime.now() + timedelta(minutes=minutes_from_now)
    reminder_data = {
        "text": reminder_text,
        "time": reminder_time,
        "triggered": False
    }
    
    with reminder_lock:
        reminders.append(reminder_data)
    
    threading.Thread(target=trigger_reminder, args=(reminder_data,), daemon=True).start()
    
    time_str = reminder_time.strftime('%I:%M %p')
    return f"Reminder set for {time_str}: {reminder_text}. I'll alert you!"

def trigger_reminder(reminder_data: dict):
    """Trigger reminder at specified time"""
    time_diff = (reminder_data["time"] - datetime.now()).total_seconds()
    if time_diff > 0:
        time.sleep(time_diff)
    
    if not reminder_data["triggered"]:
        reminder_data["triggered"] = True
        message = f"⏰ REMINDER: {reminder_data['text']}"
        print(f"\n{message}")
        speak_text(message, priority=True)

def play_music(song_name: str, platform: str = "youtube") -> str:
    """Enhanced music playback"""
    try:
        if platform == "spotify":
            query = urllib.parse.quote(song_name)
            spotify_url = f"https://open.spotify.com/search/{query}"
            webbrowser.open(spotify_url)
            return f"Playing {song_name} on Spotify"
        else:
            query = urllib.parse.quote(song_name)
            youtube_url = f"https://www.youtube.com/results?search_query={query}"
            webbrowser.open(youtube_url)
            return f"Playing {song_name} on YouTube"
    except Exception as e:
        return f"Music playback failed: {str(e)}"

def execute_command(text: str) -> Optional[str]:
    """Enhanced command execution with better pattern matching"""
    global current_language
    
    text_lower = text.lower().strip()
    
    # NEW: Check for language switch FIRST
    lang_switch = detect_language_switch(text)
    if lang_switch:
        old_lang = current_language["name"]
        current_language = lang_switch
        print(f"🌍 Language switched to: {current_language['name']}")
        
        # Response in new language
        responses = {
            "en": f"Language switched to {current_language['name']}. I'll now speak in {current_language['name']}.",
            "hi": f"भाषा बदल गई है। अब मैं {current_language['name']} में बात करूंगा।",
            "es": f"Idioma cambiado a {current_language['name']}. Ahora hablaré en {current_language['name']}.",
            "fr": f"Langue changée en {current_language['name']}. Je parlerai maintenant en {current_language['name']}.",
            "de": f"Sprache gewechselt zu {current_language['name']}. Ich werde jetzt auf {current_language['name']} sprechen.",
            "zh-CN": f"语言已切换到{current_language['name']}。我现在将使用{current_language['name']}。",
            "ja": f"言語を{current_language['name']}に切り替えました。これから{current_language['name']}で話します。",
            "ar": f"تم تبديل اللغة إلى {current_language['name']}. سأتحدث الآن باللغة {current_language['name']}.",
            "ru": f"Язык переключен на {current_language['name']}. Теперь я буду говорить на {current_language['name']}."
        }
        
        response = responses.get(current_language["code"], responses["en"])
        return response
    
    # System commands
    if any(word in text_lower for word in ["system info", "system status", "battery", "cpu"]):
        return get_system_info()
    
    # Weather
    if "weather" in text_lower:
        match = re.search(r'weather (?:in |at |for )?(.+?)(?:\s|$)', text_lower)
        city = match.group(1).strip() if match else "Delhi"
        return get_weather(city)
    
    # News
    if "news" in text_lower:
        match = re.search(r'news (?:about |on )?(.+?)(?:\s|$)', text_lower)
        topic = match.group(1).strip() if match else "latest"
        return get_news(topic)
    
    # Web search
    if any(phrase in text_lower for phrase in ["search for", "look up", "find information about", "google"]):
        query = text_lower
        for phrase in ["search for", "look up", "find information about", "google"]:
            query = query.replace(phrase, "").strip()
        if query:
            return search_web(query)
    
    # Time queries
    if any(phrase in text_lower for phrase in ["what time", "current time", "time in india"]):
        indian_tz = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(indian_tz)
        return f"The current time in India is {current_time.strftime('%I:%M %p on %A, %B %d, %Y')}"
    
    # Date queries
    if "what" in text_lower and ("date" in text_lower or "day" in text_lower):
        current = datetime.now(pytz.timezone('Asia/Kolkata'))
        return f"Today is {current.strftime('%A, %B %d, %Y')}"
    
    # Application opening
    if "open" in text_lower and any(app in text_lower for app in ["calculator", "notepad", "terminal"]):
        for app in ["calculator", "notepad", "terminal"]:
            if app in text_lower:
                return open_application(app)
    
    # Website shortcuts
    websites = {
        "youtube": "https://www.youtube.com",
        "netflix": "https://www.netflix.com",
        "amazon prime": "https://www.primevideo.com",
        "prime video": "https://www.primevideo.com",
        "google": "https://www.google.com",
        "gmail": "https://mail.google.com",
        "spotify": "https://open.spotify.com",
        "twitter": "https://www.twitter.com",
        "instagram": "https://www.instagram.com",
        "facebook": "https://www.facebook.com",
        "linkedin": "https://www.linkedin.com",
        "github": "https://www.github.com"
    }
    
    if "open" in text_lower:
        for site, url in websites.items():
            if site in text_lower:
                webbrowser.open(url)
                return f"Opening {site.title()}"
    
    # Flight search
    if "flight" in text_lower or "flights" in text_lower:
        match = re.search(r'from (.+?) to (.+?)(?:\s|$)', text_lower)
        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()
            return search_flights(origin, destination)
        else:
            return "Please say: Find flights from [city] to [city]"
    
    # Train search
    if "train" in text_lower:
        match = re.search(r'from (.+?) to (.+?)(?:\s|$)', text_lower)
        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()
            return search_trains(origin, destination)
        else:
            return "Please say: Find trains from [city] to [city]"
    
    # Cab search
    if "cab" in text_lower or "taxi" in text_lower or "uber" in text_lower or "ola" in text_lower:
        match = re.search(r'from (.+?) to (.+?)(?:\s|$)', text_lower)
        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()
            return search_cabs(origin, destination)
        else:
            return search_cabs("current location", "destination")
    
    # Bus search
    if "bus" in text_lower:
        match = re.search(r'from (.+?) to (.+?)(?:\s|$)', text_lower)
        if match:
            origin = match.group(1).strip()
            destination = match.group(2).strip()
            return search_buses(origin, destination)
        else:
            return "Please say: Find buses from [city] to [city]"
    
    # Music
    if "play" in text_lower and any(word in text_lower for word in ["song", "music", "track"]):
        query = text_lower.replace("play", "").replace("song", "").replace("music", "").replace("track", "").strip()
        platform = "spotify" if "spotify" in text_lower else "youtube"
        return play_music(query, platform)
    
    # Reminders
    if "remind" in text_lower or "reminder" in text_lower:
        # Extract time and message
        minutes_match = re.search(r'(\d+)\s*(?:minute|min)', text_lower)
        if minutes_match:
            minutes = int(minutes_match.group(1))
            message = re.sub(r'remind(?:er)?\s+(?:me\s+)?(?:in\s+)?\d+\s*(?:minute|min)s?\s+(?:to\s+)?', '', text_lower).strip()
            return set_reminder(message, minutes)
        else:
            return "Please specify time. Example: Remind me in 10 minutes to call John"
    
    # No command matched
    return None


def listen_for_speech() -> Optional[str]:
    """Listen for user speech with improved error handling"""
    try:
        with sr.Microphone() as source:
            print("\n🎤 Listening... (Speak now)")
            
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            # Listen with timeout
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            print("🔄 Processing speech...")
            
            # Use current language for recognition
            speech_lang = current_language["speech_code"]
            
            # Try Google Speech Recognition with current language
            try:
                text = recognizer.recognize_google(audio, language=speech_lang)
                print(f"✅ You said: {text}")
                return text
            except sr.UnknownValueError:
                print("❌ Could not understand audio")
                speak_text("Sorry, I didn't catch that. Could you repeat?")
                return None
            except sr.RequestError as e:
                print(f"❌ Speech recognition error: {e}")
                speak_text("Sorry, speech recognition service is unavailable")
                return None
                
    except sr.WaitTimeoutError:
        print("⏱️  No speech detected (timeout)")
        return None
    except Exception as e:
        print(f"❌ Microphone error: {e}")
        speak_text("Sorry, I'm having trouble with the microphone")
        return None


def process_input_node(state: ConversationState) -> ConversationState:
    """Process user input and determine action"""
    user_input = state["user_input"].lower().strip()
    
    # Check for exit commands
    if any(word in user_input for word in ["exit", "quit", "bye", "goodbye", "stop"]):
        state["should_continue"] = False
        state["skip_processing"] = True
        state["response_to_speak"] = "Goodbye! Have a great day!"
        return state
    
    # Try to execute direct command first
    command_result = execute_command(user_input)
    if command_result:
        state["response_to_speak"] = command_result
        state["skip_processing"] = True  # Skip LLM if command handled
        return state
    
    # Continue to LLM for conversational responses
    state["skip_processing"] = False
    return state


def llm_node(state: ConversationState) -> ConversationState:
    """LLM processing node with context awareness"""
    if state.get("skip_processing", False):
        return state
    
    try:
        # Initialize LLM
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            streaming=False
        )
        
        # Build context-aware system message
        system_prompt = f"""You are a helpful, friendly voice assistant similar to Google Assistant or Alexa.
Current language: {current_language['name']}
Current time: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p')}

Instructions:
- Give concise, natural responses (1-3 sentences)
- Be warm and conversational
- Respond in {current_language['name']} if requested
- For complex tasks, guide the user
- If you don't know something, say so politely

Context:
- Last search: {conversation_context.get('last_search', 'None')}
- Last location: {conversation_context.get('last_location', 'None')}
"""
        
        # Prepare messages
        messages = [SystemMessage(content=system_prompt)]
        
        # Add conversation history (last 5 messages)
        recent_messages = state["messages"][-10:] if len(state["messages"]) > 10 else state["messages"]
        messages.extend(recent_messages)
        
        # Add current user input
        messages.append(HumanMessage(content=state["user_input"]))
        
        # Get LLM response
        response = llm.invoke(messages)
        ai_message = response.content
        
        # Update state
        state["messages"].append(HumanMessage(content=state["user_input"]))
        state["messages"].append(AIMessage(content=ai_message))
        state["response_to_speak"] = ai_message
        
    except Exception as e:
        print(f"❌ LLM Error: {e}")
        state["response_to_speak"] = "Sorry, I encountered an error processing that request."
    
    return state


def response_node(state: ConversationState) -> ConversationState:
    """Speak the response"""
    if state.get("response_to_speak"):
        speak_text(state["response_to_speak"])
    
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    return state


def should_continue(state: ConversationState) -> str:
    """Determine if conversation should continue"""
    return "continue" if state.get("should_continue", True) else "end"


def create_conversation_graph():
    """Create the conversation workflow graph"""
    workflow = StateGraph(ConversationState)
    
    # Add nodes
    workflow.add_node("process_input", process_input_node)
    workflow.add_node("llm_response", llm_node)
    workflow.add_node("speak_response", response_node)
    
    # Define edges
    workflow.set_entry_point("process_input")
    workflow.add_edge("process_input", "llm_response")
    workflow.add_edge("llm_response", "speak_response")
    workflow.add_conditional_edges(
        "speak_response",
        should_continue,
        {
            "continue": END,
            "end": END
        }
    )
    
    # Compile with memory
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


def main():
    """Main voice assistant loop"""
    print("\n" + "="*60)
    print("🎙️  MULTILINGUAL VOICE ASSISTANT")
    print("="*60)
    print(f"📍 Current Language: {current_language['name']}")
    print("💡 Say 'switch to [language]' to change language")
    print("💡 Supported: English, Hindi, Spanish, French, German, Chinese, Japanese, Arabic, and more")
    print("💡 Say 'exit' or 'quit' to stop")
    print("="*60 + "\n")
    
    # Greet user
    greeting = get_smart_greeting()
    speak_text(greeting)
    
    # Create conversation graph
    app = create_conversation_graph()
    
    # Conversation state
    config = {"configurable": {"thread_id": "voice_assistant_session"}}
    
    # Main loop
    while True:
        try:
            # Listen for user input
            user_input = listen_for_speech()
            
            if user_input is None:
                continue  # No speech detected, try again
            
            # Process through graph
            initial_state: ConversationState = {
                "messages": [],
                "user_input": user_input,
                "should_continue": True,
                "skip_processing": False,
                "iteration_count": 0,
                "response_to_speak": "",
                "context": conversation_context
            }
            
            # Run conversation graph
            final_state = app.invoke(initial_state, config)
            
            # Check if we should exit
            if not final_state.get("should_continue", True):
                print("\n👋 Voice Assistant stopped")
                break
                
        except KeyboardInterrupt:
            print("\n\n👋 Voice Assistant stopped by user")
            speak_text("Goodbye! Have a great day!")
            break
        except Exception as e:
            print(f"\n❌ Error in main loop: {e}")
            speak_text("Sorry, I encountered an error. Let's try again.")
            time.sleep(1)


# Entry point
if __name__ == "__main__":
    try:
        # Check microphone availability
        print("🔍 Checking microphone...")
        with sr.Microphone() as source:
            print("✅ Microphone detected!")
        
        # Start assistant
        main()
        
    except OSError as e:
        print(f"\n❌ MICROPHONE ERROR: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check System Preferences → Security & Privacy → Microphone")
        print("2. Grant Terminal/Python microphone access")
        print("3. Ensure microphone is connected and working")
        print("4. Try: brew install portaudio && pip install pyaudio")
    except Exception as e:
        print(f"\n❌ STARTUP ERROR: {e}")
        print("\n🔧 Try reinstalling dependencies:")
        print("pip install -r requirements.txt")