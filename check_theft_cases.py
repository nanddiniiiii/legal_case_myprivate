import psycopg2

# Connect to database
conn = psycopg2.connect(
    host="localhost",
    database="legal_search",
    user="postgres",
    password="12345"
)

cur = conn.cursor()

# Get first 10 theft cases
cur.execute("""
    SELECT case_number, LEFT(description, 150) as desc_preview 
    FROM cases 
    WHERE category = 'theft' 
    ORDER BY id 
    LIMIT 10;
""")

results = cur.fetchall()

print("=" * 80)
print("FIRST 10 THEFT CASES IN DATABASE:")
print("=" * 80)

for i, (case_num, desc) in enumerate(results, 1):
    print(f"\n{i}. {case_num}")
    print(f"   Description: {desc}...")
    print("-" * 80)

cur.close()
conn.close()
