from datetime import date


class CouponCode:
    def __init__(self, origin_link: str, date: date, code: str):
        self.article_link = origin_link
        self.date = date
        self.code = code
        pass

    def __str__(self) -> str:
        return f"{self.code} [{self.date} | {self.article_link}]"
