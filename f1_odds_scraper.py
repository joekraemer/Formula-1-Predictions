from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import Dict, List, Optional
import pandas as pd
from pathlib import Path
import time
from datetime import datetime

class F1OddsScraper:
    """A class to scrape F1 betting odds from Oddschecker."""

    def __init__(self, race : str, data_dir: str = "data", year: Optional[int] = None, headless: bool = True):
        """
        Initialize the F1OddsScraper.

        Args:
            data_dir (str): Directory to save scraped data
            year (int, optional): Year for the F1 season. Defaults to current year.
            headless (bool): Whether to run browser in headless mode
        """
        self.race = race
        self.base_url = "https://www.oddschecker.com/motorsport/formula-1"  # Base URL without race
        self.data_dir = Path(data_dir)
        self.year = year or datetime.now().year
        self.headless = headless
        self.driver = None
        self.setup_directories()

    def setup_directories(self):
        """Set up the directory structure for data storage."""
        # Create main data directory if it doesn't exist
        self.data_dir.mkdir(exist_ok=True)
        
        # Create year directory
        self.year_dir = self.data_dir / str(self.year)
        self.year_dir.mkdir(exist_ok=True)

    def get_race_dir(self) -> Path:
        """
        Get the directory path for the race.

        Returns:
            Path: Path to the race directory
        """
        race_dir = self.year_dir / self.race
        race_dir.mkdir(exist_ok=True)
        return race_dir

    def __del__(self):
        """Destructor to ensure proper cleanup."""
        if self.driver:
            self.close_driver()

    def setup_driver(self):
        """Set up the Selenium WebDriver with appropriate options."""
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument('--headless=new')  # Updated headless mode
        
        # Add additional options to avoid detection
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920x1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        
        # Add user agent to appear more like a regular browser
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)
        
        # Mask webdriver to avoid detection
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def close_driver(self):
        """Close the Selenium WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def get_odds_url(self, category: str) -> str:
        """
        Construct the URL for specific odds.

        Args:
            category (str): Category of odds (e.g., 'qualifying', 'race-winner')

        Returns:
            str: Complete URL for the specified odds
        """
        return f"{self.base_url}/{self.race}/{category}"

    def extract_odds_data(self) -> List[Dict]:
        """
        Extract odds data from the current page.

        Returns:
            List[Dict]: List of dictionaries containing odds data
        """
        odds_data = []
        rows = self.driver.find_elements(By.CSS_SELECTOR, ".odds-table tbody tr")
        
        for row in rows:
            driver_data = {}
            
            # Get driver name
            try:
                driver_data['Driver'] = row.find_element(By.CSS_SELECTOR, ".driver-name").text
            except NoSuchElementException:
                continue

            # Get odds from different providers
            odds_cells = row.find_elements(By.CSS_SELECTOR, ".odds-cell")
            for cell in odds_cells:
                provider = cell.get_attribute("data-provider")
                odds = cell.text.strip()
                if provider and odds:
                    driver_data[provider] = odds

            odds_data.append(driver_data)

        return odds_data

    def save_odds_data(self, df: pd.DataFrame, category: str) -> Path:
        """
        Save scraped odds data to CSV in the appropriate race directory.

        Args:
            df (pd.DataFrame): DataFrame containing odds data
            category (str): Category of odds

        Returns:
            Path: Path to the saved file
        """
        # Convert numeric columns to proper type
        numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
        df[numeric_columns] = df[numeric_columns].astype(str)
        
        race_dir = self.get_race_dir()
        filename = f"{category}_odds.csv"
        filepath = race_dir / filename
        df.to_csv(filepath, index=False)
        return filepath

    def scrape_odds(self, category: str, save: bool = True) -> pd.DataFrame:
        """
        Scrape odds for a specific category.

        Args:
            category (str): Category of odds
            save (bool): Whether to save the scraped data to CSV

        Returns:
            pd.DataFrame: DataFrame containing the scraped odds
        """
        if not self.driver:
            self.setup_driver()

        url = self.get_odds_url(category)
        print(f"  Scraping {category} odds from {url}")

        try:
            self.driver.get(url)
            
            # Add a small delay to let JavaScript load
            time.sleep(3)
            
            # Wait for the odds table to load with increased timeout
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "odds-table"))
                )
            except TimeoutException:
                print(f"  Page source: {self.driver.page_source[:500]}...")  # Print first 500 chars of page source for debugging
                raise

            # Extract odds data
            odds_data = self.extract_odds_data()
            
            if not odds_data:
                print("  No odds data found in the table")
                return pd.DataFrame()
                
            # Convert to DataFrame
            df = pd.DataFrame(odds_data)
            
            if save and not df.empty:
                filepath = self.save_odds_data(df, category)
                print(f"  Saved {category} odds to {filepath}")
            
            return df

        except TimeoutException:
            print(f"  Timeout while loading {category} odds at {url}")
            raise
        except Exception as e:
            print(f"  Error scraping {category} odds: {str(e)}")
            raise

    def scrape_all_categories(self, categories: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Scrape odds for all specified categories.

        Args:
            categories (List[str]): List of categories to scrape

        Returns:
            Dict[str, pd.DataFrame]: Dictionary mapping categories to their respective DataFrames
        """
        results = {}
        race_dir = self.get_race_dir()
        
        for category in categories:
            try:
                results[category] = self.scrape_odds(category)
            except Exception as e:
                continue
        
        return results

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