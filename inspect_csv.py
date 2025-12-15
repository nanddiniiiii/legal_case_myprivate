import pandas as pd

# --- This script will open your CSV and print its column headers ---

# The path to your CSV file
FILEPATH_KAGGLE = r"D:\OneDrive - Amrita vishwa vidyapeetham\Desktop\dbms_proj\archive (2)\judgments.csv"

try:
    print(f"--- Reading columns from: {FILEPATH_KAGGLE} ---")
    
    # Read only the first row to get the header without loading the whole file
    df_header = pd.read_csv(FILEPATH_KAGGLE, nrows=0)
    
    print("\n✅ SUCCESS! Found the following columns in your CSV file:")
    for col in df_header.columns:
        print(f"  - '{col}'")
        
    print("\n--- NEXT STEP ---")
    print("Please use these exact column names to fix the df.rename() line in your 'import_data.py' script.")

except FileNotFoundError:
    print(f"❌ ERROR: Could not find the CSV file at the specified path.")
except Exception as e:
    print(f"❌ AN ERROR OCCURRED: {e}")



