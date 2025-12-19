import re
from typing import Iterable

from bdo_coupon_scanner.coupon import Coupon

CODE_REGEX = re.compile(r"((\w|\d){4})-((\w|\d){4})-((\w|\d){4})-((\w|\d){4})")


class CouponScannerBase:
    def get_scanner_name(self) -> str:
        raise NotImplementedError()

    async def get_codes(self) -> Iterable[Coupon]:
        raise NotImplementedError()
