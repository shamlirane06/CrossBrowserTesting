
import os
import re
import time
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_URL = "https://www.practiceqaautomation.com"
HOTEL_URL = f"{BASE_URL}/apps/hotel"
GRID_URL = os.getenv("GRID_URL", "http://localhost:4444/wd/hub")
BROWSER = os.getenv("BROWSER", "chrome").lower()

WAIT_SECONDS = 25
LIVE_PAUSE_SECONDS = int(os.getenv("LIVE_PAUSE_SECONDS", "3"))
CONFIRMATION_PAUSE_SECONDS = int(
    os.getenv("CONFIRMATION_PAUSE_SECONDS", "25")
)

SCREENSHOT_DIR = Path("screenshots") / BROWSER
REPORT_DIR = Path("reports")


# Fictional guest details and practice payment data only.
GUEST = {
    "first_name": "Ada",
    "last_name": "Lovelace",
    "email": "ada@example.com",
    "phone": "5551234567",
}

TEST_CARD = {
    "number": "4242424242424242",
    "expiry": "12/30",
    "cvv": "123",
}


# --------------------------------------------------
# Locator helpers
# --------------------------------------------------

def tid(test_id):
    return (By.CSS_SELECTOR, f"[data-testid='{test_id}']")


def first_found(driver, locators, timeout=WAIT_SECONDS):
    """Return the first visible element matching a list of locators."""
    end_time = time.time() + timeout
    last_error = None

    while time.time() < end_time:
        for locator in locators:
            try:
                elements = driver.find_elements(*locator)
                for element in elements:
                    if element.is_displayed():
                        return element
            except (StaleElementReferenceException, NoSuchElementException) as exc:
                last_error = exc

        time.sleep(0.25)

    raise TimeoutException(
        f"Could not find a visible element using these locators: {locators}"
    ) from last_error


class Ui:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, WAIT_SECONDS)

    def pause(self, seconds=None):
        """Pause so the live browser steps can be watched."""
        time.sleep(
            LIVE_PAUSE_SECONDS if seconds is None else seconds
        )

    def scroll_to(self, element):
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            element,
        )
        return element

    def click(self, locator):
        element = self.wait.until(
            EC.element_to_be_clickable(locator)
        )
        self.scroll_to(element)
        self.pause(0.5)

        try:
            element.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", element)

        self.pause()

    def click_first(self, locators):
        element = first_found(self.driver, locators)
        self.scroll_to(element)
        self.pause(0.5)

        try:
            self.wait.until(lambda d: element.is_enabled())
            element.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", element)

        self.pause()

    def type(self, locators, value):
        element = first_found(self.driver, locators)
        self.scroll_to(element)
        element.clear()
        element.send_keys(value)
        self.pause(0.3)

    def select(self, locator, value):
        element = self.wait.until(
            EC.element_to_be_clickable(locator)
        )
        Select(element).select_by_value(value)
        self.pause()

    def check(self, locators):
        element = first_found(self.driver, locators)
        self.scroll_to(element)

        if not element.is_selected():
            try:
                element.click()
            except ElementClickInterceptedException:
                self.driver.execute_script(
                    "arguments[0].click();", element
                )

        self.pause(0.5)

    def wait_for_url(self, fragment):
        self.wait.until(EC.url_contains(fragment))
        self.pause()

    def wait_for_page(self):
        self.wait.until(
            lambda d: d.execute_script(
                "return document.readyState"
            ) == "complete"
        )

    def body_text(self):
        return self.driver.find_element(By.TAG_NAME, "body").text

    def save_screenshot(self, filename):
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        path = SCREENSHOT_DIR / filename

        self.driver.save_screenshot(str(path))
        print(f"Screenshot saved: {path.resolve()}")

    def optional_check(self, locators):
        """Check an optional add-on only if it exists."""
        try:
            element = first_found(
                self.driver, locators, timeout=3
            )
            if not element.is_selected():
                element.click()
            self.pause(0.5)
            return True
        except TimeoutException:
            print(f"Optional element not found: {locators}")
            return False


# --------------------------------------------------
# Browser fixture
# --------------------------------------------------

@pytest.fixture
def driver():
    if BROWSER == "chrome":
        options = webdriver.ChromeOptions()
        options.add_experimental_option(
            "prefs",
            {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.password_manager_leak_detection": False,
            },
        )
    elif BROWSER == "firefox":
        options = webdriver.FirefoxOptions()
    else:
        pytest.fail(
            f"Unsupported browser '{BROWSER}'. "
            "Set BROWSER to chrome or firefox."
        )

    browser_driver = webdriver.Remote(
        command_executor=GRID_URL,
        options=options,
    )
    browser_driver.set_window_size(1440, 1000)

    try:
        yield browser_driver
    finally:
        browser_driver.quit()


# --------------------------------------------------
# End-to-end hotel booking test
# --------------------------------------------------

