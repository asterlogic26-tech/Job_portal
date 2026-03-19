import json
import scrapy

from job_crawler.items import RawJobItem
from job_crawler.spiders.base_spider import BaseJobSpider


class RemoteOKAPISpider(BaseJobSpider):
    """RemoteOK.com public API spider."""

    name = "remoteok_api"
    source_id = "remoteok_api"
    source_name = "RemoteOK"
    allowed_domains = ["remoteok.com"]
    start_urls = ["https://remoteok.com/api"]

    custom_settings = {
        **BaseJobSpider.custom_settings,
        "ROBOTSTXT_OBEY": False,  # remoteok.com specifically provides an API
    }

    def start_requests(self):
        yield scrapy.Request(
            url="https://remoteok.com/api",
            headers={"User-Agent": "PersonalJobAgent/1.0"},
            callback=self.parse,
        )

    def parse(self, response):
        try:
            data = json.loads(response.text)
            for job in data[1:]:  # First item is metadata
                if not isinstance(job, dict) or not job.get("position"):
                    continue

                item = RawJobItem(
                    source=self.source_id,
                    external_id=str(job.get("id", "")),
                    title=job.get("position", ""),
                    company_name=job.get("company", ""),
                    description_raw=job.get("description", ""),
                    source_url=job.get("url", ""),
                    apply_url=job.get("apply_url") or job.get("url", ""),
                    location="Remote",
                    remote_policy="remote",
                    salary_raw=None,
                    posted_at=None,
                    metadata={"tags": job.get("tags", [])},
                )
                self.jobs_discovered += 1
                yield item
        except Exception as e:
            self.logger.error(f"RemoteOK parse error: {e}")
