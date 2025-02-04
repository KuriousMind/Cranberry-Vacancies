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
    browser = None
    try:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        scraper = LinkedInJobsScraper(browser, context)
        await scraper.run()
    except Exception as e:
        logging.error(f"Scraping failed: {str(e)}")
        raise
    finally:
        if browser:
            await browser.close()
        logging.info("Browser resources cleaned up")

if __name__ == "__main__":
    asyncio.run(main())
