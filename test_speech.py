#!/usr/bin/env python3
"""
Quick test script to diagnose speech recognition issues
"""
import speech_recognition as sr
import time

print("🔍 Testing Speech Recognition Setup...")
print("=" * 60)

# Test 1: Check microphone
print("\n1️⃣  Testing microphone access...")
try:
    with sr.Microphone() as source:
        print("   ✅ Microphone detected and accessible")
except Exception as e:
    print(f"   ❌ Microphone error: {e}")
    exit(1)

# Test 2: Record audio
print("\n2️⃣  Testing audio recording...")
print("   🎤 Please say something (you have 5 seconds)...")
recognizer = sr.Recognizer()

try:
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
        print("   ✅ Audio recorded successfully")
except sr.WaitTimeoutError:
    print("   ⚠️  No speech detected")
    exit(0)
except Exception as e:
    print(f"   ❌ Recording error: {e}")
    exit(1)

# Test 3: Test Google Speech API
print("\n3️⃣  Testing Google Speech Recognition API...")
print("   ⏳ Sending audio to Google API...")
start_time = time.time()

try:
    text = recognizer.recognize_google(audio, language="en-US")
    elapsed = time.time() - start_time
    print(f"   ✅ API responded in {elapsed:.2f} seconds")
    print(f"   📝 Recognized text: '{text}'")
except sr.UnknownValueError:
    elapsed = time.time() - start_time
    print(f"   ⚠️  API responded in {elapsed:.2f} seconds but couldn't understand audio")
except sr.RequestError as e:
    elapsed = time.time() - start_time
    print(f"   ❌ API error after {elapsed:.2f} seconds: {e}")
    print("   💡 This might indicate:")
    print("      - No internet connection")
    print("      - Google API is down")
    print("      - Rate limiting")
except Exception as e:
    elapsed = time.time() - start_time
    print(f"   ❌ Unexpected error after {elapsed:.2f} seconds: {e}")

print("\n" + "=" * 60)
print("✅ Diagnostic test complete!")
