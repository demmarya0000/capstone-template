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
    """Detect if user wants to book travel or is providing missing info"""
    user_input = state["user_input"].lower()
    
    # Check if we're already in a booking flow waiting for info
    if state.get("booking_step") == "collecting_info" and state.get("booking_intent"):
        # User is providing missing information, keep the booking intent
        return state
    
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
        
        # If we're collecting info, merge with existing data
        if state.get("booking_step") == "collecting_info":
            # Try to extract just the missing information from current input
            new_entities = booking_service.extract_booking_entities(state["user_input"])
            # Merge with existing booking data
            existing_data = state.get("booking_data", {})
            for key, value in new_entities.items():
                if value:  # Only update if new value exists
                    existing_data[key] = value
            state["booking_data"] = existing_data
        else:
            # First time extraction
            entities = booking_service.extract_booking_entities(state["user_input"])
            state["booking_data"] = entities
        
        # Check if we have all required info
        required = ["origin", "destination", "date"]
        missing = [field for field in required if not state["booking_data"].get(field)]
        
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
    """Open booking websites with search parameters"""
    if state["booking_step"] == "searching":
        import webbrowser
        import urllib.parse
        from datetime import datetime
        
        booking_data = state["booking_data"]
        travel_mode = state["booking_intent"]
        
        # Parse date
        date = booking_data.get("parsed_date") or datetime.now()
        origin = booking_data.get("origin", "").strip()
        destination = booking_data.get("destination", "").strip()
        passengers = booking_data.get("passengers", 1)
        
        # City to IATA code mapping (common Indian cities)
        iata_codes = {
            "delhi": "DEL", "mumbai": "BOM", "bangalore": "BLR", "bengaluru": "BLR",
            "chennai": "MAA", "kolkata": "CCU", "hyderabad": "HYD", "pune": "PNQ",
            "ahmedabad": "AMD", "jaipur": "JAI", "lucknow": "LKO", "goa": "GOI",
            "kochi": "COK", "thiruvananthapuram": "TRV", "bhubaneswar": "BBI",
            "indore": "IDR", "chandigarh": "IXC", "coimbatore": "CJB", "nagpur": "NAG",
            "vadodara": "BDQ", "patna": "PAT", "ranchi": "IXR", "raipur": "RPR",
            "bhopal": "BHO", "amritsar": "ATQ", "srinagar": "SXR", "guwahati": "GAU",
            "visakhapatnam": "VTZ", "vijayawada": "VGA", "mangalore": "IXE",
            "calicut": "CCJ", "trivandrum": "TRV", "madurai": "IXM"
        }
        
        # Get IATA codes
        origin_code = iata_codes.get(origin.lower(), origin.upper()[:3])
        dest_code = iata_codes.get(destination.lower(), destination.upper()[:3])
        
        # Format dates
        date_str = date.strftime("%d/%m/%Y")
        date_ddmmyyyy = date.strftime("%d%m%Y")
        date_yyyymmdd = date.strftime("%Y-%m-%d")
        date_mmddyyyy = date.strftime("%m/%d/%Y")
        
        # Open booking websites based on travel mode
        if travel_mode == "flight":
            # MakeMyTrip Flights - Updated format
            makemytrip_url = f"https://www.makemytrip.com/flight/search?itinerary={origin_code}-{dest_code}-{date_ddmmyyyy}&tripType=O&paxType=A-{passengers}_C-0_I-0&intl=false&cabinClass=E"
            
            # Goibibo Flights - Updated format  
            goibibo_url = f"https://www.goibibo.com/flights/{origin_code}-{dest_code}-air-tickets/?date={date_yyyymmdd}&adults={passengers}&children=0&infants=0"
            
            # EaseMyTrip - Alternative site with better URL support
            easemytrip_url = f"https://www.easemytrip.com/flights/search/{origin_code}/{dest_code}/{date_ddmmyyyy}/1/{passengers}/0/0/E"
            
            webbrowser.open(makemytrip_url)
            webbrowser.open(goibibo_url)
            webbrowser.open(easemytrip_url)
            
            state["response_to_speak"] = f"Opening flight booking websites for {origin} to {destination} on {date_str}. Check your browser - MakeMyTrip, Goibibo, and EaseMyTrip are loading with your search details."
            
        elif travel_mode == "train":
            # 12Go Asia - Works well for Indian trains
            go12_url = f"https://12go.asia/en/travel/{origin.lower()}/{destination.lower()}"
            
            # MakeMyTrip Trains - Updated format
            makemytrip_train_url = f"https://www.makemytrip.com/railways/search?from={origin}&to={destination}&date={date_ddmmyyyy}"
            
            # ConfirmTkt - Indian train booking
            confirmtkt_url = f"https://www.confirmtkt.com/train-tickets/{origin.lower()}-to-{destination.lower()}"
            
            webbrowser.open(go12_url)
            webbrowser.open(makemytrip_train_url)
            webbrowser.open(confirmtkt_url)
            
            state["response_to_speak"] = f"Opening train booking websites for {origin} to {destination} on {date_str}. Check your browser - 12Go, MakeMyTrip, and ConfirmTkt are loading."
            
        elif travel_mode == "bus":
            # RedBus - Updated format with proper encoding
            origin_slug = origin.lower().replace(" ", "-")
            dest_slug = destination.lower().replace(" ", "-")
            redbus_url = f"https://www.redbus.in/bus-tickets/{origin_slug}-to-{dest_slug}?fromCityName={urllib.parse.quote(origin)}&toCityName={urllib.parse.quote(destination)}&onward={date_yyyymmdd}"
            
            # AbhiBus - Updated format
            abhibus_url = f"https://www.abhibus.com/bus-ticket-booking/online/{origin_slug}-to-{dest_slug}"
            
            # MakeMyTrip Bus - Updated format
            makemytrip_bus_url = f"https://www.makemytrip.com/bus-tickets/search?from={urllib.parse.quote(origin)}&to={urllib.parse.quote(destination)}&travelDate={date_ddmmyyyy}"
            
            webbrowser.open(redbus_url)
            webbrowser.open(abhibus_url)
            webbrowser.open(makemytrip_bus_url)
            
            state["response_to_speak"] = f"Opening bus booking websites for {origin} to {destination} on {date_str}. Check your browser - RedBus, AbhiBus, and MakeMyTrip are loading with your search."
        
        state["booking_step"] = "completed"
        state["booking_intent"] = None
        state["skip_processing"] = True
    
    return state

def present_options_node(state: Dict) -> Dict:
    """This node is no longer needed as we open websites directly"""
    # Skip this node as websites are already opened
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
