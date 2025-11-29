import speech_recognition as sr
import pyttsx3
from typing import TypedDict, Annotated, Optional
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
from typing import Dict, List
import tempfile
from openai import OpenAI

# Travel booking imports
from travel_booking import get_booking_service
from travel_rag import get_travel_rag
from booking_nodes import (
    detect_booking_intent_node,
    extract_entities_node,
    search_travel_node,
    present_options_node,
    handle_selection_node,
    confirm_booking_node
)
from language_support import detect_language_change
from advanced_skills import detect_and_execute_skill

load_dotenv()

# Initialize OpenAI client for Whisper
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Enhanced recognizer
recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.8

# Text-to-speech setup
tts_engine = None
tts_lock = threading.Lock()
USE_GTTS = True

try:
    from gtts import gTTS
    from io import BytesIO
    import pygame
    pygame.mixer.init()
    USE_GTTS = True
    print("✅ Google TTS (gTTS) loaded")
except ImportError:
    USE_GTTS = False
    print("⚠️  gTTS not available, using pyttsx3")

def init_tts_engine():
    """Initialize TTS engine"""
    global tts_engine
    
    if USE_GTTS:
        print("✅ Using Google Text-to-Speech")
        return True
    
    try:
        tts_engine = pyttsx3.init()
        voices = tts_engine.getProperty('voices')
        
        best_voice = None
        preferred_voices = ['zira', 'hazel', 'susan', 'samantha', 'female', 'david']
        
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
        
        if not best_voice and voices:
            best_voice = voices[0].id
        
        if best_voice:
            tts_engine.setProperty('voice', best_voice)
        
        tts_engine.setProperty('rate', 170)
        tts_engine.setProperty('volume', 0.95)
        
        print(f"✅ TTS Engine initialized")
        return True
    except Exception as e:
        print(f"❌ TTS initialization error: {e}")
        return False

init_tts_engine()

# Reminder system
reminders = []
reminder_lock = threading.Lock()

# Speech interrupt flag
is_speaking = False
stop_speaking = False

# Language configuration for Indian regional languages
SUPPORTED_LANGUAGES = {
    "english": {"code": "en", "whisper": "en", "gtts": "en", "name": "English"},
    "hindi": {"code": "hi", "whisper": "hi", "gtts": "hi", "name": "हिंदी"},
    "tamil": {"code": "ta", "whisper": "ta", "gtts": "ta", "name": "தமிழ்"},
    "telugu": {"code": "te", "whisper": "te", "gtts": "te", "name": "తెలుగు"},
    "bengali": {"code": "bn", "whisper": "bn", "gtts": "bn", "name": "বাংলা"},
    "marathi": {"code": "mr", "whisper": "mr", "gtts": "mr", "name": "मराठी"},
    "gujarati": {"code": "gu", "whisper": "gu", "gtts": "gu", "name": "ગુજરાતી"},
    "kannada": {"code": "kn", "whisper": "kn", "gtts": "kn", "name": "ಕನ್ನಡ"},
    "malayalam": {"code": "ml", "whisper": "ml", "gtts": "ml", "name": "മലയാളം"},
    "punjabi": {"code": "pa", "whisper": "pa", "gtts": "pa", "name": "ਪੰਜਾਬੀ"},
    "odia": {"code": "or", "whisper": "or", "gtts": "or", "name": "ଓଡ଼ିଆ"},
    "assamese": {"code": "as", "whisper": "as", "gtts": "as", "name": "অসমীয়া"},
    "urdu": {"code": "ur", "whisper": "ur", "gtts": "ur", "name": "اردو"}
}

# Current language (default: English)
current_language = "english"

# Conversation context
conversation_context = {
    "last_search": None,
    "last_location": None,
    "preferences": {},
    "language": "english"
}

class ConversationState(TypedDict):
    messages: Annotated[list, operator.add]
    user_input: str
    should_continue: bool
    skip_processing: bool
    iteration_count: int
    response_to_speak: str
    context: dict
    # Language field
    language: str  # Current conversation language
    # Booking fields
    booking_intent: Optional[str]  # "flight", "train", "bus", None
    booking_data: dict  # Extracted entities (origin, destination, date, etc.)
    booking_step: str  # "initial", "searching", "presenting", "confirming", "booked"
    search_results: list  # Available travel options
    selected_option: Optional[dict]  # User's selected option

def get_smart_greeting():
    """Simple time-based greeting"""
    indian_tz = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(indian_tz)
    hour = current_time.hour
    day = current_time.strftime("%A")
    time_str = current_time.strftime("%I:%M %p")
    
    if 5 <= hour < 12:
        return f"Good morning! It's {time_str} on {day}. How can I help you?"
    elif 12 <= hour < 17:
        return f"Good afternoon! It's {time_str} on {day}. How can I help you?"
    elif 17 <= hour < 21:
        return f"Good evening! It's {time_str} on {day}. How can I help you?"
    else:
        return f"Hello! It's {time_str} on {day}. How can I help you?"

