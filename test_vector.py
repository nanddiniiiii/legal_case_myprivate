import psycopg2

conn = psycopg2.connect(
    dbname="legal_search",
    user="postgres",
    password="12345",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Check connection info
cur.execute("SELECT version();")
print("PostgreSQL version:", cur.fetchone()[0])

cur.execute("SELECT current_database();")
print("Current database:", cur.fetchone()[0])

# Check if vector extension exists
cur.execute("SELECT * FROM pg_available_extensions WHERE name = 'vector';")
result = cur.fetchone()
if result:
    print(f"\nVector extension available: {result}")
else:
    print("\n❌ Vector extension NOT available!")

# Check if already installed
cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
result = cur.fetchone()
if result:
    print(f"✅ Vector extension INSTALLED: {result}")
else:
    print("⚠️ Vector extension NOT installed yet")

cur.close()
conn.close()
