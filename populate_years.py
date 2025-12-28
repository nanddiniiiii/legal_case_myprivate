import psycopg2
import re

try:
    conn = psycopg2.connect(
        dbname="legal_search",
        user="postgres",
        password="12345",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("EXTRACTING YEARS FROM CASE NUMBERS")
    print("="*60)
    
    # Get all cases
    cursor.execute("SELECT id, case_number FROM cases WHERE year IS NULL")
    cases = cursor.fetchall()
    
    print(f"\nFound {len(cases)} cases with NULL year")
    print("Extracting years from case numbers...\n")
    
    updated = 0
    failed = 0
    year_counts = {}
    
    for case_id, case_number in cases:
        # Extract year from case_number (format: IK-XXXXXX-YYYY)
        match = re.search(r'-(\d{4})$', case_number)
        if match:
            year = int(match.group(1))
            
            # Update the year column
            cursor.execute("UPDATE cases SET year = %s WHERE id = %s", (year, case_id))
            updated += 1
            
            # Track year distribution
            year_counts[year] = year_counts.get(year, 0) + 1
            
            if updated % 500 == 0:
                print(f"  Updated {updated} cases...")
        else:
            failed += 1
            if failed <= 5:
                print(f"  ⚠️ Could not extract year from: {case_number}")
    
    conn.commit()
    
    print(f"\n✅ Successfully updated {updated} cases")
    if failed > 0:
        print(f"⚠️  Failed to extract year from {failed} cases")
    
    print("\n" + "="*60)
    print("YEAR DISTRIBUTION AFTER UPDATE:")
    print("="*60)
    
    for year in sorted(year_counts.keys(), reverse=True):
        count = year_counts[year]
        print(f"  Year {year}: {count:,} cases")
    
    print("\n" + "="*60)
    print("✅ Year column populated successfully!")
    print("="*60)
    print("\nNow search with year filters will work!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
