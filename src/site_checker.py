from turtle import update
from typing import Iterable
from checker import CODE_REGEX, EventChecker
import requests as http
import bs4 as bs
from multiprocessing.pool import ThreadPool


class SiteEventChecker(EventChecker):
    def get_checker_name(self) -> str:
        return "official site"

    def get_page(self, link: str) -> bs.BeautifulSoup:
        response = http.get(link)
        response.raise_for_status()
        return bs.BeautifulSoup(response.text, features="html.parser")

    def get_articles_list(self) -> Iterable[bs.PageElement]:
        page = self.get_page("https://www.naeu.playblackdesert.com/en-US/News/Notice")
        updates_list = page.find("ul", attrs={"class": "thumb_nail_list"})
        if not updates_list:
            raise Exception("Could not find updates list!")
        for x in updates_list.children:
            if x == "\n":
                continue
            yield x

    def get_articles(self) -> Iterable[str]:
        html_updates = self.get_articles_list()
        for up in html_updates:
            url = up.a["href"]
            yield url

    # Check a single event article for code
    def check_article(self, event_url: str) -> Iterable[str]:
        response = http.get(event_url)
        response.raise_for_status()
        page = bs.BeautifulSoup(response.text, features="html.parser")
        content_area = page.find("div", attrs={"class": "contents_area editor_area"})
        span_text = content_area.get_text()

        def parse_code_text(text):
            for code in CODE_REGEX.finditer(text):
                yield code.group()

        return parse_code_text(span_text)

    def get_codes(self) -> Iterable[str]:
        articles = list(self.get_articles())
        code_list = set()
        with ThreadPool(len(articles)) as p:
            for x in p.map(self.check_article, articles):
                code_list.update(x)
        return code_list
