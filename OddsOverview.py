from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By  # Import the missing By class
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# Set up Selenium driver with custom user-agent
options = Options()
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
options.add_argument("--headless")  # Run in headless mode (no GUI)
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")

# Initialize driver
driver = webdriver.Chrome(service=Service(
    ChromeDriverManager().install()), options=options)


def parse_driver_odds(driver):
    # Find all the rows containing driver information
    driver_rows = driver.find_elements(
        By.XPATH, "//tr[@class='diff-row evTabRow bc']")

    driver_data = []

    # Loop through each row and extract the necessary data
    for row in driver_rows:
        driver_info = {}

        # Get the driver's name
        driver_info['name'] = row.get_attribute('data-bname')

        # Find all the betting odds (td elements with class 'bc bs o' or 'np o')
        odds_elements = row.find_elements(
            By.XPATH, ".//td[contains(@class, 'bc bs o')] | .//td[contains(@class, 'np o')]")

        # Parse the odds and provider codes
        odds_data = []
        for odds in odds_elements:
            provider_code = odds.get_attribute(
                'data-bk')  # Betting provider code
            # Extract odds value (e.g., '1/16')
            data_odds = odds.get_attribute('data-o')

            # Store the odds in the dictionary if available
            if data_odds:
                odds_data.append({
                    'provider': provider_code,
                    'odds': data_odds
                })

            # Check for the odds inside the <p> tag
            p_tag_odds = odds.find_element(
                By.XPATH, ".//p").text if odds.find_elements(By.XPATH, ".//p") else None
            if p_tag_odds:
                odds_data.append({
                    'provider': provider_code,
                    'odds': p_tag_odds
                })

        # Store the odds data for the driver
        driver_info['odds'] = odds_data
        driver_data.append(driver_info)

    return driver_data


try:
    # Step 3: Open the website
    url = "https://www.oddschecker.com/motorsport/formula-1/australian-grand-prix/to-be-classified"
    driver.get(url)

    # Wait for the page to load and verify
    time.sleep(5)  # Add a short sleep to ensure page load

    # Parse the driver data (including odds)
    driver_odds = parse_driver_odds(driver)

    # Loop through each driver's data and print
    for driver_info in driver_odds:
        print(f"Driver: {driver_info['name']}")
        for odds_info in driver_info['odds']:
            print(
                f"  Provider: {odds_info['provider']}, Odds: {odds_info['odds']}")

finally:
    driver.quit()
