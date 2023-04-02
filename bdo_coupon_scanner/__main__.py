import time
import traceback
from .scanners.scanner_base import CouponScannerBase
from .scanners.site_scanner import OfficialSiteScanner
from .scanners.twitter_scanner import TwitterScanner


def scan(scanner: CouponScannerBase):
    print(f"Running {scanner.get_scanner_name()}")
    start = time.perf_counter_ns()
    codes = scanner.get_codes()
    end = time.perf_counter_ns()
    total = (end - start) / 1000000
    if len(codes) == 0:
        print("No codes were found.")
    else:
        print(f"Found codes[{total}ms]:")
        for x in codes:
            print(x)


def main():
    scanners = [OfficialSiteScanner(), TwitterScanner()]

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
