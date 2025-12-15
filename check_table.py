import psycopg2

conn = psycopg2.connect(
    host='localhost',
    database='legal_search',
    user='postgres',
    password='12345',
    port='5432'
)
cur = conn.cursor()

# Check what tables exist
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
tables = cur.fetchall()
print("Tables in database:", tables)

# If legal_cases exists, show its structure
if tables:
    for table in tables:
        table_name = table[0]
        print(f"\nColumns in {table_name}:")
        cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'")
        for col in cur.fetchall():
            print(f"  - {col[0]}: {col[1]}")

conn.close()
