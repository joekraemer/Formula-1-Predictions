import unittest
from unittest.mock import patch, Mock, MagicMock
import pandas as pd
from pathlib import Path
import shutil
from f1_odds_scraper import F1OddsScraper

class TestF1OddsScraper(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_data_dir = "test_scraper_data"
        self.test_race = "australian-gp"
        self.scraper = F1OddsScraper(race=self.test_race, data_dir=self.test_data_dir)

    def tearDown(self):
        """Clean up after each test."""
        # Clean up the scraper
        if hasattr(self, 'scraper'):
            if self.scraper.driver:
                self.scraper.close_driver()

        # Now we can safely remove the test directory
        try:
            if Path(self.test_data_dir).exists():
                shutil.rmtree(self.test_data_dir)
        except PermissionError as e:
            print(f"Warning: Could not remove test directory: {e}")

    def test_get_odds_url(self):
        """Test URL construction."""
        category = "qualifying"
        expected_url = f"{self.scraper.base_url}/{self.test_race}/{category}"
        self.assertEqual(self.scraper.get_odds_url(category), expected_url)

    @patch('selenium.webdriver.Chrome')
    def test_setup_driver(self, mock_chrome):
        """Test WebDriver setup."""
        self.scraper.setup_driver()
        mock_chrome.assert_called_once()
        self.assertIsNotNone(self.scraper.driver)

    @patch('selenium.webdriver.Chrome')
    def test_context_manager(self, mock_chrome):
        """Test context manager functionality."""
        with F1OddsScraper(race=self.test_race, data_dir=self.test_data_dir) as scraper:
            self.assertIsNotNone(scraper.driver)
        mock_chrome.return_value.quit.assert_called_once()

    @patch('selenium.webdriver.Chrome')
    def test_scrape_odds(self, mock_chrome):
        """Test odds scraping functionality."""
        # Mock the WebDriver and its methods
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Mock find_elements to return a list of mock rows
        mock_row = MagicMock()
        mock_driver_name = MagicMock()
        mock_driver_name.text = "Max Verstappen"
        mock_row.find_element.return_value = mock_driver_name
        
        mock_odds_cell = MagicMock()
        mock_odds_cell.get_attribute.return_value = "Bookmaker1"
        mock_odds_cell.text = "2.5"
        mock_row.find_elements.return_value = [mock_odds_cell]
        
        mock_driver.find_elements.return_value = [mock_row]
        
        # Test scraping
        df = self.scraper.scrape_odds("qualifying", save=False)
        
        # Verify the results
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['Driver'], "Max Verstappen")
        self.assertEqual(df.iloc[0]['Bookmaker1'], "2.5")

    def test_save_odds_data(self):
        """Test saving odds data to CSV."""
        test_data = {
            'Driver': ['Max Verstappen', 'Lewis Hamilton'],
            'Bookmaker1': ['2.5', '3.0'],  # Keep as strings since that's how they're stored
            'Bookmaker2': ['2.6', '3.1']
        }
        df = pd.DataFrame(test_data)
        
        filepath = self.scraper.save_odds_data(df, "qualifying")
        
        # Check if file exists and contains correct data
        self.assertTrue(filepath.exists())
        
        # Read and verify saved data
        saved_df = pd.read_csv(filepath)
        
        # Ensure both dataframes have the same dtypes (string/object)
        for col in df.columns:
            df[col] = df[col].astype(str)
            saved_df[col] = saved_df[col].astype(str)
        
        pd.testing.assert_frame_equal(saved_df, df)

    @patch('selenium.webdriver.Chrome')
    def test_scrape_all_categories(self, mock_chrome):
        """Test scraping multiple categories."""
        # Mock the scrape_odds method
        with patch.object(F1OddsScraper, 'scrape_odds') as mock_scrape:
            mock_df = pd.DataFrame({
                'Driver': ['Max Verstappen'],
                'Odds': ['2.5']  # String type to match expected behavior
            })
            mock_scrape.return_value = mock_df
            
            categories = ['qualifying', 'race-winner']
            results = self.scraper.scrape_all_categories(categories)
            
            # Verify results
            self.assertEqual(len(results), 2)
            self.assertIn('qualifying', results)
            self.assertIn('race-winner', results)
            for df in results.values():
                self.assertIsInstance(df, pd.DataFrame)

    def test_error_handling(self):
        """Test error handling in scraping."""
        with patch.object(F1OddsScraper, 'extract_odds_data') as mock_extract:
            mock_extract.side_effect = Exception("Test error")
            
            with self.assertRaises(Exception):
                self.scraper.scrape_odds("qualifying")

if __name__ == '__main__':
    unittest.main() 