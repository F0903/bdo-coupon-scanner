import time
from bdo_coupon_scanner.checker import CodeChecker
from bdo_coupon_scanner.site_checker import OfficialSiteChecker
from bdo_coupon_scanner.twitter_checker import TwitterChecker


def check(checker: CodeChecker):
    print(f"Searching for {checker.get_checker_name()} codes...")
    start = time.perf_counter_ns()
    codes = checker.get_codes()
    end = time.perf_counter_ns()
    total = (end - start) / 1000000
    if len(codes) == 0:
        print("No codes were found.")
    else:
        print(f"Found codes[{total}ms]:")
        for x in codes:
            print(x)


def main():
    checkers = [OfficialSiteChecker(), TwitterChecker()]

    for checker in checkers:
        try:
            check(checker)
            print("\n")
        except Exception as e:
            print(f"Error encountered!:\n{e}\nTrying next...")

    input("Done!\nPress any key to exit...")


if __name__ == "__main__":
    main()