from typing import Iterable
import logging
import snscrape.modules.twitter as t
from itertools import takewhile
from .scanner_base import CODE_REGEX, CouponScannerBase
from ..coupon import Coupon


class TwitterScanner(CouponScannerBase):
    MAX_TWEETS = 20

    def get_scanner_name(self) -> str:
        return "Official Twitter Scanner"

    def check_tweet(self, tweet: t.Tweet) -> Coupon | None:
        log = logging.getLogger("bdocs.site-scanner")
        log.debug(f"Scanning tweet: {tweet.url}")
        text = tweet.content
        result = CODE_REGEX.search(text)
        if result == None:
            return None
        link = tweet.url
        code = result.group()
        date = tweet.date.date()
        return Coupon(code, date, link)

    def get_codes(self) -> Iterable[Coupon]:
        log = logging.getLogger("bdocs.twitter-scanner")
        log.debug("Scanning twitter codes...")
        profile = t.TwitterUserScraper("NewsBlackDesert")
        codes = set()
        for i, item in takewhile(
            lambda x: x[0] < self.MAX_TWEETS, enumerate(profile.get_items())
        ):
            if isinstance(item, t.Tweet):
                result = self.check_tweet(item)
                if result != None:
                    codes.add(result)
        return codes
