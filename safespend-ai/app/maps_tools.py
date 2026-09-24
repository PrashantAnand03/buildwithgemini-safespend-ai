"""Google Maps Geocoding and Places (New) function tools for SafeSpend AI."""

import json
import os
import urllib.parse
import urllib.request


def geocode_address(address: str) -> dict:
    """Turns a text address or location description into geographical coordinates (latitude, longitude).

    Args:
        address: The address, city, or landmark string (e.g., 'San Francisco, CA', '1600 Amphitheatre Pkwy, Mountain View, CA').

    Returns:
        A dictionary containing formatted_address, latitude, and longitude.
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"status": "error", "message": "GOOGLE_MAPS_API_KEY environment variable is not set."}

    encoded_address = urllib.parse.quote(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("status") == "OK" and data.get("results"):
            first_result = data["results"][0]
            location = first_result["geometry"]["location"]
            return {
                "status": "success",
                "formatted_address": first_result.get("formatted_address"),
                "location": {
                    "latitude": location.get("lat"),
                    "longitude": location.get("lng"),
                },
            }
        return {"status": "error", "message": f"Geocoding failed for address: '{address}'"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to geocode address: {str(e)}"}


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "store",
    radius_meters: float = 1000.0,
) -> dict:
    """Finds nearby places of a specified type (e.g., 'bank', 'supermarket', 'store', 'atm') using Places API (New).

    Args:
        latitude: Latitude coordinate of the search center.
        longitude: Longitude coordinate of the search center.
        place_type: Type of place to search for (e.g. 'bank', 'supermarket', 'store', 'atm').
        radius_meters: Search radius in meters (defaults to 1000m).

    Returns:
        A dictionary containing a list of nearby places with name, formatted_address, and location coordinates.
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"status": "error", "message": "GOOGLE_MAPS_API_KEY environment variable is not set."}

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
    }

    payload = {
        "includedTypes": [place_type.lower().strip()],
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                },
                "radius": float(radius_meters),
            }
        },
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        places_data = data.get("places", [])
        results = []
        for p in places_data:
            display_name = p.get("displayName", {}).get("text", "Unknown Place")
            results.append({
                "name": display_name,
                "address": p.get("formattedAddress"),
                "location": p.get("location"),
            })

        return {
            "status": "success",
            "count": len(results),
            "places": results,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to search nearby places: {str(e)}"}
