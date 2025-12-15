import psycopg2

conn = psycopg2.connect(
    dbname="legal_search",
    user="postgres",
    password="12345",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Check sample parties data
cur.execute("SELECT case_number, title, parties FROM cases LIMIT 10")
results = cur.fetchall()

print("Sample cases:")
for case_num, title, parties in results:
    print(f"\nCase: {case_num}")
    print(f"  Title: {title}")
    print(f"  Parties: {parties}")

cur.close()
conn.close()
