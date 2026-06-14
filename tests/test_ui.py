"""Selenium UI test for the Sentiment Analyzer frontend.

Uses headless Chrome. The function name `test_frontend_sentiment` is required
exactly by the grading script. The three fixed element IDs (text-input,
submit-btn, result-output) defined in templates/index.html are used directly.

Environment variables:
  APP_URL              - URL of the frontend (default http://localhost:5000)
  SELENIUM_REMOTE_URL  - if set, use a remote Selenium WebDriver (containerized
                         Chrome, e.g. http://localhost:4444). Otherwise a local
                         headless Chrome is launched.
"""
import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

APP_URL = os.environ.get("APP_URL", "http://localhost:5000")
SELENIUM_REMOTE_URL = os.environ.get("SELENIUM_REMOTE_URL", "")


def _make_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,1024")
    if SELENIUM_REMOTE_URL:
        return webdriver.Remote(command_executor=SELENIUM_REMOTE_URL, options=options)
    return webdriver.Chrome(options=options)


def test_frontend_sentiment():
    driver = _make_driver()
    try:
        driver.get(APP_URL)

        # Send a test sentence into the input box.
        text_input = driver.find_element(By.ID, "text-input")
        text_input.clear()
        text_input.send_keys("This product is absolutely wonderful")

        # Click the analyze button.
        driver.find_element(By.ID, "submit-btn").click()

        # Wait for the async prediction to populate result-output.
        result_text = ""
        for _ in range(30):
            result_text = driver.find_element(By.ID, "result-output").text
            if result_text.strip():
                break
            time.sleep(1)

        # Assert non-empty AND contains POSITIVE, NEGATIVE, or Confidence.
        assert result_text.strip() != "", "result-output was empty"
        assert ("POSITIVE" in result_text
                or "NEGATIVE" in result_text
                or "Confidence" in result_text), f"unexpected result text: {result_text!r}"
    finally:
        driver.quit()
