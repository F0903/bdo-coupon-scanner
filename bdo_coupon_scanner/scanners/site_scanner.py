from typing import Iterable
from datetime import date
import logging
import requests as http
from queue import Queue
import bs4 as bs
import concurrent.futures as futures
import itertools
from .scanner_base import CODE_REGEX, CouponScannerBase
from ..coupon import Coupon


BASE_URL = "https://www.naeu.playblackdesert.com/en-US/News/Notice"


class ArticleInfo:
    def __init__(self, article_link: str, date: date):
        self.article_link = article_link
        self.date = date


class OfficialSiteScanner(CouponScannerBase):
    def get_scanner_name(self) -> str:
        return "Official Site Scanner"

    def get_page(self, link: str) -> bs.BeautifulSoup:
        log = logging.getLogger(__name__)
        log.debug("Getting site articles webpage...")
        response = http.get(link)
        response.raise_for_status()
        return bs.BeautifulSoup(response.text, features="html.parser")

    def get_articles_list(self) -> Iterable[bs.PageElement]:
        log = logging.getLogger(__name__)
        log.debug("Getting articles container...")
        page = self.get_page(BASE_URL)
        updates_list = page.find("ul", attrs={"class": "thumb_nail_list"})
        if not updates_list:
            raise Exception("Could not find updates list!")
        for x in updates_list.children:
            if x == "\n":
                continue
            yield x

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

    def get_articles(self) -> Iterable[ArticleInfo]:
        log = logging.getLogger(__name__)
        log.debug("Getting all articles...")
        html_updates = self.get_articles_list()
        for up in html_updates:
            container: bs.PageElement = up.a
            url = container["href"]
            date_str = container.find_next("span", attrs={"class": "date"}).text
            date = self.parse_date(date_str)
            yield ArticleInfo(url, date)

    # Check a single event article for code
    def check_article(self, article_info: ArticleInfo) -> Iterable[Coupon]:
        log = logging.getLogger(__name__)
        log.debug(f"Scanning arcticle: {article_info.article_link}")
        response = http.get(article_info.article_link)
        response.raise_for_status()
        page = bs.BeautifulSoup(response.text, features="html.parser")
        content_area = page.find("div", attrs={"class": "contents_area"})
        section_text = content_area.get_text()

        coupon_queue = Queue()
        with futures.ThreadPoolExecutor() as executor:
            for coupon in executor.map(
                lambda code: Coupon(
                    code.group(), article_info.date, article_info.article_link
                ),
                CODE_REGEX.finditer(section_text),
            ):
                coupon_queue.put(coupon)

        coupon_queue.join()
        return coupon_queue.queue

    def get_codes(self) -> Iterable[Coupon]:
        log = logging.getLogger(__name__)
        log.debug("Scanning for site codes...")

        articles = self.get_articles()

        coupon_chain = []
        with futures.ThreadPoolExecutor() as executor:
            for coupons in executor.map(self.check_article, articles):
                coupon_chain = itertools.chain(coupon_chain, coupons)
        return coupon_chain
