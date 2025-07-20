from typing import Iterable
import logging
import datetime
import selenium.webdriver as web
from selenium.webdriver.common.by import By
from .scanner_base import CouponScannerBase
from .scanner_error import ScannerError, ScannerTimeoutError
from ..coupon import Coupon

CODES_URL = "https://garmoth.com/coupons"


class GarmothScanner(CouponScannerBase):
    def get_scanner_name(self) -> str:
        return "Garmoth Scanner"

    def get_codes(self) -> Iterable[Coupon]:
        try:
            log = logging.getLogger(__name__)

            log.debug(f"Scanning Garmoth...")

            firefox_options = web.FirefoxOptions()
            firefox_options.add_argument("--headless")
            firefox_options.add_argument("window-size=1280,800")
            firefox_options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
            )

            WAIT_TIMEOUT = 30  # seconds
            with web.Firefox(firefox_options) as browser:
                browser.set_script_timeout(WAIT_TIMEOUT)
                browser.implicitly_wait(WAIT_TIMEOUT)

                # Remove navigator.webdriver Flag using JavaScript
                browser.execute_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )

                browser.get(CODES_URL)

                # If the page has a cookie consent banner, accept it
                browser.implicitly_wait(1)  # Short wait for cookie check
                cookie_button = browser.find_elements(
                    By.CSS_SELECTOR, "button#accept-cookies"
                )
                if cookie_button:
                    cookie_button[0].click()
                browser.implicitly_wait(WAIT_TIMEOUT)  # Restore wait

                # The first section is the "Available" section
                available_coupons_section = browser.find_element(
                    By.CSS_SELECTOR, "section"
                )
                coupon_containers = available_coupons_section.find_elements(
                    By.CSS_SELECTOR, "input[id]"
                )

                for container in coupon_containers:
                    id_attr = container.get_attribute("id")
                    if not id_attr:
                        continue
                    yield Coupon(id_attr, datetime.date.today(), CODES_URL)
        except TimeoutError:
            raise ScannerTimeoutError
        except Exception:
            raise ScannerError
