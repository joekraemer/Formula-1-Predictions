from f1_odds_scraper import F1OddsScraper
from f1_odds_processor import F1OddsProcessor
from pathlib import Path
from datetime import datetime
import sys

def main():
    # Configuration
    DATA_DIR = Path("data")
    YEAR = datetime.now().year  # Current year, or specify manually
    
    print(f"\nStarting F1 odds scraping and processing for {YEAR}")
    print("=" * 50)
    
    # Create data directory if it doesn't exist
    DATA_DIR.mkdir(exist_ok=True)
    
    # Define races and categories to scrape
    # Using exact URLs from oddschecker.com
    RACES = [
        "chinese-grand-prix-2024",  # Make sure to use the exact race name from oddschecker URL
    ]
    
    CATEGORIES = [
        "race-winner",  # Start with simpler categories first
        "qualifying",
        "podium-finish",
        # "top-6-finish",  # Commented out for initial testing
        # "top-10-finish",
    ]
    
    # Game odds for different categories
    GAME_ODDS = {
    "qualifying": {"Lando Norris": 10,
                   "Charles Leclerc": 12,
                   "Oscar Piastri": 14,
                   "Max Verstappen": 12,
                   "George Russell":  16,
                   "Lewis Hamilton":  14,
                   "Carlos Sainz":  28,
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

            "podium-finish": {"Lando Norris": 10,
                    "Charles Leclerc": 12,
                    "Oscar Piastri": 14,
                    "Max Verstappen": 12,
                    "George Russell":  16,
                    "Lewis Hamilton":  14,
                    "Carlos Sainz":  28,
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
            
            # Initialize scraper with race
            scraper = F1OddsScraper(race=race, data_dir=str(DATA_DIR), year=YEAR)
            
            # Scrape odds for all categories
            print("Scraping odds...")
            success_count = 0
            with scraper:  # Using context manager to handle driver setup/cleanup
                results = scraper.scrape_all_categories(CATEGORIES)
                
                if not results:
                    print(f"No odds data found for {race}")
                    continue
                
                for category, df in results.items():
                    if not df.empty:
                        success_count += 1
            
            if success_count == 0:
                print("Failed to scrape any categories successfully")
                continue
                
            print(f"Successfully scraped odds for {success_count} out of {len(CATEGORIES)} categories")
            
            # Process odds for each category
            for category, df in results.items():
                if df.empty:
                    print(f"\nSkipping {category} - no data available")
                    continue
                    
                try:
                    print(f"\nProcessing {category}...")
                    
                    # Set appropriate game odds for the category
                    if category in GAME_ODDS:
                        processor.set_game_odds(GAME_ODDS[category])
                    else:
                        print(f"Warning: No game odds defined for {category}")
                        continue
                    
                    # Process the odds
                    df = processor.process_betting_odds(race, category)
                    df = processor.calculate_average_probabilities()
                    df = processor.normalize_probabilities()
                    df = processor.calculate_expected_points()
                    
                    # Save processed results
                    processor.save_processed_data(race, category)
                    
                    # Get and display top 5 drivers
                    top_drivers = processor.get_top_drivers(5)
                    print(f"\nTop 5 drivers for {category}:")
                    print(top_drivers.to_string(index=False))
                    
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