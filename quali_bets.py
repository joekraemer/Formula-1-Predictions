import pandas as pd
import numpy as np

# Function to convert fractional odds to implied probability


def odds_to_probability(odds):
    try:
        # If odds are in the form "N/A" or empty, we return NaN
        if odds == "N/A" or pd.isna(odds):
            return np.nan
        # Convert odds to float and calculate implied probability
        odds = float(odds)
        if odds <= 0:
            return np.nan
        return 1 / (odds + 1)
    except:
        return np.nan

# Function to read the CSV and convert odds to probabilities


def process_betting_odds(csv_file):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(csv_file)

    # Get the provider columns (all columns except "Driver")
    provider_columns = [col for col in df.columns if col != 'Driver']

    # Convert each provider's odds to probabilities
    for provider in provider_columns:
        df[provider + '_probability'] = df[provider].apply(odds_to_probability)

    return df

# Function to calculate the average probability for each driver


def calculate_average_probabilities(df):
    # Get the probability columns (all columns ending with '_probability')
    probability_columns = [
        col for col in df.columns if col.endswith('_probability')]

    # Calculate the average of the probabilities across the providers
    df['average_probability'] = df[probability_columns].mean(
        axis=1, skipna=True)
    return df

# Function to normalize the probabilities so that they sum to 100%


def normalize_probabilities(df):
    # Normalize the average probabilities so that the sum is 100%
    total_prob = df['average_probability'].sum()
    df['normalized_probability'] = (
        df['average_probability'] / total_prob) * 100
    return df


# Game Odds:
quali_game_odds = {"Lando Norris": 10,
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

# Game Odds:
podium_game_odds = {"Lando Norris": 10,
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


# Quali
csv_file = "quali_driver_odds.csv"  # replace with your actual file path
df = process_betting_odds(csv_file)
df = calculate_average_probabilities(df)
df = normalize_probabilities(df)

# Calculate variance across the probability columns (not the raw odds)
df['quali_game_points'] = df['Driver'].map(quali_game_odds)
df['quali xPts'] = df['normalized_probability'] * df['quali_game_points'] / 100

# Sort the DataFrame by 'normalized_probability' in descending order (highest first)
df = df.sort_values(by='normalized_probability', ascending=False)

# Display the final DataFrame with normalized probabilities
print("\n\n QUALI POINTS \n\n")
print(df[['Driver', 'normalized_probability', 'quali xPts']])


# Podium
csv_file = "podium_odds.csv"  # replace with your actual file path
df = process_betting_odds(csv_file)
df = calculate_average_probabilities(df)
df = normalize_probabilities(df)

# Calculate variance across the probability columns (not the raw odds)
df['game_points'] = df['Driver'].map(podium_game_odds)
df['xPts'] = df['normalized_probability'] * df['game_points'] / 100

# Sort the DataFrame by 'normalized_probability' in descending order (highest first)
df = df.sort_values(by='normalized_probability', ascending=False)

# Display the final DataFrame with normalized probabilities
print("\n\n PODIUM POINTS \n\n")
print(df[['Driver', 'normalized_probability', 'xPts']])