def speak_text(text: str, priority: bool = False, language: str = None):
    """Enhanced text-to-speech with interrupt capability and multi-language support"""
    global tts_engine, tts_lock, USE_GTTS, is_speaking, stop_speaking, current_language
    
    if not text or text.strip() == "":
        return
    
    # Use provided language or current language
    lang = language or current_language
    lang_code = SUPPORTED_LANGUAGES.get(lang, SUPPORTED_LANGUAGES["english"])["gtts"]
    
    print(f"🔊 Assistant ({SUPPORTED_LANGUAGES[lang]['name']}): {text}")
    
    is_speaking = True
    stop_speaking = False
    
    with tts_lock:
        try:
            text = text.replace("&", "and").replace("@", "at").replace("₹", "rupees")
            text = re.sub(r'http\S+', 'link', text)
            text = re.sub(r'\*+', '', text)
            text = text.replace("_", " ")
            
            if USE_GTTS:
                try:
                    tts = gTTS(text=text, lang=lang_code, slow=False)
                    fp = BytesIO()
                    tts.write_to_fp(fp)
                    fp.seek(0)
                    
                    pygame.mixer.music.load(fp)
                    pygame.mixer.music.play()
                    
                    # Check for interruption while speaking
                    while pygame.mixer.music.get_busy():
                        if stop_speaking:
                            pygame.mixer.music.stop()
                            print("⚠️ Speech interrupted")
                            break
                        time.sleep(0.1)
                    
                    is_speaking = False
                    return
                except Exception as e:
                    print(f"⚠️ gTTS error: {e}")
            
            if tts_engine is None:
                init_tts_engine()
            
            if priority or stop_speaking:
                try:
                    tts_engine.stop()
                except:
                    pass
            
            if not stop_speaking:
                tts_engine.say(text)
                tts_engine.runAndWait()
            
        except Exception as e:
            print(f"⚠️ Speech error: {e}")
        finally:
            is_speaking = False

def get_weather(city: str = "Delhi") -> str:
    """Get weather information"""
    try:
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
        
        webbrowser.open(f"https://www.google.com/search?q=weather+in+{city}")
        return f"Opening weather information for {city}"
    except Exception as e:
        return f"Sorry, couldn't fetch weather. Opening web search."

def get_news(topic: str = "latest") -> str:
    """Get latest news"""
    try:
        if topic and topic != "latest":
            search_url = f"https://news.google.com/search?q={urllib.parse.quote(topic)}"
            webbrowser.open(search_url)
            return f"Opening latest news about {topic}"
        else:
            webbrowser.open("https://news.google.com")
            return "Opening latest news for you"
    except Exception as e:
        return f"Sorry, couldn't fetch news."

def search_web(query: str) -> str:
    """Web search"""
    try:
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(search_url)
        conversation_context["last_search"] = query
        return f"Searching for: {query}"
    except Exception as e:
        return f"Sorry, search failed."

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
    """Open desktop applications"""
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
        return f"Couldn't open {app_name}"

def set_reminder(reminder_text: str, minutes_from_now: int) -> str:
    """Set a reminder"""
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
    return f"Reminder set for {time_str}: {reminder_text}"

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
    """Play music"""
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
        return f"Music playback failed"

def execute_command(text: str) -> Optional[str]:
    """Execute voice commands"""
    text_lower = text.lower().strip()
    
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
    
    # Music
    if "play" in text_lower and any(word in text_lower for word in ["song", "music", "track"]):
        query = text_lower.replace("play", "").replace("song", "").replace("music", "").replace("track", "").strip()
        platform = "spotify" if "spotify" in text_lower else "youtube"
        return play_music(query, platform)
    
    # Reminders
    if "remind" in text_lower or "reminder" in text_lower:
        minutes_match = re.search(r'(\d+)\s*(?:minute|min)', text_lower)
        if minutes_match:
            minutes = int(minutes_match.group(1))
            message = re.sub(r'remind(?:er)?\s+(?:me\s+)?(?:in\s+)?\d+\s*(?:minute|min)s?\s+(?:to\s+)?', '', text_lower).strip()
            return set_reminder(message, minutes)
        return "Please specify time. Example: Remind me in 10 minutes to call John"
    
    return None

