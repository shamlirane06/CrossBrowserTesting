
import os
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


BASE_URL = "https://www.practiceqaautomation.com"
GRID_URL = os.getenv("GRID_URL", "http://localhost:4444")
BROWSER = os.getenv("BROWSER", "chrome").lower()

SCREENSHOT_DIR = Path(
    os.getenv("SCREENSHOT_DIR", f"screenshots/{BROWSER}")
)


@pytest.fixture
def driver():
    """Create a remote browser session on Selenium Grid and always close it."""
    if BROWSER == "chrome":
        options = webdriver.ChromeOptions()
    elif BROWSER == "firefox":
        options = webdriver.FirefoxOptions()
    else:
        pytest.fail(f"Unsupported browser: {BROWSER}")

    browser = webdriver.Remote(
        command_executor=GRID_URL,
        options=options,
    )
    browser.set_window_size(1440, 1000)

    try:
        yield browser
    finally:
        browser.quit()


def test_books_hotel_in_goa(driver):
    wait = WebDriverWait(driver, 30)

    def by_testid(testid):
        return (By.CSS_SELECTOR, f'[data-testid="{testid}"]')

    def click(locator):
        element = wait.until(EC.element_to_be_clickable(locator))
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            element,
        )
        element.click()

    def enter(locator, value):
        element = wait.until(
            EC.visibility_of_element_located(locator)
        )
        element.clear()
        element.send_keys(value)

    try:
        # 1. Open StayEase and search for Goa.
        driver.get(f"{BASE_URL}/apps/hotel")

        city = wait.until(
            EC.element_to_be_clickable((By.ID, "city"))
        )
        Select(city).select_by_value("goa")

        click(by_testid("search-hotels"))
        wait.until(EC.url_contains("/apps/hotel/results"))

        # 2. Verify results and open Palm Grove Resort.
        wait.until(
            EC.text_to_be_present_in_element(
                by_testid("page-title"),
                "Stays in Goa",
            )
        )
        wait.until(
            EC.text_to_be_present_in_element(
                by_testid("result-count"),
                "4 properties",
            )
        )

        click(by_testid("view-rooms-g1"))
        wait.until(EC.url_contains("/apps/hotel/hotel/g1"))

        wait.until(
            EC.text_to_be_present_in_element(
                by_testid("hotel-title"),
                "Palm Grove Resort",
            )
        )

        # 3. Select Deluxe Room and breakfast.
        click(by_testid("select-room-deluxe"))

        breakfast = wait.until(
            EC.element_to_be_clickable(
                by_testid("addon-breakfast")
            )
        )
        if not breakfast.is_selected():
            breakfast.click()

        click(by_testid("continue-booking"))

        # Correct checkout route.
        wait.until(EC.url_contains("/apps/hotel/checkout"))
        wait.until(
            EC.visibility_of_element_located(
                by_testid("confirm-booking")
            )
        )

        # 4. Enter fictional guest details.
        enter((By.ID, "guest-first-name"), "Ada")
        enter((By.ID, "guest-last-name"), "Lovelace")
        enter((By.ID, "guest-email"), "ada@example.com")
        enter((By.ID, "guest-phone"), "5551234567")

        Select(
            wait.until(
                EC.element_to_be_clickable(
                    (By.ID, "arrival-time")
                )
            )
        ).select_by_value("14:00 – 16:00")

        enter(
            (By.ID, "special-requests"),
            "Automated cross-browser test booking.",
        )

        # 5. Select the practice site's test-card payment option.
        click(by_testid("pay-now"))

        enter((By.ID, "card-number"), "4242 4242 4242 4242")
        enter((By.ID, "card-expiry"), "12/30")
        enter((By.ID, "card-cvv"), "123")

        policy = wait.until(
            EC.element_to_be_clickable((By.ID, "accept-policy"))
        )
        if not policy.is_selected():
            policy.click()

        total = wait.until(
            EC.visibility_of_element_located(
                by_testid("checkout-total")
            )
        ).text.strip()

        assert total, "Checkout total was empty"
        print(f"Checkout total displayed: {total}")

        # 6. Submit the booking.
        click(by_testid("confirm-booking"))

        # Wait for a confirmation or reservation page.
        wait.until(
            lambda browser: (
                "/apps/hotel/confirmation"
                in browser.current_url
                or "/apps/hotel/reservations"
                in browser.current_url
            )
        )

        confirmation_url = driver.current_url
        print(f"Booking result URL: {confirmation_url}")

        # Capture the confirmation before refreshing.
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        driver.save_screenshot(
            str(SCREENSHOT_DIR / "booking_success.png")
        )

        # 7. Basic confirmation-page validation.
        # Replace these generic checks with the actual confirmation
        # selectors after inspecting the live confirmation page.
        page_text = driver.find_element(
            By.TAG_NAME, "body"
        ).text

        assert page_text.strip(), (
            "The booking result page contained no visible text"
        )

        # 8. Refresh and verify that the booking result remains visible.
        driver.refresh()

        wait.until(
            lambda browser: (
                "/apps/hotel/confirmation"
                in browser.current_url
                or "/apps/hotel/reservations"
                in browser.current_url
            )
        )

        refreshed_text = wait.until(
            EC.visibility_of_element_located(
                (By.TAG_NAME, "body")
            )
        ).text

        assert refreshed_text.strip(), (
            "No booking information was visible after refresh"
        )

        print("Booking result page remained visible after refresh.")

    except Exception:
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

        try:
            driver.save_screenshot(
                str(SCREENSHOT_DIR / "booking_failure.png")
            )
        except Exception:
            pass

        raise