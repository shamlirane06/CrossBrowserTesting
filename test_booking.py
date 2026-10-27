
import os
import time
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


GRID_URL = "http://localhost:4444"
TEST_URL = "https://www.selenium.dev/selenium/web/web-form.html"

# Delay between actions so you can watch the browser
STEP_DELAY = 3


def slow_down():
    time.sleep(STEP_DELAY)


@pytest.fixture
def driver():
    browser = os.getenv("BROWSER", "chrome").lower()

    if browser == "firefox":
        options = webdriver.FirefoxOptions()
    else:
        options = webdriver.ChromeOptions()

    browser_driver = webdriver.Remote(
        command_executor=GRID_URL,
        options=options
    )

    browser_driver.implicitly_wait(5)

    try:
        yield browser_driver
    finally:
        browser_driver.quit()


def test_demo_form_submission(driver):
    try:
        # Step 1: Open the demo web form
        print("Step 1: Opening the demo form...")
        driver.get(TEST_URL)
        slow_down()

        # Step 2: Find the text box
        print("Step 2: Finding the text box...")
        text_box = driver.find_element(By.NAME, "my-text")
        slow_down()

        # Step 3: Type text into the box
        print("Step 3: Entering text...")
        text_box.send_keys("DevOps Cross Browser Test")
        slow_down()

        # Step 4: Find the Submit button
        print("Step 4: Finding the Submit button...")
        submit_button = driver.find_element(By.TAG_NAME, "button")
        slow_down()

        # Step 5: Submit the form
        print("Step 5: Submitting the form...")
        submit_button.click()
        slow_down()

        # Step 6: Verify the result
        print("Step 6: Checking the submission result...")
        heading = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.TAG_NAME, "h1"))
        )

        assert heading.text == "Form submitted"

        print("SUCCESS: The form was submitted correctly!")

        # Keep the result visible for 10 seconds
        time.sleep(10)

    except Exception:
        # Save a screenshot if the test fails
        screenshot_dir = Path(
            os.getenv("SCREENSHOT_DIR", "screenshots")
        )
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        browser = os.getenv("BROWSER", "chrome").lower()
        driver.save_screenshot(
            str(screenshot_dir / f"{browser}_failure.png")
        )
        raise
