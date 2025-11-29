"""
Advanced Skills Module for World-Class Voice Assistant
Implements weather, calculations, timers, news, web search, and more
"""

import requests
import json
import re
from datetime import datetime, timedelta
import threading
import time
import math
from typing import Optional, Dict, Any
import wikipedia

# ============================================================================
# WEATHER SKILL
# ============================================================================

def get_weather(city: str = "Delhi") -> str:
    """Get current weather for a city"""
    try:
        # Using wttr.in - no API key needed
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        current = data['current_condition'][0]
        temp_c = current['temp_C']
        feels_like = current['FeelsLikeC']
        humidity = current['humidity']
        weather_desc = current['weatherDesc'][0]['value']
        
        return f"Weather in {city}: {weather_desc}, {temp_c}°C (feels like {feels_like}°C), humidity {humidity}%"
    except Exception as e:
        return f"Sorry, I couldn't fetch weather information for {city}"

def get_weather_forecast(city: str = "Delhi", days: int = 3) -> str:
    """Get weather forecast for next few days"""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        forecast_text = f"Weather forecast for {city}:\n"
        for i, day in enumerate(data['weather'][:days]):
            date = day['date']
            max_temp = day['maxtempC']
            min_temp = day['mintempC']
            desc = day['hourly'][0]['weatherDesc'][0]['value']
            forecast_text += f"{date}: {desc}, {min_temp}°C to {max_temp}°C\n"
        
        return forecast_text.strip()
    except Exception as e:
        return f"Sorry, I couldn't fetch forecast for {city}"

# ============================================================================
# CALCULATION SKILL
# ============================================================================

def calculate(expression: str) -> str:
    """Perform mathematical calculations"""
    try:
        # Clean the expression
        expression = expression.lower()
        expression = expression.replace('x', '*').replace('×', '*').replace('÷', '/')
        expression = expression.replace('plus', '+').replace('minus', '-')
        expression = expression.replace('times', '*').replace('divided by', '/')
        expression = expression.replace('squared', '**2').replace('cubed', '**3')
        
        # Handle special functions
        if 'square root' in expression or 'sqrt' in expression:
            num = re.search(r'(\d+\.?\d*)', expression)
            if num:
                result = math.sqrt(float(num.group(1)))
                return f"The square root is {result}"
        
        if 'factorial' in expression:
            num = re.search(r'(\d+)', expression)
            if num:
                result = math.factorial(int(num.group(1)))
                return f"The factorial is {result}"
        
        # Extract numbers and operators
        clean_expr = re.sub(r'[^0-9+\-*/().\s]', '', expression)
        
        # Evaluate safely
        result = eval(clean_expr, {"__builtins__": {}}, {"math": math})
        return f"The answer is {result}"
    except Exception as e:
        return "Sorry, I couldn't calculate that. Please try again."

def convert_units(value: float, from_unit: str, to_unit: str) -> str:
    """Convert between different units"""
    conversions = {
        # Temperature
        ('celsius', 'fahrenheit'): lambda x: (x * 9/5) + 32,
        ('fahrenheit', 'celsius'): lambda x: (x - 32) * 5/9,
        ('celsius', 'kelvin'): lambda x: x + 273.15,
        ('kelvin', 'celsius'): lambda x: x - 273.15,
        
        # Distance
        ('km', 'miles'): lambda x: x * 0.621371,
        ('miles', 'km'): lambda x: x * 1.60934,
        ('meters', 'feet'): lambda x: x * 3.28084,
        ('feet', 'meters'): lambda x: x * 0.3048,
        
        # Weight
        ('kg', 'pounds'): lambda x: x * 2.20462,
        ('pounds', 'kg'): lambda x: x * 0.453592,
    }
    
    key = (from_unit.lower(), to_unit.lower())
    if key in conversions:
        result = conversions[key](value)
        return f"{value} {from_unit} is {result:.2f} {to_unit}"
    else:
        return f"Sorry, I don't know how to convert {from_unit} to {to_unit}"

