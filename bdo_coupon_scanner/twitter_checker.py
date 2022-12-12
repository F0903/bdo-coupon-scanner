from typing import Iterable
import snscrape.modules.twitter as t
from itertools import takewhile
from .checker import CODE_REGEX, CodeChecker


MAX_TWEETS = 20


class TwitterChecker(CodeChecker):
    def get_checker_name(self) -> str:
        return "official twitter"

    def check_tweet(self, tweet: t.Tweet) -> str | None:
        text = tweet.content
        result = CODE_REGEX.search(text)
        if result != None:
            return result.group()

    def get_codes(self) -> Iterable[str]:
        profile = t.TwitterUserScraper("NewsBlackDesert")
        codes = set()
        for i, item in takewhile(
            lambda x: x[0] < MAX_TWEETS, enumerate(profile.get_items())
        ):
            if isinstance(item, t.Tweet):
                result = self.check_tweet(item)
                if result != None:
                    codes.add(result)
        return codes
