# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SkillsScraperItem(scrapy.Item):
    name = scrapy.Field()
    description = scrapy.Field()
    example_usage = scrapy.Field()
    weekly_installs = scrapy.Field()
    first_seen = scrapy.Field()
    skill_url = scrapy.Field()
    total_installs = scrapy.Field()