def listen_for_speech_whisper():
    """Listen for speech using Whisper API with multi-language support"""
    global current_language
    
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 4000
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 1.0
    
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
            
            # Get language code for Whisper
            lang_code = SUPPORTED_LANGUAGES.get(current_language, SUPPORTED_LANGUAGES["english"])["whisper"]
            
            # Save audio to temporary file
            temp_audio_path = tempfile.mktemp(suffix=".wav")
            with open(temp_audio_path, "wb") as f:
                f.write(audio.get_wav_data())
            
            try:
                print("🔄 Processing with Whisper (fast)...")
                # Use Whisper API with language parameter
                with open(temp_audio_path, "rb") as audio_file:
                    transcript = openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=lang_code  # Use current language
                    )
                
                text = transcript.text.strip()
                
                # Clean up temp file
                os.unlink(temp_audio_path)
                
                if text:
                    print(f"✅ You said: {text}")
                    return text
                else:
                    print("❌ No speech detected")
                    return None
                    
            except Exception as e:
                # Clean up temp file on error
                try:
                    os.unlink(temp_audio_path)
                except:
                    pass
                print(f"❌ Whisper error: {e}")
                speak_text("Sorry, I couldn't process that.")
                return None
                
        except sr.WaitTimeoutError:
            print("⏱️  No speech detected")
            return None
        except Exception as e:
            print(f"❌ Error in speech recognition: {e}")
            return None

def listen_for_wake_word() -> bool:
    """Listen for 'Hey Babitaji' wake word"""
    try:
        with sr.Microphone() as source:
            # Lower energy threshold for wake word detection
            recognizer.energy_threshold = 200
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            
            # Listen for short phrase
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
            
            # Use Whisper for transcription
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_audio.write(audio.get_wav_data())
                temp_audio_path = temp_audio.name
            
            try:
                with open(temp_audio_path, "rb") as audio_file:
                    transcript = openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="en"
                    )
                
                text = transcript.text.strip().lower()
                os.unlink(temp_audio_path)
                
                # Check for wake word variations
                wake_words = ["hey babitaji", "babitaji", "babita", "hey babita"]
                for wake_word in wake_words:
                    if wake_word in text:
                        print(f"✨ Wake word detected: '{text}'")
                        return True
                
                return False
                    
            except Exception as e:
                try:
                    os.unlink(temp_audio_path)
                except:
                    pass
                return False
                
    except sr.WaitTimeoutError:
        return False
    except Exception as e:
        return False

def process_input_node(state: ConversationState) -> ConversationState:
    """Process user input and check for advanced skills"""
    user_input = state["user_input"]
    
    # First, check if this is an advanced skill command
    skill_response = detect_and_execute_skill(user_input)
    if skill_response:
        state["response_to_speak"] = skill_response
        state["skip_processing"] = True
        return state
    
    # Check for exit commands
    if any(word in user_input.lower() for word in ["exit", "quit", "bye", "goodbye", "stop"]):
        state["should_continue"] = False
        state["skip_processing"] = True
        state["response_to_speak"] = "Goodbye! Have a great day!"
        return state
    
    # Add user message to conversation
    state["messages"].append(HumanMessage(content=user_input))
    
    # Continue to LLM for conversational responses
    state["skip_processing"] = False
    return state

def llm_node(state: ConversationState) -> ConversationState:
    """LLM processing node"""
    if state.get("skip_processing", False):
        return state
    
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            streaming=False,
            timeout=15
        )
        
        system_prompt = f"""You are a helpful, friendly voice assistant.
Current time: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%I:%M %p')}

Instructions:
- Give concise, natural responses (1-3 sentences)
- Be warm and conversational
- For complex tasks, guide the user

Context:
- Last search: {conversation_context.get('last_search', 'None')}
"""
        
        messages = [SystemMessage(content=system_prompt)]
        
        # Add conversation history
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
        state["response_to_speak"] = "Sorry, I encountered an error."
    
    return state

def response_node(state: ConversationState) -> ConversationState:
    """Speak the response in the appropriate language"""
    global current_language
    
    if state.get("response_to_speak"):
        # Update current language from state
        current_language = state.get("language", "english")
        speak_text(state["response_to_speak"], language=current_language)
    
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    return state

def should_continue(state: ConversationState) -> str:
    """Determine if conversation should continue"""
    return "continue" if state.get("should_continue", True) else "end"

