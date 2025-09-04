import os
import requests
import serpapi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY")  # WeatherAPI.com
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY")
AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
UNSPLASH_API_KEY = os.getenv("UNSPLASH_API_KEY")

#  WEATHER (WeatherAPI.com)

def get_weather(city: str, days: int = 3):
    """
    Get weather forecast for a city using WeatherAPI.com.
    """
    url = f"http://api.weatherapi.com/v1/forecast.json"
    params = {
        "key": WEATHERAPI_KEY,
        "q": city,
        "days": days,
        "aqi": "no",
        "alerts": "no"
    }
    response = requests.get(url, params=params)
    data = response.json()

    if response.status_code != 200 or "forecast" not in data:
        return {"error": data.get("error", {}).get("message", "Weather data not available")}

    forecast = []
    for day in data["forecast"]["forecastday"]:
        forecast.append({
            "date": day["date"],
            "avg_temp_c": day["day"]["avgtemp_c"],
            "condition": day["day"]["condition"]["text"],
            "icon": day["day"]["condition"]["icon"]
        })
    return forecast

#  PLACES (SerpAPI - Google Maps Results)

def search_places(query: str, location: str, num_results: int = 5):
    """
    Search for places using SerpAPI's Google Maps engine.
    """
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_maps",
        "q": query,
        "location": location,
        "hl": "en",
        "type": "search",
        "api_key": SERPAPI_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "local_results" not in data:
        return {"error": data.get("error", "No results found")}

    results = []
    for result in data.get("local_results", [])[:num_results]:
        results.append({
            "name": result.get("title"),
            "address": result.get("address"),
            "rating": result.get("rating"),
            "reviews": result.get("reviews"),
            "type": result.get("type"),
            "gps_coordinates": result.get("gps_coordinates"),
        })
    return results

#  CURRENCY (ExchangeRate API)

def get_exchange_rate(base: str = "USD", target: str = "INR"):
    """
    Get real-time exchange rate between two currencies.
    """
    url = f"http://api.exchangeratesapi.io/v1/latest?access_key={EXCHANGE_API_KEY}&symbols={base},{target}"
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200 or "rates" not in data:
        return {"error": data.get("error", "Exchange rate data not available")}

    rate = data["rates"].get(target) / data["rates"].get(base)
    return {"base": base, "target": target, "rate": rate}

#  AMADEUS API (Flights + Hotels)

def get_amadeus_access_token():
    """
    Get OAuth2 access token from Amadeus API.
    """
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": AMADEUS_API_KEY,
        "client_secret": AMADEUS_API_SECRET
    }
    response = requests.post(url, data=data, headers=headers)
    return response.json().get("access_token")

def search_flights(origin: str, destination: str, departure_date: str, adults: int = 1):
    """
    Search flights using Amadeus API.
    Example date: '2025-09-01'
    """
    token = get_amadeus_access_token()
    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date,
        "adults": adults,
        "currencyCode": "USD",
        "max": 3
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()

def search_hotels(city_code: str):
    """
    Search hotels in a city using Amadeus API.
    City codes can be IATA (e.g., 'DEL' for Delhi).
    """
    token = get_amadeus_access_token()
    url = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"cityCode": city_code}
    response = requests.get(url, headers=headers, params=params)
    return response.json()


# GOOGLE PLACES API

def search_google_places(query: str, location: str, radius: int = 5000):
    """
    Search for places using Google Places API.
    Location = "lat,lng"
    """
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "location": location,
        "radius": radius,
        "key": GOOGLE_PLACES_API_KEY
    }
    response = requests.get(url, params=params)
    return response.json().get("results", [])

def get_place_details(place_id: str):
    """
    Get detailed info about a place from Google Places API.
    """
    url = f"https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,rating,formatted_address,formatted_phone_number,website,review,photo",
        "key": GOOGLE_PLACES_API_KEY
    }
    response = requests.get(url, params=params)
    return response.json()

#  REST COUNTRIES API

def get_country_info(country: str):
    """
    Get country info, visa requirements, population, region, etc.
    """
    url = f"https://restcountries.com/v3.1/name/{country}"
    response = requests.get(url)
    if response.status_code != 200:
        return {"error": "Country data not available"}
    return response.json()[0]


#  UNSPLASH API

def get_destination_photo(query: str, count: int = 1):
    """
    Get high-quality destination photos from Unsplash.
    """
    url = "https://api.unsplash.com/search/photos"
    params = {
        "query": query,
        "per_page": count,
        "orientation": "landscape",
        "client_id": UNSPLASH_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    photos = [p["urls"]["regular"] for p in data.get("results", [])]
    return photos
