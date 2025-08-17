from django.conf import settings
import requests

# Google API Helper
def get_place_id(query):
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    params = {
        "input": query,
        "inputtype": "textquery",
        "fields": "place_id",
        "key": settings.GOOGLE_API_KEY
    }
    res = requests.get(url, params=params).json()
    candidates = res.get("candidates", [])
    return candidates[0]["place_id"] if candidates else None

def get_place_details(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,rating,reviews,business_status,types,photos",
        "key": settings.GOOGLE_API_KEY
    }
    res = requests.get(url, params=params).json()
    return res.get("result", {})

def get_photo_url(photo_ref, maxwidth=400):
    return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={maxwidth}&photoreference={photo_ref}&key={settings.GOOGLE_API_KEY}"