import concurrent.futures as futures
import logging
from datetime import date
from typing import Iterable

import bs4 as bs
import requests as http
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
    def __init__(self):
        self.session = http.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })

    def get_scanner_name(self) -> str:
        return "Official Site Scanner"

    def get_and_parse_page(self, link: str) -> bs.BeautifulSoup:
        log = logging.getLogger(__name__)
        log.debug(f"Getting and parsing page '{link}'...")
        # Use self.session instead of http.get
        response = self.session.get(link)
        response.raise_for_status()
        return bs.BeautifulSoup(response.text, features="html.parser")

    def get_articles(self) -> Iterable[ArticleInfo]:
        log = logging.getLogger(__name__)
        log.debug("Getting articles...")

        page = self.get_and_parse_page(ANNOUNCEMENTS_URL)

        updates_list = page.find("ul", attrs={"class": "thumb_nail_list"})
        if not updates_list:
            raise Exception("Could not find updates list!")

        children = updates_list.children
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
            yield ArticleInfo(article_link, date)

    # Check a single event article for codes
    def check_article(self, article_info: ArticleInfo) -> Iterable[Coupon]:
        log = logging.getLogger(__name__)
        log.debug(f"Scanning arcticle: {article_info.article_link}")

        page = self.get_and_parse_page(article_info.article_link)

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

    # Scans the "all currently available coupons" article, that gets updated more or less daily.
    def check_coupon_list_article(self) -> Iterable[Coupon]:
        ARTICLE_URL = "https://www.naeu.playblackdesert.com/en-US/News/Detail?groupContentNo=5676&countryType=en-US"

        page = self.get_and_parse_page(ARTICLE_URL)

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

    def get_codes(self) -> Iterable[Coupon]:
        try:
            log = logging.getLogger(__name__)
            log.debug("Scanning for site codes...")

            seen_codes = set()
            unique_coupons = []

            try:
                main_list_coupons = self.check_coupon_list_article()
                for coupon in main_list_coupons:
                    if coupon.code not in seen_codes:
                        seen_codes.add(coupon.code)
                        unique_coupons.append(coupon)
            except Exception as e:
                log.error(f"Failed to parse main coupon list: {e}")

            articles = self.get_articles()
            with futures.ThreadPoolExecutor() as executor:
                # Submit all tasks immediately
                future_to_article = {
                    executor.submit(self.check_article, article): article
                    for article in articles
                }

                # Process them as they finish (out of order)
                for future in futures.as_completed(future_to_article):
                    try:
                        coupons = future.result()
                        for coupon in coupons:
                            if coupon.code not in seen_codes:
                                seen_codes.add(coupon.code)
                                unique_coupons.append(coupon)
                    except Exception as e:
                        log.error(f"Failed to parse article: {e}")

            return unique_coupons
        except TimeoutError:
            raise ScannerTimeoutError
        except Exception:
            raise ScannerError
