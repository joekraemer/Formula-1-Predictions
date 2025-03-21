from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from typing import Dict, List, Optional
import pandas as pd
from pathlib import Path
import time
from datetime import datetime

class F1OddsScraper:
    """A class to scrape F1 betting odds from Oddschecker."""

    def __init__(self, race: str, data_dir: str = "data", year: Optional[int] = None, headless: bool = True):
        """
        Initialize the F1OddsScraper.

        Args:
            race (str): Race name (e.g., 'australian-grand-prix-2024')
            data_dir (str): Directory to save scraped data
            year (int, optional): Year for the F1 season. Defaults to current year.
            headless (bool): Whether to run browser in headless mode
        """
        self.race = race
        self.base_url = "https://www.oddschecker.com/motorsport/formula-1"
        self.data_dir = Path(data_dir)
        self.year = year or datetime.now().year
        self.headless = headless
        self.driver = None
        self.setup_directories()

    def setup_directories(self):
        """Set up the directory structure for data storage."""
        self.data_dir.mkdir(exist_ok=True)
        self.year_dir = self.data_dir / str(self.year)
        self.year_dir.mkdir(exist_ok=True)

    def get_race_dir(self) -> Path:
        """Get the directory path for the race."""
        race_dir = self.year_dir / self.race
        race_dir.mkdir(exist_ok=True)
        return race_dir

    def setup_driver(self):
        """Set up the Selenium WebDriver with appropriate options."""
        options = Options()
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.driver.implicitly_wait(10)

    def close_driver(self):
        """Close the Selenium WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def get_odds_url(self, category: str) -> str:
        """Construct the URL for specific odds."""
        return f"{self.base_url}/{self.race}/{category}"

    def extract_odds_data(self) -> List[Dict]:
        """Extract odds data from the current page."""
        odds_data = []
        
        # Find all the rows containing driver information using the specific XPATH
        rows = self.driver.find_elements(By.XPATH, "//tr[@class='diff-row evTabRow bc']")
        print(f"  Found {len(rows)} driver rows")
        
        for row in rows:
            driver_data = {}
            
            try:
                # Get driver name from the first cell
                driver_name = row.find_element(By.CSS_SELECTOR, "td:first-child").text.strip()
                if not driver_name:
                    continue
                    
                driver_data['Driver'] = driver_name
                
                # Get odds cells
                odds_cells = row.find_elements(By.CSS_SELECTOR, "td.bc")
                for cell in odds_cells:
                    provider = cell.get_attribute("data-bk")  # Changed from data-provider to data-bk
                    odds = cell.text.strip()
                    if provider and odds:
                        driver_data[provider] = odds
                
                if len(driver_data) > 1:  # Must have at least driver name and one odds
                    odds_data.append(driver_data)
                    
            except Exception as e:
                print(f"  Error processing row: {str(e)}")
                continue
        
        return odds_data

    def scrape_odds(self, category: str, save: bool = True) -> pd.DataFrame:
        """Scrape odds for a specific category."""
        if not self.driver:
            self.setup_driver()

        url = self.get_odds_url(category)
        print(f"  Scraping {category} odds from {url}")

        try:
            self.driver.get(url)
            time.sleep(5)  # Wait for page to load
            
            # Try to close country selector if it appears
            try:
                close_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Close']")
                if close_buttons:
                    print("  Found country selector, attempting to close...")
                    close_buttons[0].click()
                    time.sleep(1)
            except:
                pass

            # Extract odds data
            odds_data = self.extract_odds_data()
            
            if not odds_data:
                print("  No odds data found")
                return pd.DataFrame()
            
            print(f"  Found odds data for {len(odds_data)} drivers")
            
            # Convert to DataFrame
            df = pd.DataFrame(odds_data)
            
            if save and not df.empty:
                filepath = self.save_odds_data(df, category)
                print(f"  Saved {category} odds to {filepath}")
            
            return df

        except Exception as e:
            print(f"  Error scraping {category} odds: {str(e)}")
            raise

    def save_odds_data(self, df: pd.DataFrame, category: str) -> Path:
        """Save scraped odds data to CSV."""
        race_dir = self.get_race_dir()
        filename = f"{category}_odds.csv"
        filepath = race_dir / filename
        df.to_csv(filepath, index=False)
        return filepath

    def __enter__(self):
        """Context manager entry."""
        if not self.driver:
            self.setup_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_driver()

# Example usage
if __name__ == "__main__":
    # Base URL for the odds website
    BASE_URL = "https://example.com/f1/odds"  # Replace with actual base URL
    
    # Categories to scrape
    CATEGORIES = [
        "qualifying",
        "race-winner",
        "podium-finish",
        "top-6-finish",
        "top-10-finish"
    ]
    
    # Example usage with context manager
    with F1OddsScraper(BASE_URL) as scraper:
        # Scrape odds for Australian GP
        race = "australian-gp"
        results = scraper.scrape_all_categories(CATEGORIES)
        
        # Process results with F1OddsProcessor
        from f1_odds_processor import F1OddsProcessor
        processor = F1OddsProcessor()
        
        for category, df in results.items():
            print(f"\nProcessing {category} odds...")
            processed_df = processor.process_betting_odds(f"{race}_{category}_odds.csv")
            processor.calculate_average_probabilities()
            processor.normalize_probabilities()
            print(f"Processed {category} odds saved to CSV") 