import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime

class F1OddsProcessor:
    """A class to process and analyze F1 betting odds."""

    def __init__(self, data_dir: str = "data", year: Optional[int] = None):
        """
        Initialize the F1OddsProcessor.

        Args:
            data_dir (str): Base directory for data
            year (int, optional): Year for the F1 season. Defaults to current year.
        """
        self.data_dir = Path(data_dir)
        self.year = year or datetime.now().year
        self.year_dir = self.data_dir / str(self.year)
        self.df = None
        self.game_odds = {}
        self.setup_directories()

    def setup_directories(self):
        """Set up the directory structure for data storage."""
        self.data_dir.mkdir(exist_ok=True)
        self.year_dir.mkdir(exist_ok=True)

    def get_race_dir(self, race: str) -> Path:
        """
        Get the directory path for a specific race.

        Args:
            race (str): Race name (e.g., 'australian-gp')

        Returns:
            Path: Path to the race directory
        """
        race_dir = self.year_dir / race
        race_dir.mkdir(exist_ok=True)
        return race_dir

    def set_game_odds(self, odds_dict: Dict[str, float]) -> None:
        """
        Set the game odds for drivers.

        Args:
            odds_dict (Dict[str, float]): Dictionary mapping driver names to their odds
        """
        self.game_odds = odds_dict

    @staticmethod
    def odds_to_probability(odds: Union[str, float]) -> float:
        """
        Convert fractional odds to implied probability.

        Args:
            odds (Union[str, float]): The odds value to convert

        Returns:
            float: The calculated probability
        """
        try:
            if odds == "N/A" or pd.isna(odds):
                return np.nan
            odds = float(odds)
            if odds <= 0:
                return np.nan
            return 1 / (odds + 1)
        except:
            return np.nan

    def process_betting_odds(self, race: str, category: str) -> pd.DataFrame:
        """
        Process betting odds from a CSV file in the race directory.

        Args:
            race (str): Race name
            category (str): Category of odds (e.g., 'qualifying', 'race-winner')

        Returns:
            pd.DataFrame: Processed DataFrame with odds and probabilities
        """
        # Construct file path
        race_dir = self.get_race_dir(race)
        file_path = race_dir / f"{category}_odds.csv"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Odds file not found: {file_path}")

        # Read the CSV file into a DataFrame
        self.df = pd.read_csv(file_path)

        # Get the provider columns (all columns except "Driver")
        provider_columns = [col for col in self.df.columns if col != 'Driver']

        # Convert each provider's odds to probabilities
        for provider in provider_columns:
            self.df[provider + '_probability'] = self.df[provider].apply(self.odds_to_probability)

        return self.df

    def save_processed_data(self, race: str, category: str) -> None:
        """
        Save processed DataFrame to a CSV file in the race directory.

        Args:
            race (str): Race name
            category (str): Category of odds
        """
        if self.df is None:
            raise ValueError("No data to save. Process betting odds first.")

        race_dir = self.get_race_dir(race)
        filepath = race_dir / f"{category}_processed.csv"
        self.df.to_csv(filepath, index=False)

    def calculate_average_probabilities(self) -> pd.DataFrame:
        """
        Calculate average probabilities across all providers.

        Returns:
            pd.DataFrame: DataFrame with average probabilities added
        """
        if self.df is None:
            raise ValueError("No data loaded. Call process_betting_odds first.")

        # Get the probability columns
        probability_columns = [col for col in self.df.columns if col.endswith('_probability')]

        # Calculate average probabilities
        self.df['average_probability'] = self.df[probability_columns].mean(axis=1, skipna=True)
        return self.df

    def normalize_probabilities(self) -> pd.DataFrame:
        """
        Normalize probabilities to sum to 100%.

        Returns:
            pd.DataFrame: DataFrame with normalized probabilities added
        """
        if self.df is None:
            raise ValueError("No data loaded. Call process_betting_odds first.")

        if 'average_probability' not in self.df.columns:
            self.calculate_average_probabilities()

        # Normalize probabilities
        total_prob = self.df['average_probability'].sum()
        self.df['normalized_probability'] = (self.df['average_probability'] / total_prob) * 100
        return self.df

    def calculate_expected_points(self, points_column_name: str = 'game_points') -> pd.DataFrame:
        """
        Calculate expected points based on normalized probabilities and game odds.

        Args:
            points_column_name (str): Name of the column to store points

        Returns:
            pd.DataFrame: DataFrame with expected points calculations
        """
        if self.df is None:
            raise ValueError("No data loaded. Call process_betting_odds first.")

        if not self.game_odds:
            raise ValueError("Game odds not set. Call set_game_odds first.")

        # Add game points and calculate expected points
        self.df[points_column_name] = self.df['Driver'].map(self.game_odds)
        self.df['xPts'] = self.df['normalized_probability'] * self.df[points_column_name] / 100

        # Sort by normalized probability
        self.df = self.df.sort_values(by='normalized_probability', ascending=False)
        return self.df

    def get_driver_analysis(self, driver_name: str) -> Dict:
        """
        Get detailed analysis for a specific driver.

        Args:
            driver_name (str): Name of the driver to analyze

        Returns:
            Dict: Dictionary containing driver analysis
        """
        if self.df is None:
            raise ValueError("No data loaded. Process betting odds first.")

        driver_data = self.df[self.df['Driver'] == driver_name]
        if driver_data.empty:
            raise ValueError(f"Driver {driver_name} not found in data")

        return {
            'driver': driver_name,
            'normalized_probability': driver_data['normalized_probability'].iloc[0],
            'expected_points': driver_data['xPts'].iloc[0] if 'xPts' in self.df.columns else None,
            'game_odds': self.game_odds.get(driver_name),
            'provider_probabilities': {
                col.replace('_probability', ''): driver_data[col].iloc[0]
                for col in driver_data.columns if col.endswith('_probability')
                and col != 'normalized_probability'
            }
        }

    def get_top_drivers(self, n: int = 5) -> pd.DataFrame:
        """
        Get the top N drivers by normalized probability.

        Args:
            n (int): Number of drivers to return

        Returns:
            pd.DataFrame: Top N drivers with their statistics
        """
        if self.df is None:
            raise ValueError("No data loaded. Process betting odds first.")

        return self.df.head(n)[['Driver', 'normalized_probability', 'xPts']]