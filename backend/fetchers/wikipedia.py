import wikipedia
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Optional, List
import ssl
import urllib3

# Disable SSL warnings for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WikipediaFetcher:
    """Fetch travel information from Wikipedia/WikiVoyage"""

    def __init__(self):
        wikipedia.set_lang("en")

        # Configure session to bypass SSL verification
        session = requests.Session()
        session.verify = False

        # Monkey-patch the wikipedia library's session
        wikipedia.wikipedia.session = session

    def get_destination_summary(self, destination: str) -> Optional[str]:
        """Get a summary of a destination from Wikipedia"""
        try:
            # Try to find the page
            search_results = wikipedia.search(destination, results=3)
            if not search_results:
                return None

            # Get the first result
            page = wikipedia.page(search_results[0], auto_suggest=False)

            # Return summary (first few paragraphs)
            return page.summary
        except wikipedia.exceptions.DisambiguationError as e:
            # Try the first option in disambiguation
            try:
                page = wikipedia.page(e.options[0], auto_suggest=False)
                return page.summary
            except:
                return None
        except Exception as e:
            print(f"Error fetching Wikipedia summary for {destination}: {e}")
            return None

    def get_destination_info(self, destination: str) -> Dict:
        """Get comprehensive destination information"""
        try:
            search_results = wikipedia.search(destination, results=1)
            if not search_results:
                return {'summary': None, 'url': None}

            page = wikipedia.page(search_results[0], auto_suggest=False)

            return {
                'title': page.title,
                'summary': page.summary,
                'url': page.url,
                'content': page.content[:2000],  # First 2000 chars
                'images': page.images[:5] if hasattr(page, 'images') else []
            }
        except Exception as e:
            print(f"Error fetching destination info: {e}")
            return {'summary': None, 'url': None}

    def search_attractions(self, destination: str) -> List[str]:
        """Search for attractions related to a destination"""
        try:
            query = f"Tourist attractions in {destination}"
            results = wikipedia.search(query, results=10)
            return results
        except Exception as e:
            print(f"Error searching attractions: {e}")
            return []