def create_conversation_graph():
    """Create the conversation workflow graph with booking and language support"""
    workflow = StateGraph(ConversationState)
    
    # Add existing nodes
    workflow.add_node("process_input", process_input_node)
    workflow.add_node("llm_response", llm_node)
    workflow.add_node("speak_response", response_node)
    
    # Add language detection node
    workflow.add_node("detect_language", detect_language_change)
    
    # Add booking nodes
    workflow.add_node("detect_booking", detect_booking_intent_node)
    workflow.add_node("extract_entities", extract_entities_node)
    workflow.add_node("search_travel", search_travel_node)
    workflow.add_node("present_options", present_options_node)
    workflow.add_node("handle_selection", handle_selection_node)
    workflow.add_node("confirm_booking", confirm_booking_node)
    
    # Define conditional routing functions
    def route_after_process(state):
        if state.get("skip_processing"):
            return "speak_response"
        return "detect_language"
    
    def route_after_language(state):
        # If language was changed, skip to speak_response
        if state.get("skip_processing"):
            return "speak_response"
        return "detect_booking"
    
    def route_after_detect(state):
        if state.get("booking_intent"):
            return "extract_entities"
        return "llm_response"
    
    def route_after_extract(state):
        if state.get("booking_step") == "searching":
            return "search_travel"
        return "speak_response"
    
    def route_after_search(state):
        return "present_options"
    
    def route_after_present(state):
        return "speak_response"
    
    # Set entry point
    workflow.set_entry_point("process_input")
    
    # Define edges with conditional routing
    workflow.add_conditional_edges(
        "process_input",
        route_after_process,
        {
            "speak_response": "speak_response",
            "detect_language": "detect_language"
        }
    )
    
    workflow.add_conditional_edges(
        "detect_language",
        route_after_language,
        {
            "speak_response": "speak_response",
            "detect_booking": "detect_booking"
        }
    )
    
    workflow.add_conditional_edges(
        "detect_booking",
        route_after_detect,
        {
            "extract_entities": "extract_entities",
            "llm_response": "llm_response"
        }
    )
    
    workflow.add_conditional_edges(
        "extract_entities",
        route_after_extract,
        {
            "search_travel": "search_travel",
            "speak_response": "speak_response"
        }
    )
    
    workflow.add_edge("search_travel", "present_options")
    workflow.add_edge("present_options", "speak_response")
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
    """Main voice assistant loop with continuous listening"""
    global stop_speaking, is_speaking
    
    print("\n" + "="*60)
    print("🎙️  VOICE ASSISTANT (CONTINUOUS LISTENING)")
    print("="*60)
    print("💡 Just speak - I'm always listening!")
    print("💡 Say 'exit' or 'quit' to stop")
    print("⚡ Using OpenAI Whisper for speech recognition")
    print("="*60 + "\n")
    
    # Greet user
    greeting = get_smart_greeting()
    speak_text(greeting)
    
    # Create conversation graph
    app = create_conversation_graph()
    
    # Conversation state
    config = {"configurable": {"thread_id": "voice_assistant_session"}}
    
    # Persistent booking state across turns
    persistent_booking_state = {
        "booking_intent": None,
        "booking_data": {},
        "booking_step": "initial",
        "search_results": [],
        "selected_option": None
    }
    
    # Main continuous listening loop
    while True:
        try:
            print("\n🎤 Listening... (Speak now)")
            
            # Listen for user command directly
            user_input = listen_for_speech_whisper()
            
            if user_input is None:
                continue
            
            # Check for exit command
            if any(word in user_input.lower() for word in ["exit", "quit", "bye", "goodbye", "stop"]):
                speak_text("Goodbye! Have a great day!")
                print("\n👋 Assistant stopped")
                break
            
            # Process through graph - use persistent booking state and language
            initial_state: ConversationState = {
                "messages": [],
                "user_input": user_input,
                "should_continue": True,
                "skip_processing": False,
                "iteration_count": 0,
                "response_to_speak": "",
                "context": conversation_context,
                "language": current_language,  # Current language
                # Use persistent booking fields
                **persistent_booking_state
            }
            
            # Run conversation graph
            final_state = app.invoke(initial_state, config)
            
            # Update persistent booking state from final state
            persistent_booking_state = {
                "booking_intent": final_state.get("booking_intent"),
                "booking_data": final_state.get("booking_data", {}),
                "booking_step": final_state.get("booking_step", "initial"),
                "search_results": final_state.get("search_results", []),
                "selected_option": final_state.get("selected_option")
            }
                
        except KeyboardInterrupt:
            print("\n\n👋 Assistant stopped by user")
            speak_text("Goodbye! Have a great day!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            speak_text("Sorry, I encountered an error.")
            time.sleep(1)

# Entry point
if __name__ == "__main__":
    try:
        # Check microphone
        print("🔍 Checking microphone...")
        with sr.Microphone() as source:
            print("✅ Microphone detected!")
        
        # Check OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ ERROR: OPENAI_API_KEY not found!")
            print("Set it with: export OPENAI_API_KEY='sk-...'")
            exit(1)
        else:
            print("✅ OpenAI API key found")
        
        # Start assistant
        main()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")