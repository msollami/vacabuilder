import requests
from typing import List
import urllib.parse

class WikimediaCommonsFetcher:
    """Fetch images from Wikimedia Commons"""

    BASE_URL = "https://commons.wikimedia.org/w/api.php"

    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False

    def search_images(self, query: str, limit: int = 10) -> List[str]:
        """Search for images related to a location or topic"""
        try:
            # Try multiple search strategies
            all_images = []

            # Strategy 1: Direct search
            images = self._search_by_query(query, limit)
            all_images.extend(images)

            # Strategy 2: Search with "landscape" or "city" suffix
            if len(all_images) < limit:
                landscape_images = self._search_by_query(f"{query} landscape", limit - len(all_images))
                all_images.extend(landscape_images)

            # Strategy 3: Search with "tourism" suffix
            if len(all_images) < limit:
                tourism_images = self._search_by_query(f"{query} tourism", limit - len(all_images))
                all_images.extend(tourism_images)

            # Remove duplicates while preserving order
            seen = set()
            unique_images = []
            for img in all_images:
                if img not in seen:
                    seen.add(img)
                    unique_images.append(img)

            return unique_images[:limit]

        except Exception as e:
            print(f"Error searching Wikimedia Commons for {query}: {e}")
            return []

    def _search_by_query(self, query: str, limit: int) -> List[str]:
        """Search for images by query"""
        try:
            # Search for files
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': f'File:{query}',
                'srnamespace': 6,  # File namespace
                'srlimit': limit * 2,  # Get more to filter
                'srinfo': 'totalhits'
            }

            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            data = response.json()

            search_results = data.get('query', {}).get('search', [])

            image_urls = []
            for result in search_results:
                title = result.get('title', '')

                # Filter out non-photo files
                if self._is_valid_image(title):
                    url = self._get_image_url(title)
                    if url:
                        image_urls.append(url)
                        if len(image_urls) >= limit:
                            break

            return image_urls

        except Exception as e:
            print(f"Error in Wikimedia Commons search: {e}")
            return []

    def _is_valid_image(self, title: str) -> bool:
        """Check if the file is a valid image"""
        lower_title = title.lower()

        # Exclude unwanted file types
        exclude_keywords = [
            'icon', 'logo', 'svg', 'map', 'diagram', 'chart',
            'flag', 'coat', 'seal', 'symbol', 'wikidata',
            'button', 'banner'
        ]

        if any(keyword in lower_title for keyword in exclude_keywords):
            return False

        # Include photo formats
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        return any(ext in lower_title for ext in valid_extensions)

    def _get_image_url(self, title: str) -> str:
        """Get direct URL for an image"""
        try:
            params = {
                'action': 'query',
                'format': 'json',
                'titles': title,
                'prop': 'imageinfo',
                'iiprop': 'url',
                'iiurlwidth': 800  # Get 800px wide version
            }

            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            data = response.json()

            pages = data.get('query', {}).get('pages', {})
            if pages:
                page = next(iter(pages.values()))
                imageinfo = page.get('imageinfo', [])
                if imageinfo:
                    # Try to get the thumbnail URL, fallback to original
                    return imageinfo[0].get('thumburl') or imageinfo[0].get('url')
            return None

        except Exception as e:
            print(f"Error getting image URL: {e}")
            return None

    def get_destination_images(self, destination: str, limit: int = 10) -> List[str]:
        """Get images for a destination using multiple search terms"""
        all_images = []

        # Search with different terms
        search_terms = [
            destination,
            f"{destination} city",
            f"{destination} landscape",
            f"{destination} architecture",
            f"{destination} street"
        ]

        for term in search_terms:
            if len(all_images) >= limit:
                break
            images = self.search_images(term, limit=3)
            all_images.extend(images)

        # Remove duplicates
        unique_images = list(dict.fromkeys(all_images))
        return unique_images[:limit]
