import asyncio
import logging
from datetime import date
from typing import Iterable, List

import aiohttp
import bs4 as bs
from dateutil import parser as date_parser

from bdo_coupon_scanner.coupon import Coupon

from .scanner_base import CODE_REGEX, CouponScannerBase
from .scanner_error import ScannerError, ScannerTimeoutError

ANNOUNCEMENTS_URL = "https://www.naeu.playblackdesert.com/en-US/News/Notice"


class ArticleInfo:
    def __init__(self, article_link: str, date: date):
        self.article_link = article_link
        self.date = date


class OfficialSiteScanner(CouponScannerBase):
    def get_scanner_name(self) -> str:
        return "Official Site Scanner"

    async def get_and_parse_page(self, session: aiohttp.ClientSession, link: str) -> bs.BeautifulSoup:
        log = logging.getLogger(__name__)
        log.debug(f"Getting and parsing page '{link}'...")
        async with session.get(link) as response:
            response.raise_for_status()
            text = await response.text()
            return bs.BeautifulSoup(text, features="html.parser")

    async def get_articles(self, session: aiohttp.ClientSession) -> Iterable[ArticleInfo]:
        log = logging.getLogger(__name__)
        log.debug("Getting articles...")

        page = await self.get_and_parse_page(session, ANNOUNCEMENTS_URL)

        updates_list = page.find("ul", attrs={"class": "thumb_nail_list"})
        if not updates_list:
            raise Exception("Could not find updates list!")

        children = updates_list.children
        articles = []
        for list_element in children:
            if list_element == "\n":
                continue

            article_a = list_element.find_next("a")
            if not article_a:
                raise Exception("Could not find article link!")
            article_link = str(article_a["href"])

            date_str = article_a.find_next("span", attrs={"class": "date"}).text  # pyright: ignore[reportOptionalMemberAccess]
            # dateutil sometimes fails on "(UTC)" without a time, or the parentheses.
            # We strip it out to be safe.
            clean_date_str = date_str.replace("(UTC)", "").strip()
            date = date_parser.parse(clean_date_str).date()
            articles.append(ArticleInfo(article_link, date))
        return articles

    # Check a single event article for codes
    async def check_article(self, session: aiohttp.ClientSession, article_info: ArticleInfo) -> List[Coupon]:
        log = logging.getLogger(__name__)
        log.debug(f"Scanning arcticle: {article_info.article_link}")

        try:
            page = await self.get_and_parse_page(session, article_info.article_link)

            # Find the main content area
            content_area = page.find("div", attrs={"class": "contents_area"})
            if not content_area:
                log.warning(
                    f"Could not find content area in article: {article_info.article_link}"
                )
                return []
            section_text = content_area.get_text()

            codes = []
            for code in CODE_REGEX.finditer(section_text):
                codes.append(
                    Coupon(code.group(), article_info.date, article_info.article_link)
                )
            return codes
        except Exception as e:
            log.error(f"Failed to parse article {article_info.article_link}: {e}")
            return []

    # Scans the "all currently available coupons" article, that gets updated more or less daily.
    async def check_coupon_list_article(self, session: aiohttp.ClientSession) -> List[Coupon]:
        ARTICLE_URL = "https://www.naeu.playblackdesert.com/en-US/News/Detail?groupContentNo=5676&countryType=en-US"

        page = await self.get_and_parse_page(session, ARTICLE_URL)

        article_date_str = page.find("span", attrs={"class": "date"}).text # pyright: ignore[reportOptionalMemberAccess]

        clean_date_str = article_date_str.replace("(UTC)", "").strip()
        article_date = date_parser.parse(clean_date_str).date()

        coupon_elements = page.find_all("span", attrs={"class": "js-couponNumber"})

        codes = []
        for element in coupon_elements:
            codes.append(
                Coupon(element.text.strip(), article_date, ARTICLE_URL)
            )
        return codes

    async def get_codes(self) -> Iterable[Coupon]:
        log = logging.getLogger(__name__)
        log.debug("Scanning for site codes...")

        try:
            seen_codes = set()
            unique_coupons = []

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            async with aiohttp.ClientSession(headers=headers) as session:
                try:
                    main_list_coupons = await self.check_coupon_list_article(session)
                    for coupon in main_list_coupons:
                        if coupon.code not in seen_codes:
                            seen_codes.add(coupon.code)
                            unique_coupons.append(coupon)
                except Exception as e:
                    log.error(f"Failed to parse main coupon list: {e}")

                try:
                    articles = await self.get_articles(session)

                    tasks = [self.check_article(session, article) for article in articles]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    for result in results:
                        if isinstance(result, BaseException):
                            log.error(f"Error in article task: {result}")
                            continue

                        for coupon in result:
                            if coupon.code not in seen_codes:
                                seen_codes.add(coupon.code)
                                unique_coupons.append(coupon)

                except Exception as e:
                    log.error(f"Failed to fetch/process articles: {e}")

            return unique_coupons
        except asyncio.TimeoutError:
            raise ScannerTimeoutError
        except Exception as e:
            log.error(f"Site scanner fatal error: {e}")
            raise ScannerError
