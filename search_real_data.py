import psycopg2

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
    print("SEARCHING FOR CASES WITH ACTUAL DATA")
    print("="*60)
    
    # Search for the case we saw in results
    cursor.execute("""
        SELECT case_number, title, parties, judgment_date, 
               LEFT(description, 200) as desc_preview
        FROM cases 
        WHERE parties ILIKE '%Vivek Kumar%'
        OR description ILIKE '%Vivek Kumar%'
        LIMIT 5
    """)
    
    print("\nSearching for 'Vivek Kumar' case:")
    results = cursor.fetchall()
    if results:
        for case_num, title, parties, date, desc in results:
            print(f"\n  Case: {case_num}")
            print(f"  Title: {title}")
            print(f"  Parties: {parties}")
            print(f"  Date: {date}")
            print(f"  Description: {desc[:100]}...")
    else:
        print("  Not found!")
    
    # Count how many have actual party names
    cursor.execute("""
        SELECT COUNT(*) FROM cases 
        WHERE parties != 'Unknown' AND parties IS NOT NULL
    """)
    count = cursor.fetchone()[0]
    print(f"\n\nCases with non-Unknown parties: {count:,}")
    
    # Show some cases with kidnapping in description
    print("\n" + "="*60)
    print("CASES WITH 'KIDNAPPING' IN DESCRIPTION:")
    print("="*60)
    cursor.execute("""
        SELECT case_number, title, parties, 
               LEFT(description, 150) as desc_preview
        FROM cases 
        WHERE description ILIKE '%kidnapping%'
        LIMIT 3
    """)
    
    for case_num, title, parties, desc in cursor.fetchall():
        print(f"\n  Case: {case_num}")
        print(f"  Title: {title}")
        print(f"  Parties: {parties}")
        print(f"  Description: {desc}...")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
