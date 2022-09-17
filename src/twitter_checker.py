import snscrape.modules.twitter as t
from checker import CODE_REGEX, EventChecker
from itertools import takewhile


MAX_TWEETS = 20


class TwitterEventChecker(EventChecker):
    def get_checker_name(self) -> str:
        return "official twitter"

    def check_tweet(self, tweet: t.Tweet) -> str | None:
        text = tweet.content
        result = CODE_REGEX.search(text)
        if result != None:
            return result.group()

    def get_codes(self) -> list[str]:
        profile = t.TwitterUserScraper("NewsBlackDesert")
        codes = []
        for i, item in takewhile(
            lambda x: x[0] < MAX_TWEETS, enumerate(profile.get_items())
        ):
            if isinstance(item, t.Tweet):
                result = self.check_tweet(item)
                if result != None:
                    codes.append(result)
        return codes
