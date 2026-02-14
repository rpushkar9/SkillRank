import re
import json
import scrapy
from skills_scraper.items import SkillsScraperItem

class SkillsSpider(scrapy.Spider):
    name = "skills"
    allowed_domains = ["skills.sh"]
    start_urls = [
        "https://skills.sh",
        "https://skills.sh/trending",
        "https://skills.sh/hot",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_skills = set()

    def parse(self, response):
        """
        Parse a leaderboard page (all-time, trending, or hot).
        Each tab has up to 600 skills. We hit all three and deduplicate
        by source/skillId so we never scrape the same detail page twice.
        """
        chunks = re.findall(
            r'self\.__next_f\.push\((\[.*?\])\)</script>', response.text
        )

        skills = []
        for chunk in chunks:
            if "initialSkills" not in chunk:
                continue

            parsed = json.loads(chunk)
            content = parsed[1] if len(parsed) > 1 else ""

            idx = content.find('initialSkills":[')
            if idx < 0:
                continue

            arr_start = content.index("[", idx)
            depth = 0
            for i in range(arr_start, len(content)):
                if content[i] == "[":
                    depth += 1
                elif content[i] == "]":
                    depth -= 1
                if depth == 0:
                    skills = json.loads(content[arr_start : i + 1])
                    break
            break

        self.logger.info(
            f"Found {len(skills)} skills on {response.url} "
            f"({len(self.seen_skills)} unique so far)"
        )

        for skill in skills:
            source = skill.get("source", "")
            skill_id = skill.get("skillId", "")
            key = f"{source}/{skill_id}"

            # Skip duplicates across tabs
            if key in self.seen_skills:
                continue
            self.seen_skills.add(key)

            detail_url = f"https://skills.sh/{source}/{skill_id}"

            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_detail,
                meta={
                    "skill_name": skill.get("name", ""),
                    "total_installs": skill.get("installs", 0),
                    "source": source,
                },
            )

    def parse_detail(self, response):
        """
        Parse a skill detail page. All data is in RSC payload chunks --
        sidebar data (weekly installs, first seen, repo) in one chunk,
        SKILL.md content as escaped HTML in another.
        """
        name = response.meta["skill_name"]
        total_installs = response.meta["total_installs"]
        source = response.meta["source"]

        chunks = re.findall(
            r'self\.__next_f\.push\((\[.*?\])\)</script>', response.text
        )

        weekly_installs = ""
        first_seen = ""
        skill_url = ""
        description = ""
        skill_md_content = ""

        for chunk in chunks:
            parsed = json.loads(chunk)
            content = parsed[1] if len(parsed) > 1 and isinstance(parsed[1], str) else ""

            # Sidebar chunk -- has Weekly Installs, First Seen, repo link
            if "First Seen" in content:
                wi = re.search(r'Weekly Installs.*?"children":"([\d.,]+K?)"', content)
                if wi:
                    weekly_installs = wi.group(1)

                fs = re.search(r'First Seen.*?"children":"([^"]+)"', content)
                if fs:
                    first_seen = fs.group(1)

                repo = re.search(r'"href":"(https://github\.com/[^"]+)"', content)
                if repo:
                    skill_url = repo.group(1)

            # SKILL.md chunk -- after json.loads, unicode escapes are already
            # decoded so \u003cp\u003e becomes <p>. Look for HTML tags directly.
            if "<p>" in content or "<h1>" in content or "<h2>" in content:
                clean = re.sub(r"<[^>]+>", " ", content)
                clean = re.sub(r"\s+", " ", clean).strip()
                if len(clean) > len(skill_md_content):
                    skill_md_content = clean

        # First sentence of SKILL.md as description
        if skill_md_content:
            first_period = skill_md_content.find(". ")
            if first_period > 0:
                description = skill_md_content[: first_period + 1]
            else:
                description = skill_md_content[:200]

        # Fallback skill_url from source
        if not skill_url and source:
            skill_url = f"https://github.com/{source}"

        yield SkillsScraperItem(
            name=name,
            description=description,
            example_usage=skill_md_content,
            weekly_installs=weekly_installs,
            first_seen=first_seen,
            skill_url=skill_url,
            total_installs=str(total_installs),
        )
