# Cranberry Vacancies LinkedIn Jobs Scraper

A powerful LinkedIn job listings scraper built as an Apify actor. This scraper allows you to extract detailed job information based on search criteria while respecting LinkedIn's structure and Apify's free tier limitations.

## Features

- Search jobs using mandatory and optional keywords
- Filter by location and work type (Remote/Hybrid/On-site)
- Extract comprehensive job details:
  - Job title and company
  - Location and work type
  - Posting date
  - Salary information (when available)
  - Complete job description
  - Application URL
- Optimized for Apify's free tier
- Built-in rate limiting and error handling
- Progress tracking and partial results saving

## Input Parameters

The scraper accepts the following input parameters in JSON format:

```json
{
    "searchTerms": {
        "mandatory": ["python", "developer"],
        "optional": ["senior", "lead"]
    },
    "location": "San Francisco, CA",
    "workType": "REMOTE",
    "maxJobs": 100
}
```

### Parameter Details

- `searchTerms` (required):
  - `mandatory`: Array of keywords that must appear in job titles
  - `optional`: Array of keywords where at least one should appear
- `location` (required): Job location to search for
- `workType` (optional):
  - Options: "REMOTE", "HYBRID", "ON_SITE", "ANY"
  - Default: "ANY"
- `maxJobs` (optional):
  - Maximum number of jobs to scrape
  - Default: 100
  - Maximum: 150 (free tier limit)

## Output Format

The scraper outputs data in JSON format:

```json
{
    "jobs": [
        {
            "id": "unique_job_id",
            "title": "Senior Python Developer",
            "company": "Example Corp",
            "location": "San Francisco, CA",
            "work_type": "Remote",
            "posted_date": "2024-02-03T09:00:00",
            "salary": {
                "min": 120000,
                "max": 180000,
                "currency": "USD",
                "period": "yearly"
            },
            "description": "Full job description...",
            "url": "https://linkedin.com/jobs/view/...",
            "scraped_at": "2024-02-03T09:55:00"
        }
    ],
    "metadata": {
        "jobs_scraped": 100,
        "duration_seconds": 180,
        "search_params": {
            // Original input parameters
        }
    }
}
```

## Free Tier Limitations

- Maximum 150 jobs per run
- 30 actor compute units per month
- Shared proxies
- 1GB memory limit
- 1 concurrent run

## Local Development

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

## Deployment to Apify

1. Create an Apify account at [apify.com](https://apify.com)
2. Install Apify CLI:
   ```bash
   npm install -g apify-cli
   ```
3. Login to Apify:
   ```bash
   apify login
   ```
4. Deploy the actor:
   ```bash
   apify push
   ```

## Error Handling

The scraper includes robust error handling:
- Automatic retries for failed requests
- Rate limiting protection
- Memory usage monitoring
- Partial results saving
- Detailed error logging

## Best Practices

1. Start with specific search terms to get relevant results
2. Use mandatory keywords wisely to filter job titles
3. Keep optional keywords broad for better coverage
4. Monitor compute units usage to stay within free tier limits
5. Use smaller maxJobs values for faster results

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this code for any purpose.

## Support

For issues and feature requests, please create an issue in the repository.
