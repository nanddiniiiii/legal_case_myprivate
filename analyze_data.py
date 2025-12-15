import pandas as pd

# Load the CSV to see what real data we have
df = pd.read_csv('archive (2)/judgments.csv')

print("=== ANALYZING ORIGINAL CSV DATA ===")
print(f"Total cases in CSV: {len(df)}")
print(f"Columns: {list(df.columns)}")

print("\n=== FIRST 5 CASES ===")
for i in range(5):
    pet = df.iloc[i]['pet'] if pd.notna(df.iloc[i]['pet']) else 'Unknown'
    res = df.iloc[i]['res'] if pd.notna(df.iloc[i]['res']) else 'Unknown'
    print(f"{i+1}. {pet} vs {res}")

print("\n=== SEARCHING FOR SPECIFIC TERMS ===")
# Check for stampede
stampede_mask = df['pet'].str.contains('stampede', case=False, na=False) | df['res'].str.contains('stampede', case=False, na=False)
print(f"Cases containing 'stampede': {stampede_mask.sum()}")

# Check for theft
theft_mask = df['pet'].str.contains('theft', case=False, na=False) | df['res'].str.contains('theft', case=False, na=False)
print(f"Cases containing 'theft': {theft_mask.sum()}")

# Check for murder
murder_mask = df['pet'].str.contains('murder', case=False, na=False) | df['res'].str.contains('murder', case=False, na=False)
print(f"Cases containing 'murder': {murder_mask.sum()}")

if stampede_mask.sum() > 0:
    print("\n=== STAMPEDE CASES FOUND ===")
    stampede_cases = df[stampede_mask]
    for idx, row in stampede_cases.head(3).iterrows():
        print(f"- {row['pet']} vs {row['res']}")