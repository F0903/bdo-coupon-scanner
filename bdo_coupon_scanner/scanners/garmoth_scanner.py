import asyncio
import logging
from datetime import date
from typing import Iterable, List

import selenium.webdriver as web
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..coupon import Coupon
from .scanner_base import CouponScannerBase
from .scanner_error import ScannerError, ScannerTimeoutError

CODES_URL = "https://garmoth.com/coupons"


class GarmothScanner(CouponScannerBase):
    def get_scanner_name(self) -> str:
        return "Garmoth Scanner"

    def _get_codes_sync(self) -> List[Coupon]:
        log = logging.getLogger(__name__)
        log.debug("Scanning Garmoth...")

        try:
            firefox_options = web.FirefoxOptions()
            firefox_options.add_argument("--headless")
            firefox_options.add_argument("window-size=1280,800")
            firefox_options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
            )

            # Loading optimizations
            firefox_options.set_preference("permissions.default.image", 2)
            firefox_options.set_preference("permissions.default.stylesheet", 2)
            firefox_options.page_load_strategy = 'eager'

            WAIT_TIMEOUT = 30  # seconds
            with web.Firefox(options=firefox_options) as browser:
                # Remove navigator.webdriver Flag using JavaScript
                browser.execute_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )

                browser.get(CODES_URL)

                try:
                    # Short explicit wait for cookie button, ignore if not found
                    cookie_button = WebDriverWait(browser, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button#accept-cookies"))
                    )
                    cookie_button.click()
                except Exception:
                    pass # Cookie banner might not appear or logic failed, proceed anyway

                coupon_containers = WebDriverWait(browser, WAIT_TIMEOUT).until(
                     lambda d: d.find_elements(By.CSS_SELECTOR, "section input[id]")
                )

                if not coupon_containers:
                     # Fallback check if the lambda returned an empty list but didn't timeout (rare)
                     log.warning("No coupon containers found on Garmoth.")
                     return []

                codes = []
                for container in coupon_containers:
                    id_attr = container.get_attribute("id")
                    if not id_attr:
                        continue
                    codes.append(Coupon(id_attr, date.today(), CODES_URL))
                return codes

        except TimeoutException:
            raise ScannerTimeoutError
        except Exception as e:
            log.error(f"Garmoth scanner failed: {e}")
            raise ScannerError

    async def get_codes(self) -> Iterable[Coupon]:
        return await asyncio.to_thread(self._get_codes_sync)
