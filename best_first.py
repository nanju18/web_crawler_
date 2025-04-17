from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
from playwright.async_api import async_playwright
from log_manager import LoggerUtility
from typing import Optional, List

logger = LoggerUtility().get_logger()

class BestFirstCrawl:
    def __init__(self):
        pass

    async def fetch_rendered_html(self, url: str) -> str:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                await page.goto(url, wait_until="commit")
                await page.wait_for_timeout(120)
                html = await page.content()
                await browser.close()
                return html
        except Exception:
            logger.exception(f"Unexpected error while rendering {url}")
            raise

    def create_prune_filter(self):
        return PruningContentFilter(
            threshold=0.7,
            threshold_type="dynamic"
        )

    def create_markdown_generator(self, prune_filter=None):
        return DefaultMarkdownGenerator(
            content_filter=prune_filter or self.create_prune_filter(),
            options={"ignore_links": True}
        )

    def create_common_config(self, md_generator: DefaultMarkdownGenerator):
        return {
            "markdown_generator": md_generator,
            "scraping_strategy": LXMLWebScrapingStrategy(),
            "cache_mode": CacheMode.BYPASS,
        }

    async def crawl_single_page(self, url: str):
        rendered_html = await self.fetch_rendered_html(url)
        md_generator = self.create_markdown_generator()
        config = CrawlerRunConfig(**self.create_common_config(md_generator))

        async with AsyncWebCrawler() as crawler:
            results = await crawler.arun(url, config=config, initial_html=rendered_html)
            return [{
                "url": results.url,
                "fit_markdown": results.markdown.fit_markdown if results.markdown else None
            }]

    async def best_first_crawl(self, url: str, depth: int, keywords: Optional[List[str]] = None):
        try:
            rendered_html = await self.fetch_rendered_html(url)

            md_generator = self.create_markdown_generator()
            config_dict = self.create_common_config(md_generator)

            scorer = KeywordRelevanceScorer(
                keywords=keywords,
                weight=0.7
            )

            config_dict["deep_crawl_strategy"] = BestFirstCrawlingStrategy(
                max_depth=depth,
                include_external=False,
                url_scorer=scorer,
                #max_pages={1: 5, 2: 200}.get(depth, 500),
            )

            config = CrawlerRunConfig(**config_dict)

            async with AsyncWebCrawler() as crawler:
                results = await crawler.arun(url=url, config=config, initial_html=rendered_html)

                return [{
                    "url": result.url,
                    "depth": result.metadata.get("depth", 0),
                    "score": scorer.score(result.url),
                    "fit_markdown": result.markdown.fit_markdown if result.markdown else None
                } for result in results]

        except Exception:
            logger.exception(f"Error during best-first crawl of {url}")
            raise RuntimeError(f"Crawling failed for {url}")
