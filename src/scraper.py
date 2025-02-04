"""LinkedIn Jobs Scraper implementation."""
from typing import Dict, List, Optional
import asyncio
from datetime import datetime
import logging
from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup
import json

from apify import Actor
from apify.storages import RequestQueue, Dataset, KeyValueStore

from .config import DEFAULT_SETTINGS, ERROR_MESSAGES, INPUT_MAPPING
from .helpers import build_search_url, format_job_data

class LinkedInJobsScraper:
    def __init__(self, actor: Actor):
        self.actor = actor
        self.dataset = actor.open_dataset()
        self.request_queue = actor.open_request_queue()
        self.key_value_store = actor.open_key_value_store()
        
        self.browser: Optional[Browser] = None
        self.context = None
        self.page: Optional[Page] = None
        
        self.jobs_scraped = 0
        self.start_time = datetime.now()
        
        self.input_mapping = INPUT_MAPPING
        
        self.config = Config()  # Make sure this loads defaults correctly
        
        self.playwright = None  # Add this line to store playwright instance
        
    async def initialize(self):
        """Initialize the browser and create a new page."""
        self.playwright = await async_playwright().start()  # Store instance
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
            viewport={"width": 1920, "height": 1080}
        )
        self.page = await self.context.new_page()
        await self.page.set_default_timeout(30000)
        
        # Set up error handling
        self.page.on("console", lambda msg: logging.info(f"Browser console: {msg.text}"))
        self.page.on("pageerror", lambda err: logging.error(f"Page error: {err}"))
        
    async def close(self):
        """Proper resource cleanup"""
        if self.page and not self.page.is_closed():
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        await self.playwright.stop()  # Add playwright cleanup
        
    async def scrape_job_listings(self, search_params: Dict) -> List[Dict]:
        """Scrape job listings based on search parameters."""
        url = build_search_url(
            search_params["searchTerms"],
            search_params["location"],
            search_params.get("workType", "ANY")
        )
        
        await self.page.goto(url)
        await self.page.wait_for_load_state("networkidle", timeout=60000)
        
        jobs = []
        jobs_to_scrape = search_params.get("maxJobs", DEFAULT_SETTINGS["max_jobs_per_run"])
        
        # Use bulk content extraction
        content = await self.page.content()
        soup = BeautifulSoup(content, "html.parser")
        job_cards = soup.select(".job-card-container")
        
        # Process in batches
        batch_size = DEFAULT_SETTINGS["batch_size"]
        for i in range(0, len(job_cards), batch_size):
            batch = job_cards[i:i+batch_size]
            await self._process_batch(batch)
            
            # Check if we need to load more results
            if self.jobs_scraped >= jobs_to_scrape:
                break
                
            try:
                next_button = await self.page.query_selector("button.see-more-jobs")
                if next_button:
                    await next_button.click()
                    await self.page.wait_for_load_state("networkidle", timeout=60000)
                    await asyncio.sleep(DEFAULT_SETTINGS["request_delay"])
                else:
                    break
            except Exception as e:
                logging.error(f"Error loading more results: {str(e)}")
                break
        
        return jobs
    
    async def _process_batch(self, batch):
        jobs = []
        search_params = self.search_params
        jobs_to_scrape = self.jobs_to_scrape
        
        for card in batch:
            try:
                # Extract job data
                job_data = await self._extract_job_data(card)
                if job_data:
                    formatted_job = format_job_data(job_data, search_params)
                    jobs.append(formatted_job)
                    
                    # Save to dataset
                    await self.dataset.push_data(formatted_job)
                    self.jobs_scraped += 1
                    
                    # Update progress
                    await self.actor.push_data({
                        "status": "in_progress",
                        "jobs_scraped": self.jobs_scraped,
                        "target": jobs_to_scrape
                    })
                    
            except Exception as e:
                logging.error(f"Error processing job card: {str(e)}")
                continue
        
    async def _extract_job_data(self, card):
        try:
            return await card.evaluate('''element => ({
                id: element.closest('[data-entity-urn]')?.dataset.entityUrn.split(':').pop(),
                title: element.querySelector('[data-tracking-control-name="public_jobs_jserp-result_search-card"]')?.innerText.trim(),
                company: element.querySelector('[data-tracking-control-name="public_jobs_company-name"]')?.innerText.trim(),
                location: element.querySelector('[data-tracking-control-name="public_jobs_location"]')?.innerText.trim(),
                url: element.querySelector('a[data-tracking-control-name="public_jobs_jserp-result_search-card"]')?.href,
                posted_date: element.querySelector('time')?.datetime,
                salary: element.querySelector('[data-tracking-control-name="public_jobs_compensation"]')?.innerText.trim(),
                work_type: element.querySelector('[data-tracking-control-name="public_jobs_workplace-type"]')?.innerText.trim()
            })''')
        except Exception as e:
            logging.error(f"Evaluation failed: {str(e)}")
            return None
            
    async def run(self, actor_input: dict):
        """Main entry point for the scraper."""
        try:
            await self.initialize()
            
            # Merge input with defaults
            params = {**self.config.DEFAULT_INPUT, **actor_input}
            
            # Validate required parameters
            if not params.get('mandatoryKeywords') or not params.get('location'):
                raise ValueError("mandatoryKeywords and location are required")  # Updated error message
                
            # Build search parameters
            search_terms = {
                'mandatory': params['mandatoryKeywords'],
                'optional': params.get('optionalKeywords', []),
                'location': params['location'],
                'work_type': params.get('workType', 'ANY'),
                'max_jobs': params.get('maxJobs', 10)
            }
            
            # Use mapped input for scraping
            jobs = await self.scrape_job_listings(search_terms)
            
            # Save final results
            await self.key_value_store.set_value("OUTPUT", {
                "jobs": jobs,
                "metadata": {
                    "jobs_scraped": self.jobs_scraped,
                    "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
                    "search_params": search_terms
                }
            })
            
        except Exception as e:
            logging.error(f"Scraper error: {str(e)}")
            raise
            
        finally:
            await self.close()
