from pydantic import BaseModel, Field 
from typing import List, Dict
from datetime import date


class FlightSearchInput(BaseModel):
    """Input model for the FlightSearchTool (Amadeus API)."""
    departure_iata: str = Field(..., description="The departure airport IATA code, e.g., 'JFK'")
    arrival_iata: str = Field(..., description="The destination airport IATA code, e.g., 'LHR'")
    start_date: str = Field(..., description="The departure date in YYYY-MM-DD format (e.g., '2026-05-10')")
    end_date: str = Field(..., description="The return date in YYYY-MM-DD format (e.g., '2026-05-15')")

class IATALookupInput(BaseModel):
    """Input model for looking up the IATA code for a city."""
    city_name: str = Field(..., description="The name of the city for which to find the IATA code.")

# --- 2. FINAL ITINERARY OUTPUT SCHEMAS ---

class FlightOption(BaseModel):
    """Structured data for a single flight option retrieved from Amadeus."""
    price_usd: str = Field(description="Total price in USD.")
    airline_code: str = Field(description="Airline IATA code (e.g., UA, AA).")
    duration: str = Field(description="Total travel time, e.g., '10h 30m'.")

class ItineraryPlan(BaseModel):
    """The final structured itinerary output model for the user."""
    destination: str = Field(description="The final travel destination.")
    travel_dates: str = Field(description="The start and end dates of the trip.")
    flights: List[FlightOption] = Field(description="A list of 3 best flight options found.")
    poi_summary: str = Field(description="A detailed summary of top points of interest and activities.")
    daily_plan: Dict[str, str] = Field(description="A day-by-day plan (e.g., {'Day 1': 'Arrive, check-in, visit Big Ben'}).")