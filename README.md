# 🎙️ Advanced Multi-Language Voice Assistant

An intelligent voice assistant with travel booking capabilities, supporting 12+ Indian regional languages with real-time speech recognition and natural language processing.

## 🌟 Features

### Core Capabilities
- **Continuous Voice Recognition** - Always listening, no wake word needed
- **Multi-Language Support** - 12+ Indian regional languages with native script support
- **Smart Travel Booking** - Automated flight, train, and bus booking with 16+ travel sites
- **Context-Aware Conversations** - Remembers conversation history and booking preferences
- **Real-Time Price Comparison** - Opens multiple booking sites simultaneously for best deals

### Supported Languages
🌐 English | हिंदी | தமிழ் | తెలుగు | বাংলা | मराठी | ગુજરાતી | ಕನ್ನಡ | മലയാളം | ਪੰਜਾਬੀ | ଓଡ଼ିଆ | অসমীয়া | اردو

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API Key
- Microphone access

### Installation

```bash
# Clone the repository
git clone https://github.com/demmarya0000/capstone-template.git
cd voice-assistant

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "OPENAI_API_KEY=your_api_key_here" > .env

# Run the assistant
python3 voice_assistant.py
```

## 📋 To-Do List

### Phase 1: Core Voice Assistant ✅(DONE)
- [x] Implement basic voice recognition using Whisper API
- [x] Add text-to-speech with gTTS
- [x] Create conversation flow with LangGraph
- [x] Implement continuous listening mode
- [x] Add context memory and conversation history

### Phase 2: Multi-Language Support ✅(DONE)
- [x] Add support for 12 Indian regional languages
- [x] Implement language switching via voice commands
- [x] Add multi-language speech recognition
- [x] Add multi-language text-to-speech
- [x] Create language-specific confirmations in native scripts
- [x] Integrate language detection into workflow

### Phase 3: Travel Booking Integration ✅(DONE)
- [x] Design booking workflow with LangGraph
- [x] Implement entity extraction for travel queries
- [x] Add International Air Transport Association (IATA) code mapping for 40+ Indian cities
- [x] Create booking nodes for flights, trains, and buses
- [x] Integrate 6 flight booking sites with pre-filled parameters
- [x] Integrate 5 train booking sites with pre-filled parameters
- [x] Integrate 5 bus booking sites with pre-filled parameters
- [x] Add multi-turn conversation support for missing information
- [x] Implement booking context persistence across turns

### Phase 4: RAG System Implementation ✅(DONE)
- [x] Set up FAISS(Facebook AI similarity Search) vector store for travel information(So that it can get to me the nearest neighbours of the query vector for a very large dataset.)
- [x] Integrate RAG with booking workflow
- [x] Add travel information retrieval

### Phase 5: Advanced Features ✅(DONE)
- [x] Remove wake word for seamless interaction
- [x] Add smart time-based greetings
- [x] Implement booking state management
- [x] Add support for multiple date formats
- [x] Create comprehensive IATA code database
- [x] Add browser automation for booking sites
- [x] Implement delay management for multiple site openings

### Phase 6: Optimization & Polish ✅(DONE)
- [x] Fix booking URL formats for all sites
- [x] Add proper error handling and recovery
- [x] Implement speech interruption capability
- [x] Optimize Whisper API usage

### CONCLUSION:- 
- _I am pretty happy with how it came out, would be more working on the frontend for sure and I loved bascically this course because it was
something that I have never listned before and made a project out of it and which came out to be working is pretty big achievement for me and if I had been given more time I would have worked on implementing these things (PHASE 7) to my voice-assistant._
  
### Phase 7: Future Enhancements 🔄(TO BE DONE IN FUTURE)
- [ ] Add hotel booking integration
- [ ] Create user preference profiles
- [ ] Add voice authentication
- [ ] Implement booking history tracking
- [ ] Add calendar integration for travel dates
- [ ] Create mobile app version
- [ ] Add multi-user support
- [ ] Create web dashboard for booking management
- [ ] Add payment gateway integration
- [ ] Implement loyalty program tracking(bascially that everyday user visits)
- [ ] Add travel itinerary generation
- [ ] Create expense tracking for trips

