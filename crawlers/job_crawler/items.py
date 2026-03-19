import scrapy


class RawJobItem(scrapy.Item):
    source = scrapy.Field()
    external_id = scrapy.Field()
    title = scrapy.Field()
    company_name = scrapy.Field()
    description_raw = scrapy.Field()
    source_url = scrapy.Field()
    apply_url = scrapy.Field()
    location = scrapy.Field()
    remote_policy = scrapy.Field()
    salary_raw = scrapy.Field()
    posted_at = scrapy.Field()
    metadata = scrapy.Field()


class CompanySignalItem(scrapy.Item):
    company_name = scrapy.Field()
    signal_type = scrapy.Field()
    headline = scrapy.Field()
    description = scrapy.Field()
    url = scrapy.Field()
    source = scrapy.Field()
    published_at = scrapy.Field()
