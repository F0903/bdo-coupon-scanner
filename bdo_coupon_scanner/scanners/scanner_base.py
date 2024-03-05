from typing import Iterable
import re

CODE_REGEX = re.compile(r"((\w|\d){4})-((\w|\d){4})-((\w|\d){4})-((\w|\d){4})")


class CouponScannerBase:
    def get_scanner_name(self) -> str:
        raise NotImplementedError()

    def get_codes(self) -> Iterable[str]:
        raise NotImplementedError()