### VIDEO FOR THE VOICE ASSISTANT:-
- https://youtu.be/E1FgAc9QPZA?si=Rft9CklGDN0LHuni -> This is the Video YouTube link (Unlisted)
- (https://drive.google.com/file/d/1yOAsJOVKlLCRyBPq5x1kIMqW8Z6he7mZ/view?usp=sharing) -> This is the video Google Drive Link

## 🏗️ Architecture

### Technology Stack
- **Speech Recognition**: OpenAI Whisper API
- **Text-to-Speech**: Google Text-to-Speech (gTTS)
- **LLM**: OpenAI GPT-4
- **Workflow**: LangGraph for state management
- **Vector Store**: FAISS for RAG
- **Embeddings**: OpenAI text-embedding-3-small

### Project Structure
```
voice-assistant/
├── voice_assistant.py      # Main application
├── booking_nodes.py         # Travel booking workflow nodes
├── language_support.py      # Multi-language detection
├── travel_booking.py        # Booking service implementation
├── travel_rag.py           # RAG system for travel info
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables
```

## 🎯 Usage Examples
- FROM THESE COMMANDS YOU CAN START THE CONVERSATION WITH THE VOICE ASSISTANT:-(SNIPPETS OF THE CONVERSATIONS)
### Basic Conversation
```
You: "Hello"
Assistant: "Good morning! How can I help you?"
```

### Language Switching
```
You: "Change to Hindi"
Assistant (हिंदी): "भाषा हिंदी में बदल दी गई है। मैं अब हिंदी में बोलूंगा।"
```

### Flight Booking
```
You: "Book a flight from Delhi to Mumbai on December 25th"
Assistant: "Opening 6 flight booking sites for Delhi to Mumbai on 25/12/2024..."
*Opens Google Flights, MakeMyTrip, Yatra, Ixigo, EaseMyTrip, Cleartrip*
```

### Train Booking
```
You: "Find trains from Bangalore to Chennai"
Assistant: "I need more information. Please provide: date"
You: "Tomorrow"
Assistant: "Opening 5 train booking sites..."
*Opens Google Search, Ixigo Trains, RailYatri, MakeMyTrip, ConfirmTkt*
```

## 📊 Supported Booking Sites

### Flights (6 sites)
- Google Flights
- MakeMyTrip
- Yatra
- Ixigo
- EaseMyTrip
- Cleartrip

### Trains (5 sites)
- Google Search
- Ixigo Trains
- RailYatri
- MakeMyTrip Railways
- ConfirmTkt

### Buses (5 sites)
- Google Search
- RedBus
- Ixigo Bus
- AbhiBus
- MakeMyTrip Bus

## 🌍 Supported Cities

40+ major Indian cities including:
Delhi, Mumbai, Bangalore, Chennai, Kolkata, Hyderabad, Pune, Ahmedabad, Jaipur, Chandigarh, Ranchi, Goa, Kochi, Thiruvananthapuram, Bhubaneswar, Indore, Coimbatore, Nagpur, Vadodara, Patna, Raipur, Bhopal, Amritsar, Srinagar, Guwahati, Visakhapatnam, Vijayawada, Mangalore, Calicut, Madurai, Varanasi, Agra, Udaipur, Jodhpur, and more!

### Language Settings
Default language is English. Switch languages using voice commands:
- "Change to Hindi"
- "Switch to Tamil"
- "हिंदी में बोलो"

**PICTORIAL REPRESENTATION:-**
- WHAT I THOUGHT I WOULD HAVE MADE IF THE JARVIS FEATURE HAVE BEEN IMPLEMENTED
![PHOTO-2025-11-27-18-05-12](https://github.com/user-attachments/assets/438b241c-9602-438c-9b38-5c3b8be5e336)



## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author(ABOUT ME)

**Aarnav Arya:- JUST A GUY TRYING TO BUID SOMTHING BUY SO THAT COULD GET FAMOUS(THE RIGHT WAY) AND EARN A LOT OF MONEY "LOL"**
- GitHub: [@demmarya0000](https://github.com/demmarya0000)

**Made with ❤️ in India(BHARAT)** 🇮🇳

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
