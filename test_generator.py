import pandas as pd
import random

print("Testing case generation logic...")
print("=" * 50)

# Read CSV
df = pd.read_csv('archive (2)/judgments.csv')
print(f"Total cases in CSV: {len(df)}")

def analyze_party_type(party_name):
    """Determine the type of party based on name"""
    if pd.isna(party_name):
        return 'individual'
    
    party_lower = str(party_name).lower()
    
    if any(keyword in party_lower for keyword in ['state of', 'union of india', 'government']):
        return 'government'
    if any(keyword in party_lower for keyword in ['ltd', 'limited', 'pvt', 'corporation', 'company']):
        return 'company'
    if any(keyword in party_lower for keyword in ['university', 'college', 'hospital']):
        return 'institution'
    if any(keyword in party_lower for keyword in ['association', 'union', 'society']):
        return 'organization'
    
    return 'individual'

def determine_case_category(pet_type, res_type, pet_name, res_name):
    """Determine case category based on parties"""
    pet_lower = str(pet_name).lower() if not pd.isna(pet_name) else ''
    res_lower = str(res_name).lower() if not pd.isna(res_name) else ''
    
    if 'state of' in pet_lower or 'state of' in res_lower:
        if pet_type == 'individual' or res_type == 'individual':
            return 'criminal'
    
    if pet_type == 'organization' and res_type == 'government':
        return 'constitutional'
    
    if pet_type == 'company' and res_type == 'company':
        return 'commercial'
    
    return 'civil'

# Test with first 10 cases
print("\nAnalyzing first 10 cases:")
print("=" * 50)

for idx in range(10):
    row = df.iloc[idx]
    pet = row['pet']
    res = row['res']
    
    pet_type = analyze_party_type(pet)
    res_type = analyze_party_type(res)
    category = determine_case_category(pet_type, res_type, pet, res)
    
    print(f"\n{idx + 1}. Case: {row['case_no']}")
    print(f"   Petitioner: {pet} ({pet_type})")
    print(f"   Respondent: {res} ({res_type})")
    print(f"   Category: {category}")

print("\n" + "=" * 50)
print("✅ Test completed successfully!")
