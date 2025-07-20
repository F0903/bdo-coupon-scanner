from datetime import date


def ensure_coupon_format(coupon_code: str) -> str:
    result = []
    char_pos = 0

    for i, char in enumerate(coupon_code):
        if char == "-":
            continue

        is_dash_position = (i != 0) and (char_pos % 4 == 0)
        if is_dash_position:
            result.append("-")

        result.append(char)
        char_pos += 1

    return "".join(result)


class Coupon:
    def __init__(self, code: str, date: date, origin_link: str):
        self.code = ensure_coupon_format(code)
        self.date = date
        self.origin_link = origin_link

    def __str__(self) -> str:
        return f"{self.code} [{self.date} | {self.origin_link}]"
