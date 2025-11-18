import googlemaps
import os
from typing import List, Dict, Optional
import requests

class GooglePlacesFetcher:
    """Fetch data from Google Places API"""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_PLACES_API_KEY", "")
        if self.api_key:
            self.client = googlemaps.Client(key=self.api_key)
        else:
            self.client = None
            print("Warning: GOOGLE_PLACES_API_KEY not set. Google Places features disabled.")

    def search_attractions(self, location: str, limit: int = 10) -> List[Dict]:
        """Search for attractions in a location"""
        if not self.client:
            return []

        try:
            # Get place details
            places_result = self.client.places(
                query=f"tourist attractions in {location}",
                type="tourist_attraction"
            )

            attractions = []
            for place in places_result.get('results', [])[:limit]:
                attractions.append({
                    'name': place.get('name', ''),
                    'address': place.get('formatted_address', ''),
                    'rating': place.get('rating', 0),
                    'types': place.get('types', []),
                    'place_id': place.get('place_id', '')
                })

            return attractions
        except Exception as e:
            print(f"Error fetching attractions for {location}: {e}")
            return []

    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """Get detailed information about a place"""
        if not self.client:
            return None

        try:
            details = self.client.place(
                place_id=place_id,
                fields=['name', 'rating', 'reviews', 'photos', 'formatted_address',
                        'opening_hours', 'website', 'formatted_phone_number']
            )
            return details.get('result', {})
        except Exception as e:
            print(f"Error fetching place details: {e}")
            return None

    def get_reviews(self, place_id: str, limit: int = 5) -> List[Dict]:
        """Get reviews for a place"""
        details = self.get_place_details(place_id)
        if not details:
            return []

        reviews = details.get('reviews', [])[:limit]
        return [{
            'author': r.get('author_name', 'Anonymous'),
            'rating': r.get('rating', 0),
            'text': r.get('text', ''),
            'time': r.get('relative_time_description', '')
        } for r in reviews]
