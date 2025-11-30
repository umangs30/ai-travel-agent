import os
import requests
from dotenv import load_dotenv
import json
from typing import Type

# --- Core Imports ---
from langchain.tools import BaseTool
from tavily import TavilyClient

from core.pydantics import FlightSearchInput, IATALookupInput

# Load environment variables
load_dotenv()

def get_amadeus_token() -> str:
    """
    Retrieves a new Amadeus access token for the test environment.
    Handles API configuration using environment variables.
    """
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    data = {
        'grant_type': 'client_credentials',
        'client_id': os.getenv('AMADEUS_CLIENT_ID'),
        'client_secret': os.getenv('AMADEUS_CLIENT_SECRET')
    }
    
    if not data['client_id'] or not data['client_secret']:
        raise ValueError("AMADEUS_CLIENT_ID or AMADEUS_CLIENT_SECRET not set in .env file.")

    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()['access_token']


class FlightSearchTool(BaseTool):
    name: str = "Amadeus Flight Search Tool"
    description: str = "Searches for real-time flight offers using Amadeus. REQUIRES 3-letter IATA codes and dates in YYYY-MM-DD format."
    args_schema: Type[FlightSearchInput] = FlightSearchInput

    def _run(self, departure_iata: str, arrival_iata: str, start_date: str, end_date: str) -> str:
        
        try:
            token = get_amadeus_token()
        except Exception as e:
            return f"Error obtaining Amadeus token: {str(e)}"

        url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
        headers = {'Authorization': f'Bearer {token}'}
        
        params = {
            'originLocationCode': departure_iata.upper(),
            'destinationLocationCode': arrival_iata.upper(),
            'departureDate': start_date,
            'returnDate': end_date,
            'adults': 1,
            'max': 3,
            'currencyCode': 'USD'
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            offers = []
            if 'data' in data:
                for offer in data['data']:
                    price = offer['price']['total']
                    airline_code = offer['itineraries'][0]['segments'][0]['carrierCode']
                    duration = offer['itineraries'][0]['duration'].replace('PT', '').replace('H', 'h ').replace('M', 'm')
                    
                    offers.append({
                        "price_usd": price,
                        "airline_code": airline_code,
                        "duration": duration,
                    })

            if not offers:
                return "No real-time flight offers found for the specified criteria. The LLM should proceed to the next planning step."
            
            return json.dumps(offers)

        except requests.exceptions.RequestException as e:
            return f"Amadeus API Request Failed: {e}"


# 2. City to IATA Tool (Uses Tavily Search)
class CityToIATATool(BaseTool):
    name: str = "City to IATA Lookup"
    description: str = "Searches the web using Tavily to find the 3-letter IATA code for a given city name."
    args_schema: Type[IATALookupInput] = IATALookupInput
    
    def _run(self, city_name: str) -> str:
        tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
        if not tavily.api_key:
             return "TAVILY_API_KEY is missing. Cannot perform IATA lookup."

        try:
            query = f"IATA airport code {city_name}"
            search_result = tavily.search(query=query, search_depth='basic', max_results=1)
            
            if search_result['results'] and search_result['results'][0]['content']:
                content = search_result['results'][0]['content']
                
                # Extract 3-letter IATA code from the content
                # Look for patterns like "JFK", "LHR", "CDG" (3 consecutive uppercase letters)
                import re
                iata_match = re.search(r'\b([A-Z]{3})\b', content)
                
                if iata_match:
                    iata_code = iata_match.group(1)
                    return iata_code
                
                return f"Could not extract IATA code from search results for {city_name}."
            
            return f"Could not find IATA code for {city_name} via search."
        
        except Exception as e:
            return f"Error during IATA lookup: {e}"


# 3. Points of Interest (POI) Search Tool
class POISearchTool(BaseTool):
    name: str = "Points of Interest Search"
    description: str = "Searches the web for top tourist attractions, restaurants, and activities in a specific location."
    args_schema: Type[IATALookupInput] = IATALookupInput 
    
    def _run(self, city_name: str) -> str:
        tavily = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
        if not tavily.api_key:
             return "TAVILY_API_KEY is missing. Cannot perform POI search."

        try:
            query = f"Top 5 must-see tourist attractions, best restaurants, and recommended itinerary for a 7-day trip to {city_name}. Focus on names and descriptions."
            
            search_result = tavily.search(query=query, search_depth='advanced', max_results=5)
            
            summaries = [r['content'] for r in search_result['results']]
            
            return "Web Search Results for POIs:\n" + "\n---\n".join(summaries)
        
        except Exception as e:
            return f"Error during POI search: {e}"