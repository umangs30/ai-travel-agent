"""
Main orchestrator for the AI Travel Agent.
Demonstrates and tests the flight search, IATA lookup, and POI search tools.
"""

import os
import json
from dotenv import load_dotenv
from typing import Dict, List, Any

# Import tools
from tools.logistic_tools import FlightSearchTool, CityToIATATool, POISearchTool
from core.pydantics import ItineraryPlan, FlightOption

# Load environment variables
load_dotenv()


class TravelAgentOrchestrator:
    """Orchestrates the travel planning workflow using individual tools."""
    
    def __init__(self):
        """Initialize all available tools."""
        self.flight_search_tool = FlightSearchTool()
        self.iata_lookup_tool = CityToIATATool()
        self.poi_search_tool = POISearchTool()
        
    def lookup_iata_code(self, city_name: str) -> str:
        """
        Step 1: Look up the IATA code for a city.
        
        Args:
            city_name: Name of the city
            
        Returns:
            IATA code (e.g., 'JFK', 'LHR')
        """
        print(f"\n[STEP 1] Looking up IATA code for: {city_name}")
        print("-" * 50)
        
        result = self.iata_lookup_tool._run(city_name=city_name)
        print(f"Result: {result}")
        
        return result
    
    def search_flights(self, departure_city: str, arrival_city: str, 
                      start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Step 2: Search for flights between two cities.
        
        Args:
            departure_city: Departure city name
            arrival_city: Destination city name
            start_date: Departure date (YYYY-MM-DD)
            end_date: Return date (YYYY-MM-DD)
            
        Returns:
            List of flight options
        """
        print(f"\n[STEP 2] Searching for flights")
        print("-" * 50)
        print(f"Route: {departure_city} → {arrival_city}")
        print(f"Dates: {start_date} to {end_date}")
        
        # Get IATA codes
        departure_iata = self._extract_iata_code(self.lookup_iata_code(departure_city))
        arrival_iata = self._extract_iata_code(self.lookup_iata_code(arrival_city))
        
        if not departure_iata or not arrival_iata:
            print("❌ Failed to obtain valid IATA codes")
            return []
        
        print(f"\nDeparture IATA: {departure_iata}")
        print(f"Arrival IATA: {arrival_iata}")
        
        # Search flights
        result = self.flight_search_tool._run(
            departure_iata=departure_iata,
            arrival_iata=arrival_iata,
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"\nFlight Search Result: {result}")
        
        # Parse result
        try:
            flights = json.loads(result)
            return flights
        except json.JSONDecodeError:
            print(f"Note: {result}")
            return []
    
    def _extract_iata_code(self, result: str) -> str:
        """
        Extract the 3-letter IATA code from the lookup result.
        
        Args:
            result: Result string from IATA lookup
            
        Returns:
            3-letter IATA code or empty string if not found
        """
        import re
        # Match exactly 3 uppercase letters
        match = re.search(r'\b([A-Z]{3})\b', result.strip().upper())
        return match.group(1) if match else ""
    
    def search_poi(self, city_name: str) -> str:
        """
        Step 3: Search for points of interest and activities.
        
        Args:
            city_name: Name of the destination city
            
        Returns:
            POI search results
        """
        print(f"\n[STEP 3] Searching for Points of Interest in: {city_name}")
        print("-" * 50)
        
        result = self.poi_search_tool._run(city_name=city_name)
        print(f"Result:\n{result}")
        
        return result
    
    def plan_trip(self, departure_city: str, arrival_city: str, 
                  start_date: str, end_date: str) -> ItineraryPlan:
        """
        Complete trip planning workflow combining all tools.
        
        Args:
            departure_city: Starting city
            arrival_city: Destination city
            start_date: Trip start date (YYYY-MM-DD)
            end_date: Trip end date (YYYY-MM-DD)
            
        Returns:
            Structured ItineraryPlan
        """
        print("\n" + "=" * 60)
        print("🌍 AI TRAVEL AGENT - COMPLETE TRIP PLANNER")
        print("=" * 60)
        
        # Step 1: Search flights
        flights = self.search_flights(departure_city, arrival_city, start_date, end_date)
        
        # Step 2: Search POIs
        poi_info = self.search_poi(arrival_city)
        
        # Step 3: Create structured itinerary
        print(f"\n[STEP 4] Creating structured itinerary plan")
        print("-" * 50)
        
        # Convert flight results to FlightOption objects
        flight_options = []
        if flights:
            for flight in flights[:3]:  # Take top 3
                flight_options.append(
                    FlightOption(
                        price_usd=flight.get('price_usd', 'N/A'),
                        airline_code=flight.get('airline_code', 'N/A'),
                        duration=flight.get('duration', 'N/A')
                    )
                )
        
        # Create sample daily plan
        trip_duration = (end_date - start_date).days if isinstance(start_date, str) else 7
        daily_plan = {
            "Day 1": f"Arrive in {arrival_city}, check-in, rest and explore nearby areas",
            "Day 2-5": "Visit major attractions and landmarks",
            "Day 6": "Shopping and local cuisine exploration",
            "Day 7": "Last-minute sightseeing and departure preparation"
        }
        
        # Construct itinerary
        itinerary = ItineraryPlan(
            destination=arrival_city,
            travel_dates=f"{start_date} to {end_date}",
            flights=flight_options,
            poi_summary=poi_info[:500] + "..." if len(poi_info) > 500 else poi_info,
            daily_plan=daily_plan
        )
        
        print("\n✅ Itinerary created successfully!")
        return itinerary


def test_individual_tools():
    """Test each tool independently."""
    print("\n" + "=" * 60)
    print("🧪 TESTING INDIVIDUAL TOOLS")
    print("=" * 60)
    
    orchestrator = TravelAgentOrchestrator()
    
    # Test 1: IATA Lookup
    print("\n--- Test 1: City to IATA Lookup ---")
    orchestrator.lookup_iata_code("London")
    
    # Test 2: POI Search
    print("\n--- Test 2: Points of Interest Search ---")
    orchestrator.search_poi("Paris")
    
    # Test 3: Flight Search
    print("\n--- Test 3: Flight Search ---")
    orchestrator.search_flights(
        departure_city="New York",
        arrival_city="London",
        start_date="2026-05-10",
        end_date="2026-05-17"
    )


def test_complete_workflow():
    """Test the complete trip planning workflow."""
    print("\n" + "=" * 60)
    print("🎯 TESTING COMPLETE WORKFLOW")
    print("=" * 60)
    
    orchestrator = TravelAgentOrchestrator()
    
    # Plan a trip
    itinerary = orchestrator.plan_trip(
        departure_city="San Francisco",
        arrival_city="Barcelona",
        start_date="2026-06-01",
        end_date="2026-06-08"
    )
    
    # Display final itinerary
    print("\n" + "=" * 60)
    print("📋 FINAL ITINERARY")
    print("=" * 60)
    print(itinerary.model_dump_json(indent=2))


def main():
    """Main entry point for the travel agent."""
    import sys
    
    print("\n🚀 AI TRAVEL AGENT INITIALIZED")
    print("Choose a test mode:")
    print("1. Test individual tools")
    print("2. Test complete workflow")
    print("3. Custom trip planning (interactive)")
    
    choice = input("\nEnter your choice (1/2/3): ").strip()
    
    if choice == "1":
        test_individual_tools()
    elif choice == "2":
        test_complete_workflow()
    elif choice == "3":
        departure = input("Enter departure city: ").strip()
        arrival = input("Enter destination city: ").strip()
        start = input("Enter start date (YYYY-MM-DD): ").strip()
        end = input("Enter end date (YYYY-MM-DD): ").strip()
        
        orchestrator = TravelAgentOrchestrator()
        itinerary = orchestrator.plan_trip(departure, arrival, start, end)
        
        print("\n" + "=" * 60)
        print("📋 YOUR TRAVEL ITINERARY")
        print("=" * 60)
        print(itinerary.model_dump_json(indent=2))
    else:
        print("Invalid choice. Running default test...")
        test_complete_workflow()


if __name__ == "__main__":
    main()
