import requests

GOOGLE_PLACES_API_KEY = "AIzaSyCfT5lgVhG5shvwQG1cPrtaQvoKE_CUHtY"  # Replace with your actual API key

def get_reviews(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    
    params = {
        "key": GOOGLE_PLACES_API_KEY,
        "place_id": place_id,  # Place ID for a specific restaurant
        "fields": "name,rating,reviews"  # Fetch name, rating, and reviews
    }
    
    response = requests.get(url, params=params)
    data = response.json()

    reviews = []
    
    if "result" in data:
        if "reviews" in data["result"]:
            for review in data["result"]["reviews"]:
                reviews.append({
                    "author": review.get("author_name", "Anonymous"),
                    "rating": review.get("rating", "No Rating"),
                    "text": review.get("text", "No Review")
                })
        else:
            reviews = []  # No reviews available for this place
    return reviews

def get_restaurants(location="9.9816,76.2999", radius=5000, keyword="vegetarian"):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    
    params = {
        "key": GOOGLE_PLACES_API_KEY,
        "location": location,  # Format: latitude,longitude for Ernakulam
        "radius": radius,      # 5000 meters = 5km
        "type": "restaurant",  # Restaurant search
        "keyword": keyword     # Searching for vegetarian restaurants
    }
    
    response = requests.get(url, params=params)
    data = response.json()

    if "results" not in data or not data["results"]:
        return []  # No results found

    restaurants = []

    for place in data["results"]:
        # Fetch reviews for each place using the place_id
        place_id = place.get("place_id")
        reviews = get_reviews(place_id)  # Get reviews for the place
        
        restaurants.append({
            "name": place.get("name", "No Name"),
            "rating": place.get("rating", "No Rating"),
            "address": place.get("vicinity", "No Address"),
            "reviews": reviews
        })
    
    return restaurants
