from typing import Iterable
import snscrape.twitter as t
from checker import CODE_REGEX, CodeChecker
from itertools import takewhile


MAX_TWEETS = 20


class TwitterEventChecker(CodeChecker):
    def get_checker_name(self) -> str:
        return "official twitter"

    def check_tweet(self, tweet: t.Tweet) -> str | None:
        text = tweet.rawContent
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
