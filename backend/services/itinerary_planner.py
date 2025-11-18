from typing import List, Dict
import json
from datetime import datetime, timedelta
from llm.model import LocalLLM
from fetchers.google_places import GooglePlacesFetcher
from fetchers.wikipedia import WikipediaFetcher
from fetchers.web_scraper import WebScraper

class ItineraryPlanner:
    """Main service for planning vacation itineraries using local LLM"""

    def __init__(self):
        self.llm = LocalLLM()
        self.google_places = GooglePlacesFetcher()
        self.wikipedia = WikipediaFetcher()
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
            preferences
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

        # Wikipedia info
        wiki_info = self.wikipedia.get_destination_info(destination)

        # Google Places attractions
        attractions = self.google_places.search_attractions(destination, limit=8)

        # Travel tips
        scraper_info = self.scraper.search_destination_info(destination)

        return {
            'wiki_summary': wiki_info.get('summary', ''),
            'wiki_url': wiki_info.get('url', ''),
            'attractions': attractions,
            'tips': scraper_info.get('tips', []),
            'images': wiki_info.get('images', [])[:3]
        }

    def _generate_markdown_itinerary(self, destinations: List[Dict], preferences: str) -> str:
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

Be specific, practical, and enthusiastic. Make the itinerary feel personalized."""

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

        # Create final markdown with header
        markdown = f"""# Your Dream Vacation Itinerary

Generated on {datetime.now().strftime('%B %d, %Y')}

---

{itinerary_text}

---

## Additional Resources

"""

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
