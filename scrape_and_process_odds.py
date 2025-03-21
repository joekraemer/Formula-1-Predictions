from f1_odds_scraper import F1OddsScraper
from f1_odds_processor import F1OddsProcessor
from pathlib import Path
from datetime import datetime
import sys
import time

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
        # "winner",
        "fastest-qualifier",
        # "podium-finish",
    ]
    
    # Game odds for different categories
    GAME_ODDS = {
        "fastest-qualifier": {
            "Lando Norris": 10,
            "Charles Leclerc": 12,
            "Oscar Piastri": 14,
            "Max Verstappen": 12,
            "George Russell": 16,
            "Lewis Hamilton": 14,
            "Carlos Sainz": 28,
            "Kimi Antonelli": 18,
            "Alex Albon": 32,
            "Yuki Tsunoda": 40,
            "Isack Hadjar": 60,
            "Fernando Alonso": 43,
            "Pierre Gasly": 40,
            "Liam Lawson": 20,
            "Nico Hulkenberg": 60,
            "Lance Stroll": 46,
            "Gabriel Bortoleto": 60,
            "Jack Doohan": 56,
            "Esteban Ocon": 56,
            "Oliver Bearman": 45,
        },
        "podium-finish": {
            "Lando Norris": 10,
            "Charles Leclerc": 12,
            "Oscar Piastri": 14,
            "Max Verstappen": 12,
            "George Russell": 16,
            "Lewis Hamilton": 14,
            "Carlos Sainz": 28,
            "Kimi Antonelli": 18,
            "Alex Albon": 32,
            "Yuki Tsunoda": 40,
            "Isack Hadjar": 60,
            "Fernando Alonso": 43,
            "Pierre Gasly": 40,
            "Liam Lawson": 20,
            "Nico Hulkenberg": 60,
            "Lance Stroll": 46,
            "Gabriel Bortoleto": 60,
            "Jack Doohan": 56,
            "Esteban Ocon": 56,
            "Oliver Bearman": 45,
        }
    }
    
    try:
        processor = F1OddsProcessor(data_dir=str(DATA_DIR), year=YEAR)
        
        # Process each race
        for race in RACES:
            print(f"\nProcessing race: {race}")
            print("-" * 30)
            
            # Create a single scraper instance for all categories
            with F1OddsScraper(race=race, data_dir=str(DATA_DIR), year=YEAR, headless=False) as scraper:
                for category in CATEGORIES:
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
                            
                            # Display top 5 drivers
                            top_drivers = processor.get_top_drivers(5)
                            print(f"\nTop 5 drivers for {category}:")
                            print(top_drivers.to_string(index=False))
                        else:
                            print(f"No game odds defined for {category}")
                        
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