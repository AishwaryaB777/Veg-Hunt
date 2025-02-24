import requests

GOOGLE_PLACES_API_KEY = "AIzaSyCfT5lgVhG5shvwQG1cPrtaQvoKE_CUHtY"  # Replace with your actual API key

def get_reviews_and_image(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "key": GOOGLE_PLACES_API_KEY,
        "place_id": place_id,
        "fields": "name,rating,reviews,photos"
    }
    response = requests.get(url, params=params)
    data = response.json()

    reviews = []
    image_url = None
    
    if "result" in data:
        if "reviews" in data["result"]:
            for review in data["result"]["reviews"]:
                reviews.append({
                    "author": review.get("author_name", "Anonymous"),
                    "rating": review.get("rating", "No Rating"),
                    "text": review.get("text", "No Review")
                })
        
        if "photos" in data["result"]:
            photo_reference = data["result"]["photos"][0]["photo_reference"]
            image_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={GOOGLE_PLACES_API_KEY}"
    
    return reviews, image_url


def get_restaurants(location="9.9816,76.2999", radius=5000, keyword="vegetarian"):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "key": GOOGLE_PLACES_API_KEY,
        "location": location,
        "radius": radius,
        "type": "restaurant",
        "keyword": keyword
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    if "results" not in data or not data["results"]:
        return []
    
    restaurants = []
    
    for place in data["results"]:
        place_id = place.get("place_id")
        reviews, image_url = get_reviews_and_image(place_id)
        
        restaurants.append({
            "name": place.get("name", "No Name"),
            "rating": place.get("rating", "No Rating"),
            "address": place.get("vicinity", "No Address"),
            "image_url": image_url if image_url else "https://via.placeholder.com/400",  # Placeholder if no image
            "reviews": reviews
        })
    
    return restaurants
