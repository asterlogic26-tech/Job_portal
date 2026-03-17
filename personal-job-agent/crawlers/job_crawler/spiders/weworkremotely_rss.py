import feedparser
import scrapy
from datetime import datetime

from job_crawler.items import RawJobItem
from job_crawler.spiders.base_spider import BaseJobSpider

RSS_URLS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
]


class WeWorkRemotelySpider(BaseJobSpider):
    name = "weworkremotely_rss"
    source_id = "weworkremotely_rss"
    source_name = "We Work Remotely"

    def start_requests(self):
        for url in RSS_URLS:
            yield scrapy.Request(
                url=url,
                headers={"User-Agent": "PersonalJobAgent/1.0"},
                callback=self.parse_feed,
                meta={"feed_url": url},
            )

    def parse_feed(self, response):
        feed = feedparser.parse(response.text)
        for entry in feed.entries:
            title = entry.get("title", "")
            # WWR titles format: "Company: Job Title"
            parts = title.split(":", 1)
            company = parts[0].strip() if len(parts) > 1 else ""
            job_title = parts[1].strip() if len(parts) > 1 else title

            item = RawJobItem(
                source=self.source_id,
                external_id=entry.get("id", ""),
                title=job_title,
                company_name=company,
                description_raw=entry.get("summary", ""),
                source_url=entry.get("link", ""),
                apply_url=entry.get("link", ""),
                location="Remote",
                remote_policy="remote",
                salary_raw=None,
                posted_at=entry.get("published", None),
                metadata={},
            )
            self.jobs_discovered += 1
            yield item
