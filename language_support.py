"""
Language detection and switching node for multi-language support
"""

from typing import Dict

# Language switching keywords in different languages
LANGUAGE_KEYWORDS = {
    "english": ["english", "change to english", "switch to english", "speak english"],
    "hindi": ["hindi", "हिंदी", "change to hindi", "switch to hindi", "hindi mein bolo"],
    "tamil": ["tamil", "தமிழ்", "change to tamil", "switch to tamil"],
    "telugu": ["telugu", "తెలుగు", "change to telugu", "switch to telugu"],
    "bengali": ["bengali", "bangla", "বাংলা", "change to bengali"],
    "marathi": ["marathi", "मराठी", "change to marathi"],
    "gujarati": ["gujarati", "ગુજરાતી", "change to gujarati"],
    "kannada": ["kannada", "ಕನ್ನಡ", "change to kannada"],
    "malayalam": ["malayalam", "മലയാളം", "change to malayalam"],
    "punjabi": ["punjabi", "ਪੰਜਾਬੀ", "change to punjabi"],
    "odia": ["odia", "oriya", "ଓଡ଼ିଆ", "change to odia"],
    "assamese": ["assamese", "অসমীয়া", "change to assamese"],
    "urdu": ["urdu", "اردو", "change to urdu"]
}

# Confirmation messages in different languages
LANGUAGE_CONFIRMATIONS = {
    "english": "Language changed to English. I will now speak in English.",
    "hindi": "भाषा हिंदी में बदल दी गई है। मैं अब हिंदी में बोलूंगा।",
    "tamil": "மொழி தமிழாக மாற்றப்பட்டது. நான் இப்போது தமிழில் பேசுவேன்.",
    "telugu": "భాష తెలుగుకు మార్చబడింది. నేను ఇప్పుడు తెలుగులో మాట్లాడతాను.",
    "bengali": "ভাষা বাংলায় পরিবর্তন করা হয়েছে। আমি এখন বাংলায় কথা বলব।",
    "marathi": "भाषा मराठीमध्ये बदलली आहे. मी आता मराठीत बोलेन.",
    "gujarati": "ભાષા ગુજરાતીમાં બદલાઈ ગઈ છે. હું હવે ગુજરાતીમાં બોલીશ.",
    "kannada": "ಭಾಷೆಯನ್ನು ಕನ್ನಡಕ್ಕೆ ಬದಲಾಯಿಸಲಾಗಿದೆ. ನಾನು ಈಗ ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡುತ್ತೇನೆ.",
    "malayalam": "ഭാഷ മലയാളത്തിലേക്ക് മാറ്റി. ഞാൻ ഇപ്പോൾ മലയാളത്തിൽ സംസാരിക്കും.",
    "punjabi": "ਭਾਸ਼ਾ ਪੰਜਾਬੀ ਵਿੱਚ ਬਦਲੀ ਗਈ ਹੈ। ਮੈਂ ਹੁਣ ਪੰਜਾਬੀ ਵਿੱਚ ਬੋਲਾਂਗਾ।",
    "odia": "ଭାଷା ଓଡ଼ିଆକୁ ପରିବର୍ତ୍ତନ କରାଯାଇଛି। ମୁଁ ବର୍ତ୍ତମାନ ଓଡ଼ିଆରେ କହିବି।",
    "assamese": "ভাষা অসমীয়ালৈ সলনি কৰা হৈছে। মই এতিয়া অসমীয়াত কথা ক'ম।",
    "urdu": "زبان اردو میں تبدیل کر دی گئی ہے۔ میں اب اردو میں بات کروں گا۔"
}

def detect_language_change(state: Dict) -> Dict:
    """Detect if user wants to change language"""
    user_input = state["user_input"].lower()
    
    # Check for language change keywords
    for language, keywords in LANGUAGE_KEYWORDS.items():
        if any(keyword in user_input for keyword in keywords):
            # Language change detected
            state["language"] = language
            state["context"]["language"] = language
            state["response_to_speak"] = LANGUAGE_CONFIRMATIONS[language]
            state["skip_processing"] = True
            print(f"🌐 Language changed to: {language}")
            return state
    
    # No language change detected
    return state
