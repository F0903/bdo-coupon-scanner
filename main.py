from multiprocessing.pool import ThreadPool
import requests as http
import bs4 as bs
import re
import time

CODE_REGEX = re.compile(r"((\w|\d){4})-((\w|\d){4})-((\w|\d){4})-((\w|\d){4})")


class Event:
    def __init__(self, page_url, days_left) -> None:
        self.__page_url = page_url
        self.__days_left = days_left

    def get_url(self) -> str:
        return self.__page_url

    def get_days_left(self) -> int:
        return self.__days_left


def get_events_list():
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


def get_events() -> list[Event]:
    html_events = get_events_list()
    events = []
    for ev in html_events:
        url = ev.a["href"]
        text: str = ev.a.div.span.em.get_text()
        if text.find("Ongoing") != -1:
            days_left = 999
        else:
            days_left = int(text)
        events.append(Event(url, days_left))
    return events


class CodeCheckResponse:
    def __init__(self, status: bool, codes: list[str]) -> None:
        self.status = status
        self.codes = codes


def check_event(event: Event) -> CodeCheckResponse:
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


def get_codes() -> list[str]:
    events = get_events()
    code_list = []
    with ThreadPool(len(events)) as p:
        for x in p.map(check_event, events):
            if not x.status:
                continue
            code_list.extend(x.codes)
    return code_list


def main():
    start = time.perf_counter_ns()
    print("Searching for codes...")
    try:
        codes = get_codes()
        end = time.perf_counter_ns()
        total = (end - start) / 1000000
        if codes is None:
            print("No codes were found.")
        else:
            print(f"Found codes:")
            for x in codes:
                print(x)
            print(f"Time elapsed: {total}ms")
    except Exception as e:
        print(f"Error encountered!:\n{e}")

    input("Press any key to exit...")


if __name__ == "__main__":
    main()