# ============================================================================
# TIMER & REMINDER SKILL
# ============================================================================

active_timers = {}

def set_timer(duration_minutes: int, message: str = "Timer finished") -> str:
    """Set a timer"""
    timer_id = len(active_timers) + 1
    
    def timer_callback():
        time.sleep(duration_minutes * 60)
        print(f"\n⏰ TIMER ALERT: {message}")
        # You can add TTS here to speak the message
        if timer_id in active_timers:
            del active_timers[timer_id]
    
    thread = threading.Thread(target=timer_callback, daemon=True)
    thread.start()
    active_timers[timer_id] = {'duration': duration_minutes, 'message': message}
    
    return f"Timer set for {duration_minutes} minutes: {message}"

def set_reminder(time_str: str, message: str) -> str:
    """Set a reminder for a specific time"""
    try:
        # Parse time (simple format: HH:MM)
        reminder_time = datetime.strptime(time_str, "%H:%M").time()
        now = datetime.now()
        reminder_datetime = datetime.combine(now.date(), reminder_time)
        
        if reminder_datetime < now:
            reminder_datetime += timedelta(days=1)
        
        delay_seconds = (reminder_datetime - now).total_seconds()
        
        def reminder_callback():
            time.sleep(delay_seconds)
            print(f"\n🔔 REMINDER: {message}")
        
        thread = threading.Thread(target=reminder_callback, daemon=True)
        thread.start()
        
        return f"Reminder set for {time_str}: {message}"
    except Exception as e:
        return "Sorry, I couldn't set that reminder. Use format HH:MM (e.g., 14:30)"

# ============================================================================
# NEWS SKILL
# ============================================================================

def get_news(category: str = "general", country: str = "in") -> str:
    """Get latest news headlines"""
    try:
        # Using NewsAPI (you'll need an API key for production)
        # For now, using a free alternative
        url = f"https://newsapi.org/v2/top-headlines?country={country}&category={category}&apiKey=YOUR_API_KEY"
        
        # Alternative: Use RSS feeds
        # For demo, return sample news
        categories_map = {
            "general": "Top Headlines",
            "technology": "Technology News",
            "sports": "Sports Updates",
            "business": "Business News",
            "entertainment": "Entertainment News"
        }
        
        return f"Here are the latest {categories_map.get(category, 'general')} headlines. (Note: Connect NewsAPI for real-time news)"
    except Exception as e:
        return "Sorry, I couldn't fetch news right now"

# ============================================================================
# WEB SEARCH & INFORMATION SKILL
# ============================================================================

def search_wikipedia(query: str) -> str:
    """Search Wikipedia for information"""
    try:
        wikipedia.set_lang("en")
        summary = wikipedia.summary(query, sentences=2)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Multiple results found. Please be more specific. Options: {', '.join(e.options[:5])}"
    except wikipedia.exceptions.PageError:
        return f"Sorry, I couldn't find information about '{query}'"
    except Exception as e:
        return "Sorry, I couldn't search for that information"

def get_quick_fact(topic: str) -> str:
    """Get a quick fact about a topic"""
    try:
        result = search_wikipedia(topic)
        return f"Here's what I found: {result}"
    except Exception as e:
        return f"Sorry, I couldn't find information about {topic}"

# ============================================================================
# FUN & ENTERTAINMENT SKILL
# ============================================================================

import random

JOKES = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "Why did the scarecrow win an award? He was outstanding in his field!",
    "Why don't eggs tell jokes? They'd crack each other up!",
    "What do you call a fake noodle? An impasta!",
    "Why did the bicycle fall over? It was two-tired!",
    "What do you call a bear with no teeth? A gummy bear!",
    "Why couldn't the bicycle stand up? It was two tired!",
    "What did one wall say to the other? I'll meet you at the corner!",
]

def tell_joke() -> str:
    """Tell a random joke"""
    return random.choice(JOKES)

