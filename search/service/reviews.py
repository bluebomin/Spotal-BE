import requests
from decouple import config

GOOGLE_API_KEY = config("GOOGLE_API_KEY")

def get_place_id(query):
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": query,
        "inputtype": "textquery",
        "fields": "place_id",
        "key": GOOGLE_API_KEY
    }
    res = requests.get(url, params=params).json()
    candidates = res.get("candidates", [])
    return candidates[0]["place_id"] if candidates else None

def get_place_details(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,rating,reviews",
        "key": GOOGLE_API_KEY
    }
    res = requests.get(url, params=params).json()
    return res.get("result", {})