def test_books_hotel_end_to_end_and_checks_confirmation(driver):
    ui = Ui(driver)
    reservation_id = None

    try:
        # STEP 1: Open the hotel practice application.
        print("\nSTEP 1: Opening the hotel booking application")
        driver.get(HOTEL_URL)
        ui.wait_for_page()
        ui.pause()

        assert "/apps/hotel" in driver.current_url, (
            f"Hotel application did not open: {driver.current_url}"
        )

        # STEP 2: Search for Goa.
        print("STEP 2: Selecting Goa and searching for hotels")

        city = first_found(
            driver,
            [
                (By.ID, "city"),
                (By.NAME, "city"),
                tid("city"),
            ],
        )
        Select(city).select_by_value("goa")
        ui.pause()

        # Keep the site's default dates and guest count.
        # This avoids depending on unverified calendar selectors.
        ui.click_first(
            [
                tid("search-hotels"),
                (By.ID, "search-hotels"),
                (
                    By.XPATH,
                    "//button[normalize-space()='Search hotels']",
                ),
            ]
        )

        ui.wait_for_url("/apps/hotel/results")
        print(f"Hotel results opened: {driver.current_url}")

        # STEP 3: Select Palm Grove Resort.
        print("STEP 3: Selecting Palm Grove Resort")

        ui.click_first(
            [
                tid("view-rooms-g1"),
                (
                    By.CSS_SELECTOR,
                    "a[href='/apps/hotel/hotel/g1']",
                ),
            ]
        )

        ui.wait_for_url("/apps/hotel/hotel/g1")

        hotel_heading = first_found(
            driver,
            [
                tid("hotel-title"),
                (By.CSS_SELECTOR, "h1"),
            ],
        )

        assert "Palm Grove Resort" in hotel_heading.text, (
            f"Unexpected hotel selected: {hotel_heading.text}"
        )

        print(f"Hotel selected: {hotel_heading.text}")

        # STEP 4: Select the Deluxe Room and breakfast.
        print("STEP 4: Selecting the Deluxe Room")

        ui.click_first(
            [
                tid("select-room-deluxe"),
                (By.ID, "select-room-deluxe"),
            ]
        )

        ui.optional_check(
            [
                (By.ID, "addon-breakfast"),
                tid("addon-breakfast"),
            ]
        )

        # STEP 5: Continue to checkout.
        print("STEP 5: Continuing to guest details and payment")

        ui.click_first(
            [
                tid("continue-booking"),
                (By.ID, "continue-booking"),
                (
                    By.XPATH,
                    "//button[contains(normalize-space(.), "
                    "'Continue to booking')]",
                ),
                (
                    By.XPATH,
                    "//button[contains(normalize-space(.), "
                    "'Continue')]",
                ),
            ]
        )

        ui.wait.until(
            lambda d: (
                "/apps/hotel/checkout" in d.current_url
                or len(
                    d.find_elements(
                        By.ID, "guest-first-name"
                    )
                ) > 0
            )
        )
        ui.pause()

        # STEP 6: Enter fictional guest details.
        print("STEP 6: Entering fictional guest details")

        ui.type(
            [
                (By.ID, "guest-first-name"),
                (By.NAME, "guest-first-name"),
                tid("guest-first-name"),
            ],
            GUEST["first_name"],
        )

        ui.type(
            [
                (By.ID, "guest-last-name"),
                (By.NAME, "guest-last-name"),
                tid("guest-last-name"),
            ],
            GUEST["last_name"],
        )

        ui.type(
            [
                (By.ID, "guest-email"),
                (By.NAME, "guest-email"),
                tid("guest-email"),
            ],
            GUEST["email"],
        )

        ui.type(
            [
                (By.ID, "guest-phone"),
                (By.NAME, "guest-phone"),
                tid("guest-phone"),
            ],
            GUEST["phone"],
        )

        # STEP 7: Select an arrival time if the control exists.
        print("STEP 7: Selecting arrival time")

        try:
            arrival = first_found(
                driver,
                [
                    (By.ID, "arrival-time"),
                    (By.NAME, "arrival-time"),
                    tid("arrival-time"),
                ],
                timeout=5,
            )
            Select(arrival).select_by_visible_text(
                "14:00 – 16:00"
            )
        except TimeoutException:
            print(
                "Arrival-time selector was not found; "
                "keeping the site's default."
            )

        ui.pause()

        # STEP 8: Select payment by card.
        print("STEP 8: Selecting card payment")

        ui.click_first(
            [
                tid("pay-now"),
                (By.ID, "pay-now"),
            ]
        )

        # STEP 9: Enter the practice site's test card details.
        print("STEP 9: Entering practice payment details")

        ui.type(
            [
                (By.ID, "card-number"),
                tid("card-number"),
            ],
            TEST_CARD["number"],
        )

        ui.type(
            [
                (By.ID, "card-expiry"),
                (By.NAME, "card-expiry"),
                (By.CSS_SELECTOR, "[placeholder='MM/YY']"),
            ],
            TEST_CARD["expiry"],
        )

        ui.type(
            [
                (By.ID, "card-cvv"),
                (By.NAME, "card-cvv"),
                tid("card-cvv"),
            ],
            TEST_CARD["cvv"],
        )

        ui.check(
            [
                (By.ID, "accept-policy"),
                tid("accept-policy"),
            ]
        )

        # STEP 10: Confirm the booking.
        print("STEP 10: Confirming the booking")

        ui.click_first(
            [
                tid("confirm-booking"),
                (By.ID, "confirm-booking"),
                (
                    By.XPATH,
                    "//button[normalize-space()='Confirm booking']",
                ),
            ]
        )

        # STEP 11: Verify that a confirmation/receipt appears.
        print("STEP 11: Waiting for booking confirmation")

        confirmation_locators = [
            tid("booking-confirmed"),
            tid("reservation-id"),
            tid("booking-confirmation"),
            tid("confirmation-number"),
            (By.ID, "booking-confirmed"),
            (By.ID, "reservation-id"),
            (
                By.XPATH,
                "//*[contains(translate(normalize-space(.), "
                "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                "'abcdefghijklmnopqrstuvwxyz'), 'booking confirmed')]",
            ),
            (
                By.XPATH,
                "//*[contains(translate(normalize-space(.), "
                "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                "'abcdefghijklmnopqrstuvwxyz'), 'reservation confirmed')]",
            ),
            (
                By.XPATH,
                "//*[contains(translate(normalize-space(.), "
                "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                "'abcdefghijklmnopqrstuvwxyz'), 'booking reference')]",
            ),
        ]

        confirmation_element = first_found(
            driver,
            confirmation_locators,
            timeout=WAIT_SECONDS,
        )

        ui.wait_for_page()
        ui.pause()

        confirmation_text = ui.body_text()
        print("\n--- Confirmation page text ---")
        print(confirmation_text[:5000])
        print("--- End confirmation page text ---\n")

        # Look for a reservation/reference number in common formats.
        reservation_patterns = [
            r"\bSE-[A-Z0-9-]+\b",
            r"\b(?:reservation|booking)\s*(?:id|number|reference|#)"
            r"\s*[:#-]?\s*([A-Z0-9-]{4,})",
        ]

        for pattern in reservation_patterns:
            match = re.search(
                pattern, confirmation_text, re.IGNORECASE
            )
            if match:
                reservation_id = (
                    match.group(0)
                    if pattern.startswith(r"\bSE-")
                    else match.group(1)
                )
                break

        assert confirmation_element is not None, (
            "The booking confirmation element was not found."
        )

        # Ensure the page contains confirmation-like text.
        assert re.search(
            r"confirm|reservation|booking|receipt|reference",
            confirmation_text,
            re.IGNORECASE,
        ), "The page did not contain recognizable confirmation text."

        if reservation_id:
            print(f"Reservation reference detected: {reservation_id}")
        else:
            print(
                "No standard reservation ID pattern was detected. "
                "Review the confirmation text printed above."
            )

        ui.save_screenshot("booking_confirmation.png")

        # Keep the confirmation page open so you can watch it.
        print(
            f"Keeping the confirmation page open for "
            f"{CONFIRMATION_PAUSE_SECONDS} seconds."
        )
        ui.pause(CONFIRMATION_PAUSE_SECONDS)

        # STEP 12: Refresh and verify that confirmation remains visible.
        print("STEP 12: Refreshing the confirmation page")

        confirmation_url = driver.current_url
        driver.refresh()
        ui.wait_for_page()
        ui.pause()

        assert driver.current_url == confirmation_url, (
            "The page URL changed after refresh. "
            "The confirmation may not have persisted."
        )

        refreshed_text = ui.body_text()

        assert re.search(
            r"confirm|reservation|booking|receipt|reference",
            refreshed_text,
            re.IGNORECASE,
        ), (
            "No confirmation-related text remained after refresh."
        )

        if reservation_id:
            assert reservation_id in refreshed_text, (
                "The reservation reference was not present after refresh."
            )

        ui.save_screenshot("booking_confirmation_after_refresh.png")

        print("\nBOOKING TEST COMPLETED")
        print(f"Browser: {BROWSER}")
        print(f"Hotel: Palm Grove Resort")
        print(f"Room: Deluxe Room")
        print(f"Guest: {GUEST['first_name']} {GUEST['last_name']}")
        print(f"Reservation reference: {reservation_id or 'Review screenshot/log'}")
        print(f"Confirmation URL: {driver.current_url}")

    except Exception:
        # Preserve evidence when any step fails.
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        failure_path = SCREENSHOT_DIR / "booking_failure.png"

        try:
            driver.save_screenshot(str(failure_path))
            print(f"Failure screenshot saved: {failure_path.resolve()}")
            print(f"Failure URL: {driver.current_url}")
            print(f"Failure page title: {driver.title}")
            print(f"Failure page text:\n{driver.find_element(By.TAG_NAME, 'body').text[:3000]}")
        except Exception as screenshot_error:
            print(f"Could not capture failure evidence: {screenshot_error}")

        raise
