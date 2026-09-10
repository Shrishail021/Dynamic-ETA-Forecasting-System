import pandas as pd
import numpy as np

csv_path = r'data\railway_eta_dataset\data\synthetic_training_dataset_FINAL_clean.csv'
print(f"Loading {csv_path}...")
df = pd.read_csv(csv_path)

print("\n" + "=" * 60)
print(" DATASET OVERVIEW ")
print("=" * 60)
print(f"Total rows: {len(df):,}")
print(f"Total columns: {len(df.columns)}")
print("Columns:", list(df.columns))

print("\n" + "=" * 60)
print(" UNIQUE ENTITIES & TEMPORAL RANGE ")
print("=" * 60)
print(f"Unique trains: {df['train_no'].nunique()}")
print("Top 10 train numbers:", df['train_no'].unique()[:10].tolist())
print(f"Unique stations: {df['station_code'].nunique()}")
print(f"Date range: {df['journey_date'].min()} to {df['journey_date'].max()}")
print(f"Days of week represented: {df['day_of_week'].unique().tolist()}")
print(f"Seasons: {df['season'].unique().tolist()}")

print("\n" + "=" * 60)
print(" MISSING / NULL VALUES ")
print("=" * 60)
nulls = df.isnull().sum()
null_cols = nulls[nulls > 0]
if len(null_cols) == 0:
    print("Zero missing values! Clean dataset.")
else:
    for col, count in null_cols.items():
        print(f"  - {col}: {count:,} missing ({count/len(df)*100:.1f}%)")

print("\n" + "=" * 60)
print(" TARGET & FEATURE DISTRIBUTIONS ")
print("=" * 60)
print("Target ('simulated_delay_min') summary statistics:")
print(df['simulated_delay_min'].describe().to_string())

if 'simulated_cancelled_flag' in df.columns:
    cancelled_count = df['simulated_cancelled_flag'].sum()
    print(f"\nCancelled journeys flag: {cancelled_count:,} ({cancelled_count/len(df)*100:.2f}%)")

print("\nSample rows:")
print(df[['train_no', 'station_code', 'seq', 'distance_km', 'previous_station_delay', 'simulated_delay_min']].head(5).to_string())
