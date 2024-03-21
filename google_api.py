import requests
import os

def get_geolocation():
    """
    Obtain the geolocation using the Google Geolocation API.

    Returns:
    - The JSON response containing the geolocation information.
    """
    url = 'https://www.googleapis.com/geolocation/v1/geolocate?key={}'.format(os.getenv("GOOGLE_MAPS_API"))
    body = {
        "homeMobileCountryCode": 310,
        "homeMobileNetworkCode": 410,
        "radioType": "gsm",
        "carrier": "Vodafone",
        "considerIp": True
    }

    # Execute the HTTP POST request with the specified body
    response = requests.post(url, json=body)
    return response.json()

def search_nearby_places(api_key, latitude, longitude, radius, place_type, max_result_count=1):
    """
    Search for nearby places using the Google Places API.

    Parameters:
    - api_key: Your Google API key.
    - latitude: Latitude of the location to search.
    - longitude: Longitude of the location to search.
    - radius: Radius in meters within which to search.
    - place_type: Type of place to search for.
    - max_result_count: Maximum number of results to return.

    Returns:
    - A list of found places within the specified radius.
    """
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        'key': api_key,
        'location': f'{latitude},{longitude}',
        'radius': radius,
        'type': place_type,
        'language': 'en',  # Optional: Specify the language of the results.
    }

    response = requests.get(url, params=params)
    places = response.json().get('results', [])[:max_result_count]

    for place in places:
        place_name = place.get('name', 'N/A')
        print(f"Place Name: {place_name}")

    return places


def fetch_directions(api_key, origin_lat, origin_lng, destination_lat,
                     destination_lng, travel_mode="driving",):
    """
    Fetches directions between two points using the Google Directions API.

    Parameters:
    - api_key: Google API key.
    - origin_lat: Latitude of the origin.
    - origin_lng: Longitude of the origin.
    - destination_lat: Latitude of the destination.
    - destination_lng: Longitude of the destination.
    - travel_mode: Mode of transportation (e.g., driving, walking).
    - routing_preference: Routing preference (e.g., less walking, fewer transfers).

    Returns:
    - JSON data containing the directions.
    """
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        'key': api_key,
        'origin': f"{origin_lat},{origin_lng}",
        'destination': f"{destination_lat},{destination_lng}",
        'mode': travel_mode.lower(),
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data.get("error_message"):
        print(data["error_message"])
    elif "routes" in data and data["routes"]:
        return data
    else:
        print("No routes found. Something might be wrong with request data.")

    return data