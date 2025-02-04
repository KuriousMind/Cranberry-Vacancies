"""Configuration settings for the LinkedIn Jobs Scraper."""

# Apify settings
DEFAULT_SETTINGS = {
    "max_jobs_per_run": 150,  # Safe limit for free tier
    "max_concurrent_pages": 1,
    "request_delay": 5,  # Increased base delay
    "batch_size": 25,
    "max_retries": 3,
    "memory_check_interval": 100,  # Check every 100 jobs instead of 1000
    "max_memory_usage": 900,  # MB
    "jitter": 2,  # Add random variation
    "network_idle_timeout": 10,  # Seconds to wait
    "animation_frame_delay": 0.5  # Wait for animations
}

# LinkedIn URL templates
LINKEDIN_URLS = {
    "base": "https://www.linkedin.com",
    "jobs": "https://www.linkedin.com/jobs/search/",
}

# Work type mappings
WORK_TYPES = {
    "REMOTE": "2",
    "HYBRID": "3",
    "ON_SITE": "1",
    "ANY": None
}

# Headers and request settings
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Error messages
ERROR_MESSAGES = {
    "rate_limit": "Rate limit exceeded. Waiting before retry...",
    "no_results": "No job listings found for the given search criteria.",
    "invalid_location": "Invalid location provided.",
    "memory_limit": "Approaching memory limit. Saving current progress...",
    "compute_limit": "Approaching compute unit limit. Finalizing current batch..."
}

# Input mapping
INPUT_MAPPING = {
    'search_terms': 'searchTerms',
    'location': 'location',
    'max_results': 'maxJobs',
    'optional_keywords': 'optionalKeywords',
    'work_type': 'workType',
    'start_urls': 'start_urls'
}

__version__ = "2.1.0"  # Major version bump for significant changes

class Config:
    DEFAULT_INPUT = {
        "mandatoryKeywords": [],
        "optionalKeywords": [],
        "location": "",
        "workType": "ANY",
        "maxJobs": 100
    }
