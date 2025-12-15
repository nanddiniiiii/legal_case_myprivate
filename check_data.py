import psycopg2

try:
    # Use the same connection as your API
    conn = psycopg2.connect(
        dbname="postgres", 
        user="postgres", 
        password="12345", 
        host="localhost", 
        port="5432"
    )
    
    cur = conn.cursor()
    
    # Check first 3 cases to see what data we have
    cur.execute("SELECT caseid, title, LEFT(judgment_text, 300) FROM cases LIMIT 3")
    results = cur.fetchall()
    
    print("=== CHECKING DATABASE CONTENT ===\n")
    for i, (caseid, title, text) in enumerate(results, 1):
        print(f"CASE {i} (ID: {caseid}):")
        print(f"Title: {title}")
        print(f"Text: {text}...")
        print("-" * 80)
    
    # Check total count
    cur.execute("SELECT COUNT(*) FROM cases")
    count = cur.fetchone()[0]
    print(f"\nTotal cases in database: {count}")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")