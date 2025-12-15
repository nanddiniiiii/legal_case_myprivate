import psycopg2

# Connect to database
conn = psycopg2.connect(
    dbname="legal_search",
    user="postgres",
    password="12345",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Check how many cases exist
cur.execute("SELECT COUNT(*) FROM cases")
count = cur.fetchone()[0]
print(f"✅ Total cases in database: {count}")

# Check categories
cur.execute("SELECT category, COUNT(*) FROM cases GROUP BY category ORDER BY COUNT(*) DESC")
print("\n📊 Category distribution:")
for category, cat_count in cur.fetchall():
    print(f"  - {category}: {cat_count} cases")

# Show sample case
cur.execute("SELECT case_number, title, LEFT(description, 100) FROM cases LIMIT 1")
sample = cur.fetchone()
print(f"\n📄 Sample case:")
print(f"  Case Number: {sample[0]}")
print(f"  Title: {sample[1]}")
print(f"  Description: {sample[2]}...")

cur.close()
conn.close()
