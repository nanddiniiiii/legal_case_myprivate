import psycopg2
import sys

# --- This script directly searches your database or inspects a random row ---

def inspect_random_row():
    """Connects to the DB and fetches one random row to inspect its contents."""
    print("--- Inspecting a random row from the 'cases' table ---")
    conn = None
    try:
        conn = psycopg2.connect(
            dbname="postgres", user="postgres", password="12345", host="localhost", port="5432"
        )
        cur = conn.cursor()
        print("✅ Database connection successful.")

        # Fetch the title and judgment_text from one random case
        query = "SELECT title, judgment_text FROM cases ORDER BY RANDOM() LIMIT 1;"
        cur.execute(query)
        result = cur.fetchone()

        if result:
            title, judgment_text = result
            print("\n--- Found Random Case ---")
            print(f"Title: {title}")
            # Print the first 500 characters of the judgment text to see what's inside
            print(f"Judgment Text (first 500 chars): {judgment_text[:500]}")
            
            if not judgment_text or not judgment_text.strip():
                 print("\n❌ DIAGNOSIS: The 'judgment_text' column appears to be empty or blank.")
            else:
                 print("\n✅ DIAGNOSIS: The 'judgment_text' column contains data.")

        else:
            print("\n❌ Could not retrieve a random row. The 'cases' table might be empty.")

    except Exception as e:
        print(f"❌ AN ERROR OCCURRED: {e}")
    finally:
        if conn:
            conn.close()
            print("\nDatabase connection closed.")


def direct_db_search(search_term):
    """Connects to the DB and performs a direct ILIKE search on title and judgment_text."""
    print(f"--- Running a direct database search for the term: '{search_term}' ---")
    conn = None
    try:
        conn = psycopg2.connect(
            dbname="postgres", user="postgres", password="12345", host="localhost", port="5432"
        )
        cur = conn.cursor()
        print("✅ Database connection successful.")

        # UPDATED QUERY: Now searches both title and judgment_text, just like the API
        query = "SELECT title FROM cases WHERE title ILIKE %s OR judgment_text ILIKE %s LIMIT 5;"
        cur.execute(query, (f'%{search_term}%', f'%{search_term}%'))
        results = cur.fetchall()

        if results:
            print(f"\n✅ SUCCESS! Found {len(results)} matching cases in the database:")
            for i, row in enumerate(results):
                print(f"  {i+1}: {row[0]}")
        else:
            print(f"\n❌ CONFIRMED: The term '{search_term}' was not found in the title or text of any cases.")

    except Exception as e:
        print(f"❌ AN ERROR OCCURRED: {e}")
    finally:
        if conn:
            conn.close()
            print("\nDatabase connection closed.")

# --- How to run this script ---
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '--inspect':
            inspect_random_row()
        else:
            term_to_search = sys.argv[1]
            direct_db_search(term_to_search)
    else:
        print("❗ Please provide an action.")
        print("   Example Usage (Search) -> python debug_search.py court")
        print("   Example Usage (Inspect) -> python debug_search.py --inspect")