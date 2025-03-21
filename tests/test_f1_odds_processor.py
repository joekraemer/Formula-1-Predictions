import unittest
import pandas as pd
import numpy as np
from f1_odds_processor import F1OddsProcessor
import os
from pathlib import Path
import shutil

class TestF1OddsProcessor(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_data_dir = "test_data"
        self.test_race = "test-race"
        self.test_category = "qualifying"
        self.processor = F1OddsProcessor(data_dir=self.test_data_dir)
        
        self.test_odds = {
            "Max Verstappen": 10,
            "Lewis Hamilton": 12,
            "Charles Leclerc": 14
        }
        self.processor.set_game_odds(self.test_odds)

    def tearDown(self):
        """Clean up after each test."""
        if Path(self.test_data_dir).exists():
            shutil.rmtree(self.test_data_dir)

    def test_data_directory_creation(self):
        """Test that the data directory is created properly."""
        self.assertTrue(Path(self.test_data_dir).exists())
        self.assertTrue(Path(self.test_data_dir).is_dir())

    def test_odds_to_probability(self):
        """Test odds to probability conversion."""
        self.assertAlmostEqual(
            self.processor.odds_to_probability(1), 0.5)
        self.assertTrue(np.isnan(
            self.processor.odds_to_probability("N/A")))
        self.assertTrue(np.isnan(
            self.processor.odds_to_probability(-1)))

    def test_process_betting_odds(self):
        """Test processing betting odds from DataFrame."""
        # Create test data
        test_data = {
            'Driver': ['Max Verstappen', 'Lewis Hamilton'],
            'Provider1': [1.5, 2.0],
            'Provider2': [1.8, 2.2]
        }
        
        # Create race directory and save test data
        race_dir = self.processor.get_race_dir(self.test_race)
        test_file = race_dir / f"{self.test_category}_odds.csv"
        pd.DataFrame(test_data).to_csv(test_file, index=False)

        # Process the odds
        df = self.processor.process_betting_odds(self.test_race, self.test_category)
        
        # Check if probability columns were created
        self.assertIn('Provider1_probability', df.columns)
        self.assertIn('Provider2_probability', df.columns)

    def test_save_processed_data(self):
        """Test saving processed data to CSV."""
        # Create test data
        test_data = {
            'Driver': ['Max Verstappen', 'Lewis Hamilton'],
            'normalized_probability': [60, 40],
            'xPts': [6, 4]
        }
        self.processor.df = pd.DataFrame(test_data)

        # Save the data
        self.processor.save_processed_data(self.test_race, self.test_category)

        # Check if file exists and contains correct data
        expected_file = self.processor.get_race_dir(self.test_race) / f"{self.test_category}_processed.csv"
        self.assertTrue(expected_file.exists())
        saved_df = pd.read_csv(expected_file)
        pd.testing.assert_frame_equal(saved_df, self.processor.df)

    def test_file_not_found(self):
        """Test handling of non-existent input file."""
        with self.assertRaises(FileNotFoundError):
            self.processor.process_betting_odds("nonexistent-race", "nonexistent-category")

    def test_calculate_average_probabilities(self):
        """Test calculation of average probabilities."""
        # Create test data
        test_data = {
            'Driver': ['Max Verstappen', 'Lewis Hamilton'],
            'Provider1_probability': [0.4, 0.3],
            'Provider2_probability': [0.5, 0.2]
        }
        self.processor.df = pd.DataFrame(test_data)

        df = self.processor.calculate_average_probabilities()
        
        # Check if average probability is correct
        self.assertAlmostEqual(df['average_probability'].iloc[0], 0.45)
        self.assertAlmostEqual(df['average_probability'].iloc[1], 0.25)

    def test_normalize_probabilities(self):
        """Test normalization of probabilities."""
        # Create test data
        test_data = {
            'Driver': ['Max Verstappen', 'Lewis Hamilton'],
            'average_probability': [0.4, 0.2]
        }
        self.processor.df = pd.DataFrame(test_data)

        df = self.processor.normalize_probabilities()
        
        # Check if probabilities sum to 100
        self.assertAlmostEqual(df['normalized_probability'].sum(), 100)

    def test_calculate_expected_points(self):
        """Test calculation of expected points."""
        # Create test data
        test_data = {
            'Driver': ['Max Verstappen', 'Lewis Hamilton'],
            'normalized_probability': [60, 40]
        }
        self.processor.df = pd.DataFrame(test_data)

        df = self.processor.calculate_expected_points()
        
        # Check if expected points are calculated correctly
        max_xpts = 60 * self.test_odds['Max Verstappen'] / 100
        self.assertAlmostEqual(df[df['Driver'] == 'Max Verstappen']['xPts'].iloc[0], max_xpts)

    def test_get_driver_analysis(self):
        """Test getting driver analysis."""
        # Create test data
        test_data = {
            'Driver': ['Max Verstappen', 'Lewis Hamilton'],
            'normalized_probability': [60, 40],
            'xPts': [6, 4]
        }
        self.processor.df = pd.DataFrame(test_data)

        analysis = self.processor.get_driver_analysis('Max Verstappen')
        
        self.assertEqual(analysis['driver'], 'Max Verstappen')
        self.assertEqual(analysis['normalized_probability'], 60)
        self.assertEqual(analysis['expected_points'], 6)

    def test_get_top_drivers(self):
        """Test getting top drivers."""
        # Create test data
        test_data = {
            'Driver': ['Max Verstappen', 'Lewis Hamilton', 'Charles Leclerc'],
            'normalized_probability': [50, 30, 20],
            'xPts': [5, 3, 2]
        }
        self.processor.df = pd.DataFrame(test_data)

        top_2 = self.processor.get_top_drivers(2)
        
        self.assertEqual(len(top_2), 2)
        self.assertEqual(top_2.iloc[0]['Driver'], 'Max Verstappen')

if __name__ == '__main__':
    unittest.main()