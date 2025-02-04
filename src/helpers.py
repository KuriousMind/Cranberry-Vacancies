"""Helper functions for the LinkedIn Jobs Scraper."""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import re

def build_search_url(
    keywords: Dict[str, List[str]],
    location: str,
    work_type: Optional[str] = None
) -> str:
    """Build LinkedIn search URL from parameters."""
    from .config import LINKEDIN_URLS, WORK_TYPES
    
    # Combine mandatory and optional keywords
    search_query = " ".join(keywords.get("mandatory", []))
    if keywords.get("optional"):
        search_query += " " + " ".join(f"OR {kw}" for kw in keywords["optional"])
    
    params = {
        "keywords": search_query,
        "location": location,
        "f_WT": WORK_TYPES.get(work_type) if work_type != "ANY" else None,
        "position": 1,
        "pageNum": 0
    }
    
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    
    # Build query string
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{LINKEDIN_URLS['jobs']}?{query_string}"

def parse_date(date_str: str) -> str:
    """Convert LinkedIn date format to ISO format."""
    now = datetime.now()
    
    if "just now" in date_str.lower() or "now" in date_str.lower():
        return now.isoformat()
    
    # Handle "1h ago", "2d ago", etc.
    time_match = re.match(r"(\d+)\s*([hdwmy])", date_str.lower())
    if time_match:
        amount, unit = time_match.groups()
        amount = int(amount)
        
        if unit == 'h':
            delta = timedelta(hours=amount)
        elif unit == 'd':
            delta = timedelta(days=amount)
        elif unit == 'w':
            delta = timedelta(weeks=amount)
        elif unit == 'm':
            delta = timedelta(days=amount * 30)  # Approximate
        elif unit == 'y':
            delta = timedelta(days=amount * 365)  # Approximate
            
        return (now - delta).isoformat()
    
    # Try to parse as standard date format
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").isoformat()
    except ValueError:
        return date_str

def extract_salary(salary_text: str) -> Dict[str, Union[float, str, None]]:
    """Improved salary parsing with better range handling."""
    salary_info = {
        "min": None,
        "max": None,
        "currency": None,
        "period": None
    }
    
    if not salary_text:
        return salary_info
    
    # Normalize text
    text = salary_text.lower().replace(',', '').replace('~', '-')
    
    # Currency detection
    currency_map = {'$': 'USD', '£': 'GBP', '€': 'EUR', '₹': 'INR', '¥': 'JPY'}
    salary_info['currency'] = next(
        (v for k, v in currency_map.items() if k in text),
        None
    )
    
    # Extract numerical values
    numbers = re.findall(r'\d+\.?\d*[k]?', text)
    numbers = [float(n.replace('k', '')) * 1000 if 'k' in n else float(n) for n in numbers]
    
    if numbers:
        if 'up to' in text:
            salary_info['max'] = max(numbers)
        elif 'from' in text:
            salary_info['min'] = min(numbers)
        else:
            salary_info['min'] = min(numbers)
            salary_info['max'] = max(numbers) if len(numbers) > 1 else None
    
    # Period detection
    period_map = {
        'year': 'yearly', 'yr': 'yearly', 'annual': 'yearly',
        'month': 'monthly', 'mo': 'monthly',
        'week': 'weekly', 'wk': 'weekly',
        'hour': 'hourly', 'hr': 'hourly'
    }
    salary_info['period'] = next(
        (v for k, v in period_map.items() if k in text),
        None
    )
    
    return salary_info

def format_job_data(
    job_data: Dict,
    search_params: Dict
) -> Dict:
    """Format job data for storage."""
    return {
        "id": job_data.get("id"),
        "title": job_data.get("title"),
        "company": job_data.get("company"),
        "location": job_data.get("location"),
        "work_type": job_data.get("work_type"),
        "posted_date": parse_date(job_data.get("posted_date", "")),
        "salary": extract_salary(job_data.get("salary", "")),
        "description": job_data.get("description"),
        "url": job_data.get("url"),
        "scraped_at": datetime.now().isoformat(),
        "search_params": search_params
    }
