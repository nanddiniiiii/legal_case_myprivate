import psycopg2

# Connect to legal_search database
conn = psycopg2.connect(
    dbname="legal_search",
    user="postgres",
    password="12345",
    host="localhost",
    port="5432"
)

cur = conn.cursor()

# Create users table
print("Creating users table...")
cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Create user_searches table
print("Creating user_searches table...")
cur.execute("""
    CREATE TABLE IF NOT EXISTS user_searches (
        id SERIAL PRIMARY KEY,
        user_email VARCHAR(255) NOT NULL,
        search_query TEXT NOT NULL,
        results_count INTEGER,
        search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Create user_bookmarks table
print("Creating user_bookmarks table...")
cur.execute("""
    CREATE TABLE IF NOT EXISTS user_bookmarks (
        id SERIAL PRIMARY KEY,
        user_email VARCHAR(255) NOT NULL,
        case_id INTEGER NOT NULL,
        bookmarked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_email, case_id)
    )
""")

conn.commit()
cur.close()
conn.close()

print("✅ All authentication tables created successfully in legal_search database!")
