"""Main entry point for the LinkedIn Jobs Scraper Apify actor."""
import asyncio
import logging
from apify import Actor
from .scraper import LinkedInJobsScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def main():
    """Main function that runs the LinkedIn Jobs Scraper."""
    async with Actor() as actor:
        # Get input
        actor_input = await actor.get_input() or {}
        
        # Log the start of the scraping process
        logging.info("Starting LinkedIn Jobs Scraper")
        logging.info(f"Input parameters: {actor_input}")
        
        try:
            # Initialize and run scraper
            scraper = LinkedInJobsScraper(actor)
            await scraper.run(actor_input)
            
            logging.info("Scraping completed successfully")
            
        except Exception as e:
            logging.error(f"Scraping failed: {str(e)}")
            raise

if __name__ == "__main__":
    asyncio.run(main())
