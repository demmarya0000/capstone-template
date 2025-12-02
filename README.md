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

### Phase 1: Core Voice Assistant ✅
- [x] Implement basic voice recognition using Whisper API
- [x] Add text-to-speech with gTTS
- [x] Create conversation flow with LangGraph
- [x] Implement continuous listening mode
- [x] Add context memory and conversation history

### Phase 2: Multi-Language Support ✅
- [x] Add support for 12 Indian regional languages
- [x] Implement language switching via voice commands
- [x] Add multi-language speech recognition
- [x] Add multi-language text-to-speech
- [x] Create language-specific confirmations in native scripts
- [x] Integrate language detection into workflow

### Phase 3: Travel Booking Integration ✅
- [x] Design booking workflow with LangGraph
- [x] Implement entity extraction for travel queries
- [x] Add IATA code mapping for 40+ Indian cities
- [x] Create booking nodes for flights, trains, and buses
- [x] Integrate 6 flight booking sites with pre-filled parameters
- [x] Integrate 5 train booking sites with pre-filled parameters
- [x] Integrate 5 bus booking sites with pre-filled parameters
- [x] Add multi-turn conversation support for missing information
- [x] Implement booking context persistence across turns

### Phase 4: RAG System Implementation ✅
- [x] Set up FAISS vector store for travel information
- [x] Implement document chunking and embedding
- [x] Create semantic search functionality
- [x] Integrate RAG with booking workflow
- [x] Add travel information retrieval

### Phase 5: Advanced Features ✅
- [x] Remove wake word for seamless interaction
- [x] Add smart time-based greetings
- [x] Implement booking state management
- [x] Add support for multiple date formats
- [x] Create comprehensive IATA code database
- [x] Add browser automation for booking sites
- [x] Implement delay management for multiple site openings

### Phase 6: Optimization & Polish ✅
- [x] Fix booking URL formats for all sites
- [x] Add proper error handling and recovery
- [x] Implement speech interruption capability
- [x] Optimize Whisper API usage
- [x] Add console feedback and progress indicators
- [x] Create comprehensive documentation

### Phase 7: Future Enhancements 🔄
- [ ] Add hotel booking integration
- [ ] Implement cab/taxi booking (Uber, Ola)
- [ ] Add weather information integration
- [ ] Create user preference profiles
- [ ] Add voice authentication
- [ ] Implement booking history tracking
- [ ] Add calendar integration for travel dates
- [ ] Create mobile app version
- [ ] Add offline mode with cached responses
- [ ] Implement voice biometrics for security
- [ ] Add multi-user support
- [ ] Create web dashboard for booking management
- [ ] Add payment gateway integration
- [ ] Implement loyalty program tracking
- [ ] Add travel itinerary generation
- [ ] Create expense tracking for trips

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

## 🔧 Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key
```

### Language Settings
Default language is English. Switch languages using voice commands:
- "Change to Hindi"
- "Switch to Tamil"
- "हिंदी में बोलो"

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

**Aarnav Arya**
- GitHub: [@demmarya0000](https://github.com/demmarya0000)

## 🙏 Acknowledgments

- OpenAI for Whisper API and GPT-4
- Google for Text-to-Speech
- LangChain team for LangGraph
- All travel booking sites for their services

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

**Made with ❤️ in India** 🇮🇳
