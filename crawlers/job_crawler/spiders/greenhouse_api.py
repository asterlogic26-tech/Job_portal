import json
import scrapy
from crawlers.job_crawler.spiders.base_spider import BaseJobSpider
from crawlers.job_crawler.items import RawJobItem


class GreenhouseApiSpider(BaseJobSpider):
    """
    Polls Greenhouse public board API for configured company boards.
    No authentication required — public job listings only.
    """
    name = "greenhouse_api"
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

        self.boards = (
            config.get("sources", {})
            .get("ats_apis", {})
            .get("providers", {})
            .get("greenhouse", {})
            .get("boards", [])
        )

    def start_requests(self):
        base = "https://boards-api.greenhouse.io/v1/boards"
        for board in self.boards:
            url = f"{base}/{board}/jobs?content=true"
            yield scrapy.Request(url, callback=self.parse_board, cb_kwargs={"board": board})

    def parse_board(self, response, board: str):
        if response.status != 200:
            return

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            return

        jobs = data.get("jobs", [])
        self.log_discovery(len(jobs), f"greenhouse/{board}")

        for job in jobs:
            meta = job.get("metadata", [])
            location = job.get("location", {}).get("name", "")

            item = RawJobItem(
                external_id=f"greenhouse_{board}_{job['id']}",
                source="greenhouse",
                title=job.get("title", ""),
                company_name=board.replace("-", " ").title(),
                location=location,
                url=job.get("absolute_url", ""),
                description=job.get("content", ""),
                description_html=job.get("content", ""),
                posted_at=job.get("updated_at", ""),
                raw_data=job,
            )
            yield item
