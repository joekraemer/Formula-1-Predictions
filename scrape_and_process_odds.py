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
        "japanese-grand-prix",
    ]
    
    CATEGORIES = [
        "winner",
        "fastest-qualifier",
        "podium-finish",
        "1st-driver-retirement",
        "safety-car",
        "fastest-lap"
    ]
    
    # Game odds for different categories
    GAME_ODDS = {
        "fastest-qualifier": {
            "Lando Norris": 5,
            "Oscar Piastri": 6,
            "Max Verstappen": 12,
            "Charles Leclerc": 15,
            "Lewis Hamilton": 20,
            "George Russell": 18,
            "Kimi Antonelli": 28,
            "Yuki Tsunoda": 30,
            "Carlos Sainz": 40,
            "Alex Albon": 40,
            "Liam Lawson": 45,
            "Pierre Gasly": 50,
            "Fernando Alonso": 50,
            "Isack Hadjar": 50,
            "Lance Stroll": 55,
            "Nico Hulkenberg": 58,
            "Gabriel Bortoleto": 60,
            "Jack Doohan": 60,
            "Esteban Ocon": 58,
            "Oliver Bearman": 60,
        },
        "podium-finish": {
            "Lando Norris": 5,
            "Charles Leclerc": 12,
            "Oscar Piastri": 6,
            "Max Verstappen": 10,
            "George Russell": 15,
            "Lewis Hamilton": 16,
            "Carlos Sainz": 30,
            "Kimi Antonelli": 25,
            "Alex Albon": 30,
            "Yuki Tsunoda": 20,
            "Isack Hadjar": 45,
            "Fernando Alonso": 50,
            "Pierre Gasly": 50,
            "Liam Lawson": 35,
            "Nico Hulkenberg": 55,
            "Lance Stroll": 50,
            "Gabriel Bortoleto": 60,
            "Jack Doohan": 60,
            "Esteban Ocon": 55,
            "Oliver Bearman": 55,
        },
        "safety-car": {
            "Yes" : 10,
            "No Retirement" : 20
        },
        "fastest-lap": {
            "Lando Norris": 5,
            "Max Verstappen": 10,
            "Charles Leclerc": 18,
            "Oscar Piastri": 12,
            "George Russell": 21,
            "Lewis Hamilton": 16,
            "Carlos Sainz": 42,
            "Kimi Antonelli": 30,
            "Alex Albon": 42,
            "Yuki Tsunoda": 35,
            "Isack Hadjar": 45,
            "Fernando Alonso": 50,
            "Pierre Gasly": 55,
            "Liam Lawson": 50,
            "Nico Hulkenberg": 55,
            "Lance Stroll": 55,
            "Gabriel Bortoleto": 60,
            "Jack Doohan": 60,
            "Esteban Ocon": 60,
            "Oliver Bearman": 60,
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