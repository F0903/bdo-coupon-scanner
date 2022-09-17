from checker import CODE_REGEX, EventChecker
import requests as http
import bs4 as bs
from multiprocessing.pool import ThreadPool


class CodeCheckResponse:
    def __init__(self, status: bool, codes: list[str]):
        self.status = status
        self.codes = codes


class SiteEvent:
    def __init__(self, page_url, days_left) -> None:
        self.__page_url = page_url
        self.__days_left = days_left

    def get_url(self) -> str:
        return self.__page_url

    def get_days_left(self) -> int:
        return self.__days_left


class SiteEventChecker(EventChecker):
    def get_checker_name(self) -> str:
        return "official site"

    def get_events_list(self):
        response = http.get(
            "https://www.naeu.playblackdesert.com/en-US/News/Notice?boardType=3"
        )
        response.raise_for_status()
        page = bs.BeautifulSoup(response.text, features="html.parser")
        events_container = page.find("div", attrs={"class": "event_list"})
        if not events_container:
            raise Exception("Could not find events container!")
        events_list = events_container.find("ul")
        return [x for x in events_list.children if x != "\n"]

    def get_events(self) -> list[SiteEvent]:
        html_events = self.get_events_list()
        events = []
        for ev in html_events:
            url = ev.a["href"]
            text: str = ev.a.div.span.em.get_text()
            if text.find("Ongoing") != -1:
                days_left = 999
            else:
                days_left = int(text)
            events.append(SiteEvent(url, days_left))
        return events

    def check_event(self, event: SiteEvent) -> CodeCheckResponse:
        url = event.get_url()
        response = http.get(url)
        response.raise_for_status()
        page = bs.BeautifulSoup(response.text, features="html.parser")
        content_area = page.find("div", attrs={"class": "contents_area editor_area"})
        span_texts = map(lambda x: x.get_text(), content_area.find_all("span"))
        codes = []
        for text in span_texts:
            result = CODE_REGEX.search(text)
            if result is None:
                continue
            codes.append(result.group())
        return CodeCheckResponse(len(codes) > 0, codes)

    def get_codes(self) -> list[str]:
        events = self.get_events()
        code_list = []
        with ThreadPool(len(events)) as p:
            for x in p.map(self.check_event, events):
                if not x.status:
                    continue
                code_list.extend(x.codes)
        return code_list
