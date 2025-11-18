from typing import List, Dict
import json
from datetime import datetime, timedelta
from llm.model import LocalLLM
from fetchers.google_places import GooglePlacesFetcher
from fetchers.wikipedia import WikipediaFetcher
from fetchers.wikivoyage import WikivoyageFetcher
from fetchers.wikimedia_commons import WikimediaCommonsFetcher
from fetchers.web_scraper import WebScraper

class ItineraryPlanner:
    """Main service for planning vacation itineraries using local LLM"""

    def __init__(self):
        self.llm = LocalLLM()
        self.google_places = GooglePlacesFetcher()
        self.wikipedia = WikipediaFetcher()
        self.wikivoyage = WikivoyageFetcher()
        self.wikimedia = WikimediaCommonsFetcher()
        self.scraper = WebScraper()

    def is_llm_ready(self) -> bool:
        """Check if LLM is loaded"""
        return self.llm.is_ready()

    async def generate_itinerary(self, destinations: List[Dict], preferences: str) -> Dict:
        """Generate a complete vacation itinerary"""

        print(f"\n{'='*60}")
        print(f"Starting itinerary generation for {len(destinations)} destination(s)")
        print(f"{'='*60}\n")

        # Gather information about each destination
        enriched_destinations = []
        for i, dest in enumerate(destinations, 1):
            # Handle both dict and Pydantic objects
            dest_name = dest.name if hasattr(dest, 'name') else dest['name']
            dest_dict = dest.dict() if hasattr(dest, 'dict') else dest

            print(f"[{i}/{len(destinations)}] Gathering information for {dest_name}...")
            dest_info = await self._gather_destination_info(dest_name)
            enriched_destinations.append({
                **dest_dict,
                **dest_info
            })
            print(f"    ✓ Found {len(dest_info.get('attractions', []))} attractions")

        # Generate itinerary using LLM
        print(f"\n{'='*60}")
        print("Generating personalized itinerary with AI...")
        print("This may take 30-60 seconds...")
        print(f"{'='*60}\n")

        markdown = self._generate_markdown_itinerary(
            enriched_destinations,
            preferences,
            enriched_destinations  # Pass for image gallery
        )

        print(f"\n{'='*60}")
        print("✓ Itinerary generation complete!")
        print(f"{'='*60}\n")

        # Structure the itinerary data
        itinerary = self._structure_itinerary(enriched_destinations, markdown)

        return {
            "markdown": markdown,
            "itinerary": itinerary
        }

    async def _gather_destination_info(self, destination: str) -> Dict:
        """Gather information from multiple sources"""

        # Wikivoyage info (preferred for travel)
        wikivoyage_info = self.wikivoyage.get_destination_info(destination)

        # Wikipedia info (backup)
        wiki_info = self.wikipedia.get_destination_info(destination)

        # Google Places attractions
        attractions = self.google_places.search_attractions(destination, limit=8)

        # Travel tips
        scraper_info = self.scraper.search_destination_info(destination)

        # Combine images from multiple sources
        all_images = []

        # 1. Wikivoyage images (best for travel)
        if wikivoyage_info.get('images'):
            all_images.extend(wikivoyage_info['images'][:5])
            print(f"   ✓ Found {len(wikivoyage_info['images'])} images from Wikivoyage")

        # 2. Wikipedia images
        if wiki_info.get('images'):
            all_images.extend(wiki_info['images'][:3])
            print(f"   ✓ Found {len(wiki_info['images'])} images from Wikipedia")

        # 3. If we still don't have enough images, search Wikimedia Commons
        if len(all_images) < 5:
            print(f"   🔍 Searching Wikimedia Commons for more images...")
            commons_images = self.wikimedia.get_destination_images(destination, limit=8)
            all_images.extend(commons_images)
            print(f"   ✓ Found {len(commons_images)} images from Wikimedia Commons")

        # Use Wikivoyage summary if available, fallback to Wikipedia
        summary = wikivoyage_info.get('summary') or wiki_info.get('summary', '')
        url = wikivoyage_info.get('url') or wiki_info.get('url', '')

        print(f"   📸 Total images collected: {len(all_images)}")

        return {
            'wiki_summary': summary,
            'wiki_url': url,
            'attractions': attractions,
            'tips': scraper_info.get('tips', []),
            'images': all_images[:10],  # Keep up to 10 images
            'wikivoyage_sections': {
                'see': wikivoyage_info.get('see', ''),
                'do': wikivoyage_info.get('do', ''),
                'eat': wikivoyage_info.get('eat', ''),
            }
        }

    def _generate_markdown_itinerary(self, destinations: List[Dict], preferences: str, enriched_destinations: List[Dict]) -> str:
        """Use LLM to generate markdown itinerary"""

        # Prepare context for LLM
        context = self._prepare_llm_context(destinations, preferences)

        # Create prompt
        system_prompt = """You are a professional travel planner. Create detailed, engaging vacation itineraries based on the provided destination information and user preferences. Format your response in clean markdown with:
- Clear day-by-day schedule
- Activity recommendations with timing
- Dining suggestions
- Travel tips and local insights
- Must-see attractions

Be specific, practical, and enthusiastic. Make the itinerary feel personalized.

IMPORTANT: Start with a creative, destination-specific title (e.g., "5-Day Adventure in Tokyo"). Do NOT use generic titles like "Your Dream Vacation Itinerary" or "Vacation Itinerary"."""

        user_prompt = f"""Create a vacation itinerary with the following information:

DESTINATIONS:
{context['destinations_text']}

USER PREFERENCES:
{preferences}

AVAILABLE ATTRACTIONS AND INFO:
{context['attractions_text']}

Generate a complete, day-by-day itinerary in markdown format. Include specific times, practical advice, and make it exciting!"""

        # Generate with LLM
        full_prompt = self.llm.create_prompt(system_prompt, user_prompt)
        itinerary_text = self.llm.generate(full_prompt, max_tokens=3000, temperature=0.7)

        # Debug: Print first 200 chars of LLM output
        print(f"\n{'='*60}")
        print(f"LLM OUTPUT (first 200 chars):")
        print(f"{itinerary_text[:200]}")
        print(f"{'='*60}\n")

        # Create final markdown
        # Remove generic headers if LLM generated them (despite instructions)
        lines = itinerary_text.strip().split('\n')

        print(f"First line from LLM: {lines[0] if lines else 'NO LINES'}")

        # Remove any leading generic headers
        while lines and any(header.lower() in lines[0].lower() for header in ['your dream vacation', 'vacation itinerary']):
            print(f"🗑️  REMOVING GENERIC HEADER: {lines[0]}")
            lines.pop(0)
            # Also remove any empty lines after the header
            while lines and not lines[0].strip():
                lines.pop(0)

        # Rejoin the text
        itinerary_text = '\n'.join(lines)

        # Split into first line (title) and rest
        lines = itinerary_text.split('\n', 1)

        # Add date after the first line (which should be the actual trip title)
        generated_date = f"\nGenerated on {datetime.now().strftime('%B %d, %Y')}\n\n---\n\n"

        if len(lines) > 1:
            markdown = f"{lines[0]}\n{generated_date}{lines[1]}"
        else:
            markdown = f"{itinerary_text}\n{generated_date}"

        # Add image gallery if available
        image_gallery = self._create_image_gallery(enriched_destinations)
        if image_gallery:
            markdown += f"\n\n{image_gallery}\n\n"

        markdown += f"\n\n---\n\n## Additional Resources\n\n"

        # Add destination links
        for dest in destinations:
            if dest.get('wiki_url'):
                markdown += f"\n- [{dest['name']}]({dest['wiki_url']})"

        markdown += "\n\n*Happy travels!*"

        return markdown

    def _prepare_llm_context(self, destinations: List[Dict], preferences: str) -> Dict:
        """Prepare context information for LLM"""

        destinations_text = ""
        attractions_text = ""

        for i, dest in enumerate(destinations, 1):
            name = dest['name']
            dates = ""
            if dest.get('start_date'):
                dates = f" ({dest['start_date']} to {dest.get('end_date', 'TBD')})"

            destinations_text += f"\n{i}. {name}{dates}"

            # Add wiki summary
            if dest.get('wiki_summary'):
                summary = dest['wiki_summary'][:500]  # Limit length
                destinations_text += f"\n   Overview: {summary}..."

            # Add attractions
            if dest.get('attractions'):
                attractions_text += f"\n\nAttractions in {name}:"
                for attr in dest['attractions'][:6]:
                    rating = attr.get('rating', 'N/A')
                    attractions_text += f"\n- {attr['name']} (Rating: {rating})"

            # Add tips
            if dest.get('tips'):
                attractions_text += f"\n\nTravel Tips for {name}:"
                for tip in dest['tips'][:3]:
                    attractions_text += f"\n- {tip}"

        return {
            'destinations_text': destinations_text,
            'attractions_text': attractions_text
        }

    def _create_image_gallery(self, destinations: List[Dict]) -> str:
        """Create an image gallery from destination images"""
        gallery_md = "## Photo Gallery\n\n"
        has_images = False

        for dest in destinations:
            images = dest.get('images', [])
            print(f"📸 Destination: {dest['name']} - Found {len(images)} images")
            if images:
                has_images = True
                gallery_md += f"### {dest['name']}\n\n"
                for img_url in images[:5]:  # Show up to 5 images per destination
                    print(f"   Adding image: {img_url[:80]}...")
                    gallery_md += f"![{dest['name']}]({img_url})\n\n"

        if has_images:
            print(f"✅ Created photo gallery with images!")
        else:
            print(f"❌ No images found for gallery")

        return gallery_md if has_images else ""

    def _structure_itinerary(self, destinations: List[Dict], markdown: str) -> Dict:
        """Structure itinerary data for API response"""
        return {
            'total_destinations': len(destinations),
            'destinations': [
                {
                    'name': d['name'],
                    'start_date': d.get('start_date'),
                    'end_date': d.get('end_date'),
                    'attractions_count': len(d.get('attractions', []))
                }
                for d in destinations
            ],
            'generated_at': datetime.now().isoformat()
        }
