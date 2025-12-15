import psycopg2

print("--- Verifying Content Directly from Database ---")

try:
    # Ensure these EXACTLY match your generator and API
    conn = psycopg2.connect(
        dbname="legal_search", 
        user="postgres", 
        password="12345", 
        host="localhost", 
        port="5432"
    )
    cur = conn.cursor()
    print("✅ Database connection successful.")

    # 1. Check total count
    cur.execute("SELECT COUNT(*) FROM cases")
    count = cur.fetchone()[0]
    print(f"\nTotal cases found: {count}")
    if count == 0:
        print("❌ ERROR: The 'cases' table is empty! The generator likely failed.")
        conn.close()
        exit()
    elif count < 47400:
         print(f"⚠️ WARNING: Expected ~47400 cases, but only found {count}. Generator might have stopped early.")


    # 2. Check for UNIQUE descriptions
    cur.execute("SELECT COUNT(DISTINCT description) FROM cases")
    unique_count = cur.fetchone()[0]
    print(f"\nUnique descriptions found: {unique_count}")
    if unique_count < 300: # Expecting around 330 unique ones
        print(f"❌ ERROR: Low unique descriptions ({unique_count}). Likely populated with duplicate or template data.")
    elif unique_count > 400: # Should be close to 330
         print(f"✅ Found {unique_count} unique descriptions (Expected ~330).")
    else:
        print(f"✅ Found {unique_count} unique descriptions (Looks good, expected ~330).")


    # 3. Sample descriptions from different categories
    print("\n--- Sampling Descriptions ---")
    categories_to_check = ['criminal', 'civil', 'family', 'property', 'commercial']
    all_descriptions_same = True
    first_desc = None
    
    for category in categories_to_check:
        cur.execute("SELECT description FROM cases WHERE category = %s LIMIT 3", (category,))
        results = cur.fetchall()
        print(f"\nCategory: {category} (Sample of {len(results)})")
        if not results:
            print("  No cases found for this category.")
            continue
            
        desc_set_cat = set()
        for i, (desc,) in enumerate(results):
            print(f"  Sample {i+1}: {desc[:150]}...") # Print first 150 chars
            desc_set_cat.add(desc)
            if first_desc is None:
                first_desc = desc
            elif desc != first_desc:
                all_descriptions_same = False

        if len(desc_set_cat) < len(results) and len(results) > 1:
             print(f"  ⚠️ WARNING: Found duplicate descriptions within this category sample.")
        elif len(results) > 1:
             print(f"  ✅ Descriptions in this sample appear unique.")


    if all_descriptions_same and count > 1 and first_desc is not None:
         print("\n❌ CRITICAL ERROR: All sampled descriptions across categories appear to be identical!")
    elif not all_descriptions_same:
         print("\n✅ Descriptions sampled across categories appear varied.")


    conn.close()
    print("\n--- Verification Complete ---")

except Exception as e:
    print(f"❌ DATABASE ERROR: {e}")
    print("   Check connection details (dbname, user, password, host, port)")
    print("   Ensure PostgreSQL server is running and the 'legal_search' database exists.")