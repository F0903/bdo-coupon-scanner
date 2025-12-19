from datetime import date


def _ensure_coupon_format(coupon_code: str) -> str:
    return coupon_code.replace("-", "")


class Coupon:
    def __init__(self, code: str, date: date, origin_link: str):
        self.code = _ensure_coupon_format(code)
        self.date = date
        self.origin_link = origin_link

    def __str__(self) -> str:
        return f"{self.code} [{self.date} | {self.origin_link}]"
