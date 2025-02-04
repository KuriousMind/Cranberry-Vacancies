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

from .config import DEFAULT_SETTINGS, ERROR_MESSAGES
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
        
    async def initialize(self):
        """Initialize the browser and create a new page."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch()
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
        # Set up error handling
        self.page.on("console", lambda msg: logging.info(f"Browser console: {msg.text}"))
        self.page.on("pageerror", lambda err: logging.error(f"Page error: {err}"))
        
    async def close(self):
        """Close browser and clean up resources."""
        if self.browser:
            await self.browser.close()
            
    async def scrape_job_listings(self, search_params: Dict) -> List[Dict]:
        """Scrape job listings based on search parameters."""
        url = build_search_url(
            search_params["searchTerms"],
            search_params["location"],
            search_params.get("workType", "ANY")
        )
        
        await self.page.goto(url)
        await self.page.wait_for_load_state("networkidle")
        
        jobs = []
        jobs_to_scrape = search_params.get("maxJobs", DEFAULT_SETTINGS["max_jobs_per_run"])
        
        while len(jobs) < jobs_to_scrape:
            # Extract job cards
            job_cards = await self.page.query_selector_all(".job-card-container")
            
            for card in job_cards:
                if len(jobs) >= jobs_to_scrape:
                    break
                    
                try:
                    # Click to load job details
                    await card.click()
                    await asyncio.sleep(DEFAULT_SETTINGS["request_delay"])
                    
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
            
            # Check if we need to load more results
            if len(jobs) < jobs_to_scrape:
                try:
                    next_button = await self.page.query_selector("button.see-more-jobs")
                    if next_button:
                        await next_button.click()
                        await self.page.wait_for_load_state("networkidle")
                        await asyncio.sleep(DEFAULT_SETTINGS["request_delay"])
                    else:
                        break
                except Exception as e:
                    logging.error(f"Error loading more results: {str(e)}")
                    break
                    
        return jobs
    
    async def _extract_job_data(self, card) -> Optional[Dict]:
        """Extract data from a job card."""
        try:
            # Get basic info from card
            title = await card.query_selector(".job-card-list__title")
            company = await card.query_selector(".job-card-container__company-name")
            location = await card.query_selector(".job-card-container__metadata-item")
            
            # Get job description from expanded view
            description = await self.page.query_selector(".show-more-less-html__markup")
            
            # Get posting date
            date_element = await card.query_selector("time")
            posted_date = await date_element.get_attribute("datetime") if date_element else None
            
            # Get salary if available
            salary_element = await self.page.query_selector(".compensation-metadata")
            salary = await salary_element.inner_text() if salary_element else None
            
            # Get work type
            work_type_element = await self.page.query_selector(".workplace-type")
            work_type = await work_type_element.inner_text() if work_type_element else None
            
            # Get job URL
            url_element = await card.query_selector("a.job-card-list__title")
            url = await url_element.get_attribute("href") if url_element else None
            
            return {
                "id": await card.get_attribute("data-job-id"),
                "title": await title.inner_text() if title else None,
                "company": await company.inner_text() if company else None,
                "location": await location.inner_text() if location else None,
                "description": await description.inner_text() if description else None,
                "posted_date": posted_date,
                "salary": salary,
                "work_type": work_type,
                "url": url
            }
            
        except Exception as e:
            logging.error(f"Error extracting job data: {str(e)}")
            return None
            
    async def run(self, input_data: Dict):
        """Main entry point for the scraper."""
        try:
            await self.initialize()
            
            # Validate input
            if not input_data.get("searchTerms") or not input_data.get("location"):
                raise ValueError("Search terms and location are required")
                
            # Start scraping
            jobs = await self.scrape_job_listings(input_data)
            
            # Save final results
            await self.key_value_store.set_value("OUTPUT", {
                "jobs": jobs,
                "metadata": {
                    "jobs_scraped": self.jobs_scraped,
                    "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
                    "search_params": input_data
                }
            })
            
        except Exception as e:
            logging.error(f"Scraper error: {str(e)}")
            raise
            
        finally:
            await self.close()
