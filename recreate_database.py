import psycopg2

print("🔧 Recreating database and tables...")

# Connect to default postgres database first
conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="12345",
    host="localhost",
    port="5432"
)
conn.autocommit = True
cur = conn.cursor()

# Terminate all connections to legal_search database
print("Terminating all connections to legal_search database...")
cur.execute("""
    SELECT pg_terminate_backend(pg_stat_activity.pid)
    FROM pg_stat_activity
    WHERE pg_stat_activity.datname = 'legal_search'
    AND pid <> pg_backend_pid()
""")
print("✅ All connections terminated")

# Drop existing database if it exists (to ensure clean slate with new container)
print("Dropping existing legal_search database if it exists...")
cur.execute("DROP DATABASE IF EXISTS legal_search")
print("✅ Old database dropped (if existed)")

# Create fresh database
print("Creating fresh legal_search database...")
cur.execute("CREATE DATABASE legal_search")
print("✅ Database created!")

cur.close()
conn.close()

# Now connect to legal_search and create tables
print("\n🔧 Creating tables...")
conn = psycopg2.connect(
    dbname="legal_search",
    user="postgres",
    password="12345",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Enable pgvector extension
print("Enabling pgvector extension...")
try:
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    print("✅ pgvector extension enabled")
    conn.commit()
except Exception as e:
    print(f"⚠️  pgvector extension error: {e}")
    print("Trying to continue without pgvector...")
    conn.rollback()

# Create cases table
cur.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        id SERIAL PRIMARY KEY,
        case_number TEXT,
        title TEXT,
        parties TEXT,
        description TEXT,
        category TEXT,
        judgment_date TEXT,
        bench TEXT,
        embedding vector(384)
    )
""")
print("✅ Cases table created")

# Create users table
cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
print("✅ Users table created")

# Create user_searches table
cur.execute("""
    CREATE TABLE IF NOT EXISTS user_searches (
        id SERIAL PRIMARY KEY,
        user_email TEXT NOT NULL,
        query TEXT NOT NULL,
        results_count INTEGER,
        searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
print("✅ User searches table created")

# Create user_bookmarks table
cur.execute("""
    CREATE TABLE IF NOT EXISTS user_bookmarks (
        id SERIAL PRIMARY KEY,
        user_email TEXT NOT NULL,
        case_id INTEGER NOT NULL,
        bookmarked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_email, case_id)
    )
""")
print("✅ User bookmarks table created")

conn.commit()
cur.close()
conn.close()

print("\n🎉 Database setup complete!")
print("\n⚠️  IMPORTANT: Now you need to run intelligent_case_generator.py to populate the 47,400 cases!")
