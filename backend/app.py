from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import speech_recognition as sr
import pyttsx3
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
import operator
import json
import base64
import io
import wave
from dotenv import load_dotenv
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import tempfile
import webbrowser
import urllib.parse
import subprocess
import platform

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

executor = ThreadPoolExecutor(max_workers=3)

class ConversationState(TypedDict):
    messages: Annotated[list, operator.add]
    user_input: str
    should_continue: bool
    skip_processing: bool

def execute_command(text):
    text_lower = text.lower()
    
    if "open youtube" in text_lower:
        return {"action": "open_url", "url": "https://www.youtube.com", "message": "Opening YouTube"}
    
    if "open netflix" in text_lower:
        return {"action": "open_url", "url": "https://www.netflix.com", "message": "Opening Netflix"}
    
    if "open amazon prime" in text_lower or "open prime video" in text_lower:
        return {"action": "open_url", "url": "https://www.primevideo.com", "message": "Opening Amazon Prime Video"}
    
    if "open google" in text_lower:
        return {"action": "open_url", "url": "https://www.google.com", "message": "Opening Google"}
    
    if "open gmail" in text_lower:
        return {"action": "open_url", "url": "https://mail.google.com", "message": "Opening Gmail"}
    
    if "open spotify" in text_lower:
        return {"action": "open_url", "url": "https://open.spotify.com", "message": "Opening Spotify"}
    
    if "play song" in text_lower or "play music" in text_lower or "play " in text_lower:
        song_name = text_lower.replace("play song", "").replace("play music", "").replace("play", "").strip()
        if song_name:
            query = urllib.parse.quote(song_name)
            youtube_url = f"https://www.youtube.com/results?search_query={query}&sp=EgIQAQ%253D%253D"
            return {"action": "play_song", "url": youtube_url, "message": f"Playing {song_name}", "song_name": song_name}
    
    return None

def process_audio_data(audio_data: bytes):
    recognizer = sr.Recognizer()
    try:
        audio_file = sr.AudioFile(io.BytesIO(audio_data))
        with audio_file as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio)
        return {"success": True, "text": text}
    except sr.UnknownValueError:
        return {"success": False, "error": "Could not understand audio"}
    except sr.RequestError as e:
        return {"success": False, "error": f"Speech recognition error: {e}"}
    except Exception as e:
        return {"success": False, "error": f"Error: {e}"}

def process_with_llm_sync(messages):
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        response = llm.invoke(messages)
        return {"success": True, "content": response.content}
    except Exception as e:
        return {"success": False, "error": str(e)}

def text_to_speech_sync(text: str):
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 0.9)
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        engine.save_to_file(text, temp_filename)
        engine.runAndWait()
        
        with open(temp_filename, "rb") as f:
            audio_data = f.read()
        
        os.unlink(temp_filename)
        
        return base64.b64encode(audio_data).decode('utf-8')
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

@app.post("/api/process-audio")
async def process_audio(audio_data: dict):
    try:
        audio_bytes = base64.b64decode(audio_data["audio"])
        
        loop = asyncio.get_event_loop()
        transcription_result = await loop.run_in_executor(executor, process_audio_data, audio_bytes)
        
        if not transcription_result["success"]:
            raise HTTPException(status_code=400, detail=transcription_result["error"])
        
        text = transcription_result["text"]
        
        command_result = execute_command(text)
        if command_result:
            audio_base64 = await loop.run_in_executor(executor, text_to_speech_sync, command_result["message"])
            return {
                "transcription": text,
                "response": command_result["message"],
                "audio": audio_base64,
                "action": command_result.get("action"),
                "url": command_result.get("url"),
                "song_name": command_result.get("song_name")
            }
        
        messages = [HumanMessage(content=text)]
        llm_result = await loop.run_in_executor(executor, process_with_llm_sync, messages)
        
        if not llm_result["success"]:
            raise HTTPException(status_code=500, detail=llm_result["error"])
        
        response_text = llm_result["content"]
        
        audio_base64 = await loop.run_in_executor(executor, text_to_speech_sync, response_text)
        
        return {
            "transcription": text,
            "response": response_text,
            "audio": audio_base64
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/text-to-speech")
async def text_to_speech(data: dict):
    try:
        text = data.get("text", "")
        loop = asyncio.get_event_loop()
        audio_base64 = await loop.run_in_executor(executor, text_to_speech_sync, text)
        
        if audio_base64:
            return {"audio": audio_base64}
        else:
            raise HTTPException(status_code=500, detail="Failed to generate speech")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)