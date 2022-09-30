from typing import Iterable
from datetime import date
from checker import CODE_REGEX, CodeChecker
import requests as http
import bs4 as bs
from multiprocessing.pool import ThreadPool


class OfficialSiteCode:
    def __init__(self, article_link: str, date: date, code: str):
        self.article_link = article_link
        self.date = date
        self.code = code
        pass

    def __str__(self) -> str:
        return f"{self.code} [{self.date} | {self.article_link}]"


class ArticleInfo:
    def __init__(self, article_link: str, date: date):
        self.article_link = article_link
        self.date = date


class OfficialSiteChecker(CodeChecker):
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

    def parse_date(self, date_str: str) -> date:
        month_str = date_str[0:3]
        day_str = date_str[4:6]
        year_str = date_str[8:12]
        month = [
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
        ].index(month_str) + 1
        day = int(day_str)
        year = int(year_str)
        return date(year, month, day)

    def get_articles(self) -> Iterable[ArticleInfo]:
        html_updates = self.get_articles_list()
        for up in html_updates:
            container: bs.PageElement = up.a
            url = container["href"]
            date_str = container.find_next("span", attrs={"class": "date"})
            date = self.parse_date(date_str.text)
            yield ArticleInfo(url, date)

    # Check a single event article for code
    def check_article(self, article_info: ArticleInfo) -> Iterable[OfficialSiteCode]:
        response = http.get(article_info.article_link)
        response.raise_for_status()
        page = bs.BeautifulSoup(response.text, features="html.parser")
        content_area = page.find("div", attrs={"class": "contents_area editor_area"})
        span_text = content_area.get_text()

        def parse_code_text(text):
            for code in CODE_REGEX.finditer(text):
                yield OfficialSiteCode(
                    article_info.article_link, article_info.date, code.group()
                )

        return parse_code_text(span_text)

    def get_codes(self) -> Iterable[OfficialSiteCode]:
        articles = list(self.get_articles())
        code_list = set()
        with ThreadPool(len(articles)) as p:
            for x in p.map(self.check_article, articles):
                code_list.update(x)
        ordered_code_list = list(code_list)
        ordered_code_list.sort(key=lambda x: x.date, reverse=True)
        return ordered_code_list
