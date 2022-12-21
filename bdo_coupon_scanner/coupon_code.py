from datetime import date


class CouponCode:
    def __init__(self, code: str, date: date, origin_link: str):
        self.code = code
        self.date = date
        self.article_link = origin_link
        pass

    def __str__(self) -> str:
        return f"{self.code} [{self.date} | {self.article_link}]"
