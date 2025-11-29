"""
Travel Booking Module - Mock booking service for flights, trains, and buses
Includes entity extraction and booking state management
"""

import re
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import dateparser
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

class TravelBookingService:
    """Mock travel booking service"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.bookings = []  # Store completed bookings
        self.booking_counter = 1000
    
    def extract_booking_entities(self, text: str) -> Dict:
        """
        Extract booking entities from user input using LLM
        
        Returns dict with: origin, destination, date, travel_mode, passengers
        """
        system_prompt = """You are an entity extraction assistant for travel bookings.
Extract the following information from user input:
- origin: departure city
- destination: arrival city  
- date: travel date (extract as natural language)
- travel_mode: flight, train, or bus
- passengers: number of passengers (default 1)

Return ONLY a JSON object with these fields. Use null for missing information.
Example: {"origin": "Delhi", "destination": "Mumbai", "date": "December 10th", "travel_mode": "flight", "passengers": 1}
"""
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=text)
            ])
            
            # Parse JSON from response
            import json
            entities = json.loads(response.content)
            
            # Parse date if present
            if entities.get('date'):
                parsed_date = dateparser.parse(entities['date'])
                if parsed_date:
                    entities['parsed_date'] = parsed_date
            
            return entities
        except Exception as e:
            print(f"❌ Entity extraction error: {e}")
            return {}
    
    def search_flights(self, origin: str, destination: str, date: datetime, passengers: int = 1) -> List[Dict]:
        """Search for available flights"""
        flights = []
        airlines = ["Air India", "IndiGo", "SpiceJet", "Vistara", "Go First"]
        
        # Generate 3-5 flight options
        num_flights = random.randint(3, 5)
        base_price = random.randint(3000, 8000)
        
        for i in range(num_flights):
            departure_hour = random.choice([6, 9, 12, 15, 18, 21])
            departure_time = date.replace(hour=departure_hour, minute=random.choice([0, 15, 30, 45]))
            duration_minutes = random.randint(90, 180)
            arrival_time = departure_time + timedelta(minutes=duration_minutes)
            
            price_variation = random.randint(-1000, 2000)
            price = base_price + price_variation + (i * 500)
            
            flight = {
                "id": f"FL{random.randint(1000, 9999)}",
                "airline": random.choice(airlines),
                "flight_number": f"{random.choice(['6E', 'AI', 'SG', 'UK'])}{random.randint(100, 999)}",
                "origin": origin,
                "destination": destination,
                "departure": departure_time.strftime("%I:%M %p"),
                "arrival": arrival_time.strftime("%I:%M %p"),
                "duration": f"{duration_minutes // 60}h {duration_minutes % 60}m",
                "price": price * passengers,
                "seats_available": random.randint(5, 50),
                "class": "Economy"
            }
            flights.append(flight)
        
        # Sort by price
        flights.sort(key=lambda x: x['price'])
        return flights
    
    def search_trains(self, origin: str, destination: str, date: datetime, passengers: int = 1) -> List[Dict]:
        """Search for available trains"""
        trains = []
        train_names = [
            "Rajdhani Express", "Shatabdi Express", "Duronto Express",
            "Garib Rath", "Jan Shatabdi", "Superfast Express"
        ]
        
        num_trains = random.randint(3, 5)
        base_price = random.randint(800, 2500)
        
        for i in range(num_trains):
            departure_hour = random.choice([7, 10, 14, 17, 20, 23])
            departure_time = date.replace(hour=departure_hour, minute=random.choice([0, 15, 30]))
            duration_hours = random.randint(6, 20)
            arrival_time = departure_time + timedelta(hours=duration_hours)
            
            price_variation = random.randint(-300, 800)
            price = base_price + price_variation + (i * 200)
            
            train = {
                "id": f"TR{random.randint(10000, 99999)}",
                "name": random.choice(train_names),
                "train_number": f"{random.randint(10000, 99999)}",
                "origin": origin,
                "destination": destination,
                "departure": departure_time.strftime("%I:%M %p"),
                "arrival": arrival_time.strftime("%I:%M %p, %d %b"),
                "duration": f"{duration_hours}h {random.randint(0, 59)}m",
                "price": price * passengers,
                "seats_available": random.randint(10, 100),
                "class": random.choice(["3AC", "2AC", "1AC", "Sleeper"])
            }
            trains.append(train)
        
        trains.sort(key=lambda x: x['price'])
        return trains
    
    def search_buses(self, origin: str, destination: str, date: datetime, passengers: int = 1) -> List[Dict]:
        """Search for available buses"""
        buses = []
        operators = ["RedBus", "VRL Travels", "SRS Travels", "Orange Travels", "Kallada Travels"]
        
        num_buses = random.randint(4, 6)
        base_price = random.randint(500, 1500)
        
        for i in range(num_buses):
            departure_hour = random.choice([6, 9, 12, 15, 18, 21, 23])
            departure_time = date.replace(hour=departure_hour, minute=random.choice([0, 30]))
            duration_hours = random.randint(6, 14)
            arrival_time = departure_time + timedelta(hours=duration_hours)
            
            price_variation = random.randint(-200, 400)
            price = base_price + price_variation + (i * 150)
            
            bus = {
                "id": f"BS{random.randint(1000, 9999)}",
                "operator": random.choice(operators),
                "bus_type": random.choice(["AC Sleeper", "AC Seater", "Non-AC Sleeper", "Volvo AC"]),
                "origin": origin,
                "destination": destination,
                "departure": departure_time.strftime("%I:%M %p"),
                "arrival": arrival_time.strftime("%I:%M %p, %d %b"),
                "duration": f"{duration_hours}h {random.randint(0, 59)}m",
                "price": price * passengers,
                "seats_available": random.randint(5, 40)
            }
            buses.append(bus)
        
        buses.sort(key=lambda x: x['price'])
        return buses
    
    def book_travel(self, booking_details: Dict) -> Dict:
        """Complete a booking"""
        self.booking_counter += 1
        booking_id = f"BK{self.booking_counter}"
        
        booking = {
            "booking_id": booking_id,
            "status": "CONFIRMED",
            "booked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            **booking_details
        }
        
        self.bookings.append(booking)
        return booking
    
    def format_options(self, options: List[Dict], travel_mode: str, top_n: int = 3) -> str:
        """Format search results for voice output"""
        if not options:
            return f"Sorry, no {travel_mode}s found for this route."
        
        options = options[:top_n]
        result = f"I found {len(options)} {travel_mode} options:\n\n"
        
        for i, option in enumerate(options, 1):
            if travel_mode == "flight":
                result += f"{i}. {option['airline']} {option['flight_number']}\n"
                result += f"   Departure: {option['departure']}, Arrival: {option['arrival']}\n"
                result += f"   Duration: {option['duration']}, Price: ₹{option['price']}\n\n"
            
            elif travel_mode == "train":
                result += f"{i}. {option['name']} ({option['train_number']})\n"
                result += f"   Departure: {option['departure']}, Arrival: {option['arrival']}\n"
                result += f"   Class: {option['class']}, Price: ₹{option['price']}\n\n"
            
            elif travel_mode == "bus":
                result += f"{i}. {option['operator']} - {option['bus_type']}\n"
                result += f"   Departure: {option['departure']}, Arrival: {option['arrival']}\n"
                result += f"   Price: ₹{option['price']}\n\n"
        
        return result.strip()

# Singleton instance
_booking_service_instance = None

def get_booking_service() -> TravelBookingService:
    """Get or create TravelBookingService singleton instance"""
    global _booking_service_instance
    if _booking_service_instance is None:
        _booking_service_instance = TravelBookingService()
    return _booking_service_instance
