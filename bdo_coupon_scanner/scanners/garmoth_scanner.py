from typing import Iterable
import logging
import datetime
import selenium.webdriver as web
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from .scanner_base import CouponScannerBase
from .scanner_error import ScannerError, ScannerTimeoutError
from ..coupon import Coupon

BASE_URL = "https://garmoth.com"


class GarmothScanner(CouponScannerBase):
    def get_scanner_name(self) -> str:
        return "Garmoth Scanner"

    def get_codes(self) -> Iterable[Coupon]:
        try:
            log = logging.getLogger(__name__)
            log.debug(f"Scanning Garmoth...")
            firefox_options = web.FirefoxOptions()
            firefox_options.add_argument("--headless")
            with web.Firefox(firefox_options) as browser:
                browser.implicitly_wait(45)
                browser.get(BASE_URL)
                see_more_button = browser.find_element(
                    By.CSS_SELECTOR, 'a[href="/coupons"]'
                )
                assert see_more_button.text == "See more"
                see_more_button.click()
                available_coupons_section = browser.find_element(
                    By.CSS_SELECTOR, "section"
                )
                coupon_containers = available_coupons_section.find_elements(
                    By.CSS_SELECTOR, "input[id]"
                )
                for container in coupon_containers:
                    yield Coupon(
                        container.get_attribute("id"), datetime.date.today(), BASE_URL
                    )
        except TimeoutError:
            raise ScannerTimeoutError
        except Exception:
            raise ScannerError
