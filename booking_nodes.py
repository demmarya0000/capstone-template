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
    """Open maximum booking websites with all search parameters pre-filled"""
    if state["booking_step"] == "searching":
        import webbrowser
        import urllib.parse
        from datetime import datetime
        import time
        
        booking_data = state["booking_data"]
        travel_mode = state["booking_intent"]
        
        # Parse date
        date = booking_data.get("parsed_date") or datetime.now()
        origin = booking_data.get("origin", "").strip()
        destination = booking_data.get("destination", "").strip()
        passengers = booking_data.get("passengers", 1)
        
        # Comprehensive IATA code mapping for Indian cities
        iata_codes = {
            "delhi": "DEL", "new delhi": "DEL", "mumbai": "BOM", "bangalore": "BLR", "bengaluru": "BLR",
            "chennai": "MAA", "kolkata": "CCU", "hyderabad": "HYD", "pune": "PNQ",
            "ahmedabad": "AMD", "jaipur": "JAI", "lucknow": "LKO", "goa": "GOI", "panaji": "GOI",
            "kochi": "COK", "cochin": "COK", "thiruvananthapuram": "TRV", "bhubaneswar": "BBI",
            "indore": "IDR", "chandigarh": "IXC", "coimbatore": "CJB", "nagpur": "NAG",
            "vadodara": "BDQ", "patna": "PAT", "ranchi": "IXR", "raipur": "RPR",
            "bhopal": "BHO", "amritsar": "ATQ", "srinagar": "SXR", "guwahati": "GAU",
            "visakhapatnam": "VTZ", "vizag": "VTZ", "vijayawada": "VGA", "mangalore": "IXE",
            "calicut": "CCJ", "kozhikode": "CCJ", "trivandrum": "TRV", "madurai": "IXM",
            "varanasi": "VNS", "agra": "AGR", "udaipur": "UDR", "jodhpur": "JDH"
        }
        
        # Get IATA codes
        origin_code = iata_codes.get(origin.lower(), origin.upper()[:3])
        dest_code = iata_codes.get(destination.lower(), destination.upper()[:3])
        
        # Format dates in multiple formats for different sites
        date_str = date.strftime("%d/%m/%Y")
        date_yyyy_mm_dd = date.strftime("%Y-%m-%d")
        date_ddmmyyyy = date.strftime("%d%m%Y")
        date_dd_mm_yyyy = date.strftime("%d-%m-%Y")
        
        # Open booking websites based on travel mode
        if travel_mode == "flight":
            print(f"\n🛫 Opening 6 flight booking sites with pre-filled details...")
            
            # 1. Google Flights - Most comprehensive
            google_flights = f"https://www.google.com/travel/flights?q=Flights+from+{urllib.parse.quote(origin)}+to+{urllib.parse.quote(destination)}+on+{date_yyyy_mm_dd}+for+{passengers}+passengers"
            
            # 2. MakeMyTrip - India's largest
            makemytrip = f"https://www.makemytrip.com/flight/search?itinerary={origin_code}-{dest_code}-{date_ddmmyyyy}&tripType=O&paxType=A-{passengers}_C-0_I-0&intl=false&cabinClass=E&rKey=DCALC"
            
            # 3. Yatra - Reliable Indian site
            yatra = f"https://www.yatra.com/online-flight-booking?origin={origin_code}&destination={dest_code}&departure_date={date_yyyy_mm_dd}&adult={passengers}&child=0&infant=0&class=Economy&search_source=search_box"
            
            # 4. Ixigo - Price comparison
            ixigo = f"https://www.ixigo.com/search/result/flight?from={origin_code}&to={dest_code}&date={date_yyyy_mm_dd}&adults={passengers}&children=0&infants=0&class=e"
            
            # 5. EaseMyTrip - Budget flights
            easemytrip = f"https://www.easemytrip.com/flights/search/{origin_code}/{dest_code}/{date_ddmmyyyy}/1/{passengers}/0/0/E"
            
            # 6. Cleartrip - Clean interface
            cleartrip = f"https://www.cleartrip.com/flights/results?from={origin_code}&to={dest_code}&depart_date={date_dd_mm_yyyy}&adults={passengers}&childs=0&infants=0&class=Economy&airline=&carrier=&sd=1734912000000"
            
            # Open all sites in separate thread to avoid blocking
            def open_sites_async():
                for url in [google_flights, makemytrip, yatra, ixigo, easemytrip, cleartrip]:
                    webbrowser.open(url)
                    time.sleep(0.2)
            
            import threading
            thread = threading.Thread(target=open_sites_async, daemon=True)
            thread.start()
            
            state["response_to_speak"] = f"Opening 6 flight booking sites for {origin} to {destination} on {date_str} for {passengers} passenger(s). All details are pre-filled on Google Flights, MakeMyTrip, Yatra, Ixigo, EaseMyTrip, and Cleartrip. Compare prices and book the best deal!"
            
        elif travel_mode == "train":
            print(f"\n🚂 Opening 5 train booking sites with pre-filled details...")
            
            # 1. Google Search - Shows all options
            google_trains = f"https://www.google.com/search?q=trains+from+{urllib.parse.quote(origin)}+to+{urllib.parse.quote(destination)}+on+{date_yyyy_mm_dd}+IRCTC"
            
            # 2. Ixigo Trains - Comprehensive
            ixigo_trains = f"https://www.ixigo.com/search/result/trains?from={urllib.parse.quote(origin)}&to={urllib.parse.quote(destination)}&date={date_yyyy_mm_dd}"
            
            # 3. RailYatri - Popular platform
            railyatri = f"https://www.railyatri.in/train-ticket/trains-from-{origin.lower().replace(' ', '-')}-to-{destination.lower().replace(' ', '-')}"
            
            # 4. MakeMyTrip Trains
            makemytrip_trains = f"https://www.makemytrip.com/railways/search?from={urllib.parse.quote(origin)}&to={urllib.parse.quote(destination)}&date={date_ddmmyyyy}"
            
            # 5. ConfirmTkt - Availability predictor
            confirmtkt = f"https://www.confirmtkt.com/train-tickets/{origin.lower().replace(' ', '-')}-to-{destination.lower().replace(' ', '-')}"
            
            # Open all sites in separate thread to avoid blocking
            def open_sites_async():
                for url in [google_trains, ixigo_trains, railyatri, makemytrip_trains, confirmtkt]:
                    webbrowser.open(url)
                    time.sleep(0.2)
            
            import threading
            thread = threading.Thread(target=open_sites_async, daemon=True)
            thread.start()
            
            state["response_to_speak"] = f"Opening 5 train booking sites for {origin} to {destination} on {date_str}. Check Google Search, Ixigo Trains, RailYatri, MakeMyTrip, and ConfirmTkt for all available trains with timings, prices, and seat availability."
            
        elif travel_mode == "bus":
            print(f"\n🚌 Opening bus booking sites...")
            
            # 1. Google Search - Comprehensive search with all details
            google_buses = f"https://www.google.com/search?q=bus+tickets+from+{urllib.parse.quote(origin)}+to+{urllib.parse.quote(destination)}+on+{date_str}+RedBus+Ixigo+AbhiBus+MakeMyTrip+timings+price"
            
            # 2. RedBus - Try with route in URL
            origin_slug = origin.lower().replace(" ", "-").replace(",", "")
            dest_slug = destination.lower().replace(" ", "-").replace(",", "")
            redbus = f"https://www.redbus.in/bus-tickets/{origin_slug}-to-{dest_slug}"
            
            # 3. Ixigo Bus - Homepage (manual search needed)
            ixigo_bus = f"https://www.ixigo.com/bus"
            
            # 4. AbhiBus - Try with route
            abhibus = f"https://www.abhibus.com/{origin_slug}-to-{dest_slug}-bus"
            
            # 5. MakeMyTrip Bus - Homepage
            makemytrip_bus = f"https://www.makemytrip.com/bus-tickets/"
            
            # Open all sites in separate thread to avoid blocking
            def open_sites_async():
                for url in [google_buses, redbus, ixigo_bus, abhibus, makemytrip_bus]:
                    webbrowser.open(url)
                    time.sleep(0.2)
            
            import threading
            thread = threading.Thread(target=open_sites_async, daemon=True)
            thread.start()
            
            state["response_to_speak"] = f"Opening bus booking sites for {origin} to {destination} on {date_str}. Google Search shows comprehensive results with timings and prices. RedBus and AbhiBus may have the route pre-filled. For Ixigo and MakeMyTrip, please search manually with your route and date."
        
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
