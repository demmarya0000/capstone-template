"""
Booking workflow nodes for LangGraph integration
These nodes handle the travel booking flow
"""

from typing import Dict
from datetime import datetime
import dateparser
from travel_booking import get_booking_service
from travel_rag import get_travel_rag

# Services will be initialized lazily

def detect_booking_intent_node(state: Dict) -> Dict:
    """Detect if user wants to book travel"""
    user_input = state["user_input"].lower()
    
    # Check for booking keywords
    booking_keywords = {
        "flight": ["flight", "fly", "plane", "air"],
        "train": ["train", "railway", "rail"],
        "bus": ["bus"]
    }
    
    for mode, keywords in booking_keywords.items():
        if any(keyword in user_input for keyword in keywords):
            if any(word in user_input for word in ["book", "find", "search", "show", "get"]):
                state["booking_intent"] = mode
                state["booking_step"] = "extracting"
                state["booking_data"] = {}
                return state
    
    # No booking intent detected
    state["booking_intent"] = None
    state["booking_step"] = "initial"
    return state

def extract_entities_node(state: Dict) -> Dict:
    """Extract booking entities from user input"""
    if state.get("booking_intent"):
        booking_service = get_booking_service()
        # Use LLM to extract entities
        entities = booking_service.extract_booking_entities(state["user_input"])
        state["booking_data"] = entities
        
        # Check if we have all required info
        required = ["origin", "destination", "date"]
        missing = [field for field in required if not entities.get(field)]
        
        if missing:
            # Ask for missing information
            state["booking_step"] = "collecting_info"
            state["response_to_speak"] = f"I need more information. Please provide: {', '.join(missing)}"
            state["skip_processing"] = True
        else:
            # We have all info, proceed to search
            state["booking_step"] = "searching"
    
    return state

def search_travel_node(state: Dict) -> Dict:
    """Search for travel options"""
    if state["booking_step"] == "searching":
        booking_service = get_booking_service()
        booking_data = state["booking_data"]
        travel_mode = state["booking_intent"]
        
        # Parse date
        date = booking_data.get("parsed_date") or datetime.now()
        origin = booking_data.get("origin", "")
        destination = booking_data.get("destination", "")
        passengers = booking_data.get("passengers", 1)
        
        # Search based on travel mode
        if travel_mode == "flight":
            results = booking_service.search_flights(origin, destination, date, passengers)
        elif travel_mode == "train":
            results = booking_service.search_trains(origin, destination, date, passengers)
        elif travel_mode == "bus":
            results = booking_service.search_buses(origin, destination, date, passengers)
        else:
            results = []
        
        state["search_results"] = results
        state["booking_step"] = "presenting"
    
    return state

def present_options_node(state: Dict) -> Dict:
    """Present travel options to user"""
    if state["booking_step"] == "presenting":
        booking_service = get_booking_service()
        results = state.get("search_results", [])
        travel_mode = state["booking_intent"]
        
        if results:
            # Format options for voice
            formatted = booking_service.format_options(results, travel_mode, top_n=3)
            state["response_to_speak"] = formatted + "\n\nWhich option would you like to book? Say 'first', 'second', or 'third'."
            state["booking_step"] = "awaiting_selection"
        else:
            state["response_to_speak"] = f"Sorry, no {travel_mode}s found for this route."
            state["booking_step"] = "initial"
            state["booking_intent"] = None
        
        state["skip_processing"] = True
    
    return state

def handle_selection_node(state: Dict) -> Dict:
    """Handle user's selection of travel option"""
    if state["booking_step"] == "awaiting_selection":
        user_input = state["user_input"].lower()
        
        # Parse selection
        selection_map = {"first": 0, "1": 0, "second": 1, "2": 1, "third": 2, "3": 2}
        selected_index = None
        
        for key, index in selection_map.items():
            if key in user_input:
                selected_index = index
                break
        
        if selected_index is not None and selected_index < len(state.get("search_results", [])):
            state["selected_option"] = state["search_results"][selected_index]
            state["booking_step"] = "confirming"
        else:
            state["response_to_speak"] = "I didn't understand your selection. Please say 'first', 'second', or 'third'."
            state["skip_processing"] = True
    
    return state

def confirm_booking_node(state: Dict) -> Dict:
    """Confirm and complete booking"""
    if state["booking_step"] == "confirming":
        booking_service = get_booking_service()
        selected = state.get("selected_option")
        
        if selected:
            # Create booking
            booking_details = {
                **selected,
                "passenger_count": state["booking_data"].get("passengers", 1),
                "travel_date": state["booking_data"].get("date", "")
            }
            
            booking = booking_service.book_travel(booking_details)
            
            # Format confirmation message
            travel_mode = state["booking_intent"]
            if travel_mode == "flight":
                confirmation = f"✅ Booking confirmed! Your flight {selected['flight_number']} from {selected['origin']} to {selected['destination']} on {selected['departure']} is booked. Booking ID: {booking['booking_id']}. Total: ₹{selected['price']}"
            elif travel_mode == "train":
                confirmation = f"✅ Booking confirmed! Your train {selected['name']} from {selected['origin']} to {selected['destination']} on {selected['departure']} is booked. Booking ID: {booking['booking_id']}. Total: ₹{selected['price']}"
            else:  # bus
                confirmation = f"✅ Booking confirmed! Your bus from {selected['origin']} to {selected['destination']} on {selected['departure']} is booked. Booking ID: {booking['booking_id']}. Total: ₹{selected['price']}"
            
            state["response_to_speak"] = confirmation
            state["booking_step"] = "booked"
            state["booking_intent"] = None
            state["skip_processing"] = True
    
    return state
