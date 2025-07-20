from typing import Iterable
from datetime import date
import logging
import requests as http
import bs4 as bs
import concurrent.futures as futures
import itertools
from .scanner_error import ScannerTimeoutError, ScannerError
from .scanner_base import CODE_REGEX, CouponScannerBase
from ..coupon import Coupon


ANNOUNCEMENTS_URL = "https://www.naeu.playblackdesert.com/en-US/News/Notice"


class ArticleInfo:
    def __init__(self, article_link: str, date: date):
        self.article_link = article_link
        self.date = date


class OfficialSiteScanner(CouponScannerBase):
    def get_scanner_name(self) -> str:
        return "Official Site Scanner"

    def get_and_parse_page(self, link: str) -> bs.BeautifulSoup:
        log = logging.getLogger(__name__)
        log.debug(f"Getting and parsing page '{link}'...")
        response = http.get(link)
        response.raise_for_status()
        return bs.BeautifulSoup(response.text, features="html.parser")

    def get_articles(self) -> Iterable[ArticleInfo]:
        log = logging.getLogger(__name__)
        log.debug("Getting articles...")

        page = self.get_and_parse_page(ANNOUNCEMENTS_URL)

        updates_list = page.find("ul", attrs={"class": "thumb_nail_list"})
        if not updates_list:
            raise Exception("Could not find updates list!")

        children = updates_list.children  # type: ignore
        for list_element in children:
            if list_element == "\n":
                continue

            article_a = list_element.find("a")  # type: ignore
            if not article_a:
                raise Exception("Could not find article link!")
            article_link = article_a["href"]  # type: ignore

            date_str = article_a.find_next("span", attrs={"class": "date"}).text
            date = self.parse_date(date_str)
            yield ArticleInfo(article_link, date)

    def parse_date(self, date_str: str) -> date:
        month_str = date_str[0:3]
        day_str_offset = 0
        if date_str[5] == ",":  # If day string is only 1 char
            day_str_offset = 1

        day_str = date_str[4 : 6 - day_str_offset]
        year_str = date_str[8 - day_str_offset : 12 - day_str_offset]

        MONTHS = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        month = MONTHS.index(month_str) + 1
        day = int(day_str)
        year = int(year_str)
        return date(year, month, day)

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

    def get_codes(self) -> Iterable[Coupon]:
        try:
            log = logging.getLogger(__name__)
            log.debug("Scanning for site codes...")
            articles = self.get_articles()
            coupon_chain = []
            with futures.ThreadPoolExecutor() as executor:
                for coupons in executor.map(self.check_article, articles):
                    coupon_chain = itertools.chain(coupon_chain, coupons)
            return coupon_chain
        except TimeoutError:
            raise ScannerTimeoutError
        except Exception:
            raise ScannerError
