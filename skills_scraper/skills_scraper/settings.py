BOT_NAME = "skills_scraper"

SPIDER_MODULES = ["skills_scraper.spiders"]
NEWSPIDER_MODULE = "skills_scraper.spiders"

USER_AGENT = "SkillRankBot/1.0 (university research project)"

ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 0.5
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# Output -- one JSON object per line
FEEDS = {
    "data/skills_raw.jsonl": {
        "format": "jsonlines",
        "encoding": "utf-8",
        "overwrite": True,
    }
}

FEED_EXPORT_ENCODING = "utf-8"
LOG_LEVEL = "INFO"
