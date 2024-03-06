import time
import traceback
from .scanners.scanner_base import CouponScannerBase
from .scanners.site_scanner import OfficialSiteScanner
from .scanners.garmoth_scanner import GarmothScanner

""" from .scanners.twitter_scanner import TwitterScanner """


def scan(scanner: CouponScannerBase):
    print(f"Running {scanner.get_scanner_name()}")
    before_codes = time.perf_counter_ns()
    codes = scanner.get_codes()
    after_codes = time.perf_counter_ns()
    print(f"get_codes took: {(after_codes - before_codes) / 1000000}ms")
    current = time.perf_counter_ns()
    for x in codes:
        now = time.perf_counter_ns()
        time_taken = now - current
        current = now
        print(f"{x} {time_taken / 1000000}ms")


def main():
    scanners = [OfficialSiteScanner(), GarmothScanner()]

    for scanner in scanners:
        try:
            scan(scanner)
            print("\n")
        except Exception as e:
            strbuf = ""
            for s in traceback.format_exception(e):
                strbuf += s
            print(f"Error encountered!:\n{strbuf}\nTrying next...")

    input("Done!\nPress any key to exit...")


if __name__ == "__main__":
    main()