def get_fun_fact() -> str:
    """Get a random fun fact"""
    facts = [
        "Honey never spoils. Archaeologists have found 3000-year-old honey in Egyptian tombs that's still edible!",
        "A group of flamingos is called a 'flamboyance'.",
        "Octopuses have three hearts and blue blood!",
        "Bananas are berries, but strawberries aren't!",
        "The shortest war in history lasted 38 minutes between Britain and Zanzibar.",
    ]
    return random.choice(facts)

# ============================================================================
# MUSIC & VIDEO PLAYBACK SKILL
# ============================================================================

import webbrowser
import urllib.parse

def play_music(query: str, platform: str = "youtube") -> str:
    """Play music/video on YouTube, Spotify, or other platforms"""
    try:
        query_encoded = urllib.parse.quote(query)
        
        if platform == "youtube" or platform == "yt":
            # YouTube - Use direct watch URL with search query (auto-plays first result)
            # Format: youtube.com/results?search_query=QUERY then auto-click first result
            # Better approach: Use a direct link that searches and plays
            youtube_search_url = f"https://www.youtube.com/results?search_query={query_encoded}"
            
            # Alternative: Try to get video ID and play directly
            try:
                import requests
                # Search YouTube and get first video ID
                search_url = f"https://www.youtube.com/results?search_query={query_encoded}"
                response = requests.get(search_url, timeout=5)
                
                # Extract first video ID from search results
                import re
                video_id_match = re.search(r'"videoId":"([^"]+)"', response.text)
                
                if video_id_match:
                    video_id = video_id_match.group(1)
                    # Direct play URL
                    youtube_url = f"https://www.youtube.com/watch?v={video_id}&autoplay=1"
                    webbrowser.open(youtube_url)
                    return f"Playing '{query}' on YouTube"
                else:
                    # Fallback to search
                    webbrowser.open(youtube_search_url)
                    return f"Searching '{query}' on YouTube - click the first result to play"
            except:
                # If API fails, use search URL
                webbrowser.open(youtube_search_url)
                return f"Opening '{query}' on YouTube"
        
        elif platform == "spotify":
            # Spotify - Direct search
            spotify_url = f"https://open.spotify.com/search/{query_encoded}"
            webbrowser.open(spotify_url)
            return f"Searching '{query}' on Spotify - click to play"
        
        elif platform == "music" or platform == "apple":
            # Apple Music
            music_url = f"https://music.apple.com/search?term={query_encoded}"
            webbrowser.open(music_url)
            return f"Searching '{query}' on Apple Music"
        
        elif platform == "soundcloud":
            # SoundCloud
            soundcloud_url = f"https://soundcloud.com/search?q={query_encoded}"
            webbrowser.open(soundcloud_url)
            return f"Searching '{query}' on SoundCloud"
        
        elif platform == "gaana":
            # Gaana (Indian music platform)
            gaana_url = f"https://gaana.com/search/{query_encoded}"
            webbrowser.open(gaana_url)
            return f"Searching '{query}' on Gaana"
        
        elif platform == "jiosaavn" or platform == "saavn":
            # JioSaavn (Indian music platform)
            saavn_url = f"https://www.jiosaavn.com/search/{query_encoded}"
            webbrowser.open(saavn_url)
            return f"Searching '{query}' on JioSaavn"
        
        else:
            # Default to YouTube with auto-play attempt
            youtube_search_url = f"https://www.youtube.com/results?search_query={query_encoded}"
            webbrowser.open(youtube_search_url)
            return f"Playing '{query}' on YouTube"
            
    except Exception as e:
        return f"Sorry, I couldn't play '{query}'"

def play_video(query: str) -> str:
    """Play video on YouTube"""
    return play_music(query, "youtube")

# ============================================================================
# SYSTEM CONTROL SKILL
# ============================================================================

import subprocess
import platform

