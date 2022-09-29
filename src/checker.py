import re
from typing import Iterable


CODE_REGEX = re.compile(r"((\w|\d){4})-((\w|\d){4})-((\w|\d){4})-((\w|\d){4})")


class EventChecker:
    def get_checker_name(self) -> str:
        raise NotImplementedError()

    def get_codes(self) -> Iterable[str]:
        raise NotImplementedError()
