import requests
from typing import Dict, List, Optional
import re

class WikivoyageFetcher:
    """Fetch travel information from Wikivoyage"""

    BASE_URL = "https://en.wikivoyage.org/w/api.php"

    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for development

    def get_destination_info(self, destination: str) -> Dict:
        """Get comprehensive travel information for a destination"""
        try:
            # Search for the destination page
            page_title = self._search_destination(destination)
            if not page_title:
                return {'summary': None, 'images': [], 'sections': {}}

            # Get page content
            content = self._get_page_content(page_title)

            # Extract images
            images = self._get_page_images(page_title)

            # Parse sections
            sections = self._parse_sections(content)

            return {
                'title': page_title,
                'summary': sections.get('understand', '')[:500] if 'understand' in sections else content[:500],
                'url': f"https://en.wikivoyage.org/wiki/{page_title.replace(' ', '_')}",
                'images': images[:10],  # Get more images from Wikivoyage
                'see': sections.get('see', ''),
                'do': sections.get('do', ''),
                'eat': sections.get('eat', ''),
                'sleep': sections.get('sleep', ''),
                'stay_safe': sections.get('stay safe', ''),
            }
        except Exception as e:
            print(f"Error fetching Wikivoyage info for {destination}: {e}")
            return {'summary': None, 'images': [], 'sections': {}}

    def _search_destination(self, destination: str) -> Optional[str]:
        """Search for a destination page"""
        try:
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': destination,
                'srlimit': 1
            }

            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            data = response.json()

            if data.get('query', {}).get('search'):
                return data['query']['search'][0]['title']
            return None
        except Exception as e:
            print(f"Error searching Wikivoyage: {e}")
            return None

    def _get_page_content(self, page_title: str) -> str:
        """Get full page content"""
        try:
            params = {
                'action': 'query',
                'format': 'json',
                'titles': page_title,
                'prop': 'extracts',
                'explaintext': True,
                'exsectionformat': 'plain'
            }

            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            data = response.json()

            pages = data.get('query', {}).get('pages', {})
            if pages:
                page = next(iter(pages.values()))
                return page.get('extract', '')
            return ''
        except Exception as e:
            print(f"Error getting Wikivoyage content: {e}")
            return ''

    def _get_page_images(self, page_title: str) -> List[str]:
        """Get all images from a page"""
        try:
            params = {
                'action': 'query',
                'format': 'json',
                'titles': page_title,
                'prop': 'images',
                'imlimit': 50
            }

            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            data = response.json()

            pages = data.get('query', {}).get('pages', {})
            if not pages:
                return []

            page = next(iter(pages.values()))
            images = page.get('images', [])

            # Get image URLs
            image_urls = []
            for img in images:
                title = img.get('title', '')
                # Filter out icons and UI images
                if not any(x in title.lower() for x in ['icon', 'logo', 'button', 'wikivoyage']):
                    url = self._get_image_url(title)
                    if url:
                        image_urls.append(url)

            return image_urls
        except Exception as e:
            print(f"Error getting Wikivoyage images: {e}")
            return []

    def _get_image_url(self, image_title: str) -> Optional[str]:
        """Get direct URL for an image"""
        try:
            params = {
                'action': 'query',
                'format': 'json',
                'titles': image_title,
                'prop': 'imageinfo',
                'iiprop': 'url',
                'iiurlwidth': 800
            }

            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            data = response.json()

            pages = data.get('query', {}).get('pages', {})
            if pages:
                page = next(iter(pages.values()))
                imageinfo = page.get('imageinfo', [])
                if imageinfo:
                    return imageinfo[0].get('url')
            return None
        except Exception as e:
            return None

    def _parse_sections(self, content: str) -> Dict[str, str]:
        """Parse content into sections"""
        sections = {}

        # Common Wikivoyage sections
        section_names = ['understand', 'see', 'do', 'eat', 'drink', 'sleep', 'stay safe', 'get in', 'get around']

        for section in section_names:
            # Try to extract section content
            pattern = rf'{section}\s*==+\s*\n(.*?)(?:==|$)'
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                sections[section.lower()] = match.group(1).strip()[:1000]

        return sections