def open_application(app_name: str) -> str:
    """Open an application"""
    try:
        system = platform.system()
        app_name = app_name.lower()
        
        if system == "Darwin":  # macOS
            apps = {
                "chrome": "Google Chrome",
                "safari": "Safari",
                "notes": "Notes",
                "calendar": "Calendar",
                "music": "Music",
                "mail": "Mail"
            }
            if app_name in apps:
                subprocess.Popen(["open", "-a", apps[app_name]])
                return f"Opening {apps[app_name]}"
        
        return f"Opening {app_name}..."
    except Exception as e:
        return f"Sorry, I couldn't open {app_name}"

# ============================================================================
# SKILL DETECTOR
# ============================================================================

def detect_and_execute_skill(user_input: str) -> Optional[str]:
    """Detect which skill to use and execute it"""
    text = user_input.lower()
    
    # Music/Video Playback - HIGH PRIORITY
    if any(word in text for word in ["play", "listen", "song", "music", "video"]):
        # Detect platform
        platform = "youtube"  # Default
        if "spotify" in text:
            platform = "spotify"
        elif "apple music" in text or "itunes" in text:
            platform = "music"
        elif "soundcloud" in text:
            platform = "soundcloud"
        elif "gaana" in text:
            platform = "gaana"
        elif "jiosaavn" in text or "saavn" in text:
            platform = "jiosaavn"
        
        # Extract song/video name
        query = text
        # Remove platform names
        query = re.sub(r'(on |from )?(youtube|spotify|apple music|soundcloud|gaana|jiosaavn|saavn)', '', query)
        # Remove command words
        query = re.sub(r'^(play|listen to|listen|show me|find|search for|search)\s+', '', query)
        query = query.strip()
        
        if query:
            return play_music(query, platform)
    
    # Weather
    if any(word in text for word in ["weather", "temperature", "forecast"]):
        city_match = re.search(r'in ([a-z\s]+)', text)
        city = city_match.group(1).strip() if city_match else "Delhi"
        
        if "forecast" in text:
            return get_weather_forecast(city)
        return get_weather(city)
    
    # Calculations
    if any(word in text for word in ["calculate", "what is", "plus", "minus", "times", "divided", "multiply"]):
        if any(op in text for op in ['+', '-', '*', '/', 'plus', 'minus', 'times', 'divided']):
            return calculate(text)
    
    # Unit conversion
    if "convert" in text:
        match = re.search(r'(\d+\.?\d*)\s*(\w+)\s*to\s*(\w+)', text)
        if match:
            value, from_unit, to_unit = match.groups()
            return convert_units(float(value), from_unit, to_unit)
    
    # Timer
    if "timer" in text or "set a timer" in text:
        match = re.search(r'(\d+)\s*minute', text)
        if match:
            minutes = int(match.group(1))
            message_match = re.search(r'for (.+)', text)
            message = message_match.group(1) if message_match else "Timer"
            return set_timer(minutes, message)
    
    # Reminder
    if "remind" in text:
        time_match = re.search(r'at (\d{1,2}):(\d{2})', text)
        if time_match:
            time_str = f"{time_match.group(1)}:{time_match.group(2)}"
            message_match = re.search(r'to (.+?) at', text)
            message = message_match.group(1) if message_match else "Reminder"
            return set_reminder(time_str, message)
    
    # News
    if "news" in text:
        category = "general"
        if "technology" in text or "tech" in text:
            category = "technology"
        elif "sports" in text:
            category = "sports"
        elif "business" in text:
            category = "business"
        return get_news(category)
    
    # Wikipedia/Information
    if any(phrase in text for phrase in ["who is", "what is", "tell me about", "information about"]):
        query = re.sub(r'(who is|what is|tell me about|information about)\s*', '', text)
        return search_wikipedia(query)
    
    # Jokes
    if "joke" in text or "make me laugh" in text:
        return tell_joke()
    
    # Fun facts
    if "fun fact" in text or "interesting fact" in text:
        return get_fun_fact()
    
    # Open application
    if "open" in text:
        app_match = re.search(r'open\s+(\w+)', text)
        if app_match:
            return open_application(app_match.group(1))
    
    return None  # No skill matched
