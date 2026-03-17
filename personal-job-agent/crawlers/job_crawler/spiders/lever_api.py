import json
import scrapy
from crawlers.job_crawler.spiders.base_spider import BaseJobSpider
from crawlers.job_crawler.items import RawJobItem


class LeverApiSpider(BaseJobSpider):
    """
    Polls Lever public API for configured companies.
    Returns open job postings without authentication.
    """
    name = "lever_api"
    custom_settings = {
        "DOWNLOAD_DELAY": 1.5,
        "AUTOTHROTTLE_ENABLED": True,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        import yaml
        import os

        config_path = os.path.join(
            os.path.dirname(__file__), "../../../../config/sources.yml"
        )
        with open(config_path) as f:
            config = yaml.safe_load(f)

        self.companies = (
            config.get("sources", {})
            .get("ats_apis", {})
            .get("providers", {})
            .get("lever", {})
            .get("companies", [])
        )

    def start_requests(self):
        base = "https://api.lever.co/v0/postings"
        for company in self.companies:
            url = f"{base}/{company}?mode=json"
            yield scrapy.Request(url, callback=self.parse_company, cb_kwargs={"company": company})

    def parse_company(self, response, company: str):
        if response.status != 200:
            return

        try:
            jobs = json.loads(response.text)
        except json.JSONDecodeError:
            return

        if not isinstance(jobs, list):
            return

        self.log_discovery(len(jobs), f"lever/{company}")

        for job in jobs:
            categories = job.get("categories", {})
            location = categories.get("location", "")
            team = categories.get("team", "")
            commitment = categories.get("commitment", "")  # Full-time, Part-time, etc.

            item = RawJobItem(
                external_id=f"lever_{company}_{job['id']}",
                source="lever",
                title=job.get("text", ""),
                company_name=company.replace("-", " ").title(),
                location=location,
                url=job.get("hostedUrl", ""),
                apply_url=job.get("applyUrl", ""),
                description=job.get("descriptionPlain", ""),
                description_html=job.get("description", ""),
                posted_at=str(job.get("createdAt", "")),
                raw_data={
                    **job,
                    "team": team,
                    "commitment": commitment,
                },
            )
            yield item
