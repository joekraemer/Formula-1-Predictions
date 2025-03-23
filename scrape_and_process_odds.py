from f1_odds_scraper import F1OddsScraper
from f1_odds_processor import F1OddsProcessor
from pathlib import Path
from datetime import datetime
import sys
import time
import pandas as pd

def main():
    # Configuration
    DATA_DIR = Path("data")
    YEAR = datetime.now().year
    
    print(f"\nStarting F1 odds scraping and processing for {YEAR}")
    print("=" * 50)
    
    # Create data directory if it doesn't exist
    DATA_DIR.mkdir(exist_ok=True)
    
    # Define races and categories to scrape
    RACES = [
        "chinese-grand-prix",
    ]
    
    CATEGORIES = [
        "winner",
        "fastest-qualifier",
        "podium-finish",
        "1st-driver-retirement",
        "safety-car"
    ]
    
    # Game odds for different categories
    GAME_ODDS = {
        "fastest-qualifier": {
            "Lando Norris": 5,
            "Oscar Piastri": 8,
            "Charles Leclerc": 10,
            "Lewis Hamilton": 20,
            "Carlos Sainz": 28,
            "George Russell": 18,
            "Kimi Antonelli": 25,
            "Alex Albon": 34,
            "Yuki Tsunoda": 30,
            "Isack Hadjar": 40,
            "Pierre Gasly": 40,
            "Max Verstappen": 12,
            "Liam Lawson": 36,
            "Nico Hulkenberg": 55,
            "Gabriel Bortoleto": 55,
            "Fernando Alonso": 44,
            "Lance Stroll": 46,
            "Jack Doohan": 54,
            "Esteban Ocon": 60,
            "Oliver Bearman": 60,
        },
        "podium-finish": {
            "Lando Norris": 5,
            "Charles Leclerc": 10,
            "Oscar Piastri": 6,
            "Max Verstappen": 7,
            "George Russell": 13,
            "Lewis Hamilton": 16,
            "Carlos Sainz": 25,
            "Kimi Antonelli": 20,
            "Alex Albon": 25,
            "Yuki Tsunoda": 30,
            "Isack Hadjar": 45,
            "Fernando Alonso": 42,
            "Pierre Gasly": 35,
            "Liam Lawson": 30,
            "Nico Hulkenberg": 45,
            "Lance Stroll": 42,
            "Gabriel Bortoleto": 45,
            "Jack Doohan": 48,
            "Esteban Ocon": 55,
            "Oliver Bearman": 60,
        },
        "safety-car": {
            "Yes" : 1.5,
            "No Retirement" : 2.5
        }

    }
    
    try:
        processor = F1OddsProcessor(data_dir=str(DATA_DIR), year=YEAR)
        
        # Process each race
        for race in RACES:
            print(f"\nProcessing race: {race}")
            print("-" * 30)
            
            # Create a single scraper instance for all categories
            for category in CATEGORIES:
                with F1OddsScraper(race=race, data_dir=str(DATA_DIR), year=YEAR, headless=True) as scraper:
                    print(f"\nScraping {category}...")
                    try:
                        df = scraper.scrape_odds(category)
                        if df.empty:
                            print(f"No data found for {category}")
                            continue
                            
                        print(f"Successfully scraped {category}")
                        
                        # Process the odds if we have game odds for this category
                        if category in GAME_ODDS:
                            print(f"\nProcessing {category}...")
                            processor.set_game_odds(GAME_ODDS[category])
                            df = processor.process_betting_odds(race, category)
                            df = processor.calculate_average_probabilities()
                            df = processor.normalize_probabilities()
                            df = processor.calculate_expected_points()
                            processor.save_processed_data(race, category)
                            
                            top_drivers = processor.get_top_drivers(20)
                            print(f"\nTop 20 for {category}:")
                            print(top_drivers.to_string(index=False))
                        else:
                            print(f"\nProcessing {category} (without game odds)...")
                            df = processor.process_betting_odds(race, category)
                            df = processor.calculate_average_probabilities()
                            df = processor.normalize_probabilities()
                            processor.save_processed_data(race, category)
                            
                            # Display top 20 by normalized probability
                            print(f"\nTop 20 for {category}:")
                            # Get the first column name (could be Driver, Team, etc.)
                            first_col = df.columns[0]
                            top = df.sort_values('normalized_probability', ascending=False).head(20)[[first_col, 'normalized_probability']]
                            print(top.to_string(index=False))
                        
                        # Add a small delay between categories
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"Error processing {category}: {str(e)}")
                        continue
        
        print("\nProcessing complete!")
        print("=" * 50)
    
    except Exception as e:
        print(f"\nError in main process: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 