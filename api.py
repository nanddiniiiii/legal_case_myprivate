# ==============================================================================
# IMPORT NECESSARY LIBRARIES
# ==============================================================================
from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import psycopg2
from sentence_transformers import SentenceTransformer
import numpy as np
import traceback
import random # Keep random for shuffling ties
import ast
from datetime import datetime, timezone
import bcrypt
import time
from functools import wraps
import os
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth

# Load environment variables
load_dotenv()

# Try to import pgvector, but work without it if not available
try:
    from pgvector.psycopg2 import register_vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    print("⚠️  pgvector not available - using fallback search method")

# ==============================================================================
# --- SIMPLE IN-MEMORY CACHE ---
# ==============================================================================
class SimpleCache:
    def __init__(self, ttl=300):  # Default 5 minutes TTL
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                print(f"--- CACHE HIT for key: {key[:50]}... ---")
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key, value):
        self.cache[key] = (value, time.time())
        print(f"--- CACHE SET for key: {key[:50]}... ---")
    
    def clear(self):
        self.cache.clear()
        print("--- CACHE CLEARED ---")

# Initialize caches
search_cache = SimpleCache(ttl=300)  # 5 minutes for searches
analytics_cache = SimpleCache(ttl=600)  # 10 minutes for analytics

# Cache decorator
def cached(cache, key_func=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = f.__name__ + str(args) + str(kwargs)
            
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            result = f(*args, **kwargs)
            cache.set(key, result)
            return result
        return wrapper
    return decorator

# ==============================================================================
# --- CONFIGURATION & AI MODEL LOADING ---
# ==============================================================================
app = Flask(__name__, static_folder='DBMS UI', static_url_path='')
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app, supports_credentials=True, origins='*', resources={r"/*": {"origins": "*"}})

# Configure OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

print("--- Loading AI model for semantic search ---")
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ AI model loaded successfully (all-MiniLM-L6-v2, 384 dims).")
except Exception as e:
    print(f"❌ CRITICAL ERROR: Could not load SentenceTransformer model. Error: {e}")
    model = None

# ==============================================================================
# --- DATABASE CONNECTION FUNCTION ---
# ==============================================================================
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        # Use environment variables for production, fallback to local for development
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "legal_search"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "12345"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ DATABASE CONNECTION ERROR: {e}")
        raise e

# ==============================================================================
# --- FRONTEND ROUTES ---
# ==============================================================================
@app.route('/')
def index():
    """Serve the main index page."""
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files from DBMS UI folder."""
    try:
        return app.send_static_file(path)
    except:
        # If file not found, serve index.html (for client-side routing)
        return app.send_static_file('index.html')

# ==============================================================================
# --- ENHANCED SEARCH ENDPOINT (WITH DIVERSIFICATION & LARGER POOL) ---
# ==============================================================================
@app.route('/search', methods=['GET'])
def search_cases():
    """
    Enhanced hybrid search prioritizing description diversity in results.
    Fetches a larger pool initially. Supports category filtering.
    """
    print("\n\n--- SERVER LOG: New Diversified Search Request Received ---")
    query = request.args.get('query', '').strip()
    category = request.args.get('category', '').strip()
    print(f"--- SERVER LOG: Received query: '{query}' (Category: {category or 'All'}) ---")

    if not query:
        print("--- SERVER LOG: ERROR - Query parameter is empty. ---")
        return jsonify({"error": "Query parameter is required."}), 400
    if not model:
        print("--- SERVER LOG: CRITICAL ERROR - AI model not loaded. ---")
        return jsonify({"error": "AI model is not available."}), 503

    conn = None
    cur = None
    RESULTS_LIMIT = 20 # How many results to finally return
    # *** OPTIMIZED FETCH POOL SIZE FOR SPEED ***
    FETCH_POOL_SIZE = 200 # Balanced pool size for speed and diversity

    # Check cache first for faster repeated searches
    cache_key = f"search:{query}:{category}"
    cached_result = search_cache.get(cache_key)
    if cached_result:
        print(f"--- SERVER LOG: 🚀 CACHE HIT for query: '{query[:50]}' ---")
        return jsonify(cached_result)

    try:
        print("--- SERVER LOG: Connecting to database for search... ---")
        conn = get_db_connection()
        
        # Try to register pgvector, but continue if it fails
        use_pgvector = False
        if PGVECTOR_AVAILABLE:
            try:
                register_vector(conn)
                use_pgvector = True
                print("--- SERVER LOG: Using pgvector for fast search ---")
            except Exception as e:
                print(f"--- SERVER LOG: pgvector not available in DB, using fallback method ---")
                use_pgvector = False
        
        cur = conn.cursor()
        print("--- SERVER LOG: ✅ DB Connection successful. ---")

        print("--- SERVER LOG: Generating query embedding... ---")
        query_embedding = model.encode(query)
        query_embedding_np = np.array(query_embedding, dtype=np.float32)
        print("--- SERVER LOG: ✅ Query embedding generated. ---")

        # Build category filter
        category_filter = ""
        query_params = []
        if category:
            category_filter = " AND category = %s"
            query_params = [category]
        
        # --- Keyword Search ---
        print(f"--- SERVER LOG: Performing keyword search (pool size {FETCH_POOL_SIZE})... ---")
        keyword_query = f"""
            SELECT case_number, title, parties, description, embedding,
                   CASE WHEN LOWER(description) ILIKE LOWER(%s) THEN 25.0
                        WHEN LOWER(title) ILIKE LOWER(%s) THEN 20.0
                        ELSE 0.0 END as keyword_bonus
            FROM cases WHERE (LOWER(description) ILIKE LOWER(%s) OR LOWER(title) ILIKE LOWER(%s)){category_filter}
            LIMIT %s;
        """
        search_pattern = f'%{query}%'
        params = [search_pattern, search_pattern, search_pattern, search_pattern] + query_params + [FETCH_POOL_SIZE]
        cur.execute(keyword_query, params)
        keyword_results_raw = cur.fetchall()
        print(f"--- SERVER LOG: Found {len(keyword_results_raw)} potential keyword matches. ---")

        # --- Semantic Search ---
        print(f"--- SERVER LOG: Performing semantic search (pool size {FETCH_POOL_SIZE})... ---")
        
        if use_pgvector:
            # Use pgvector for fast similarity search
            semantic_query = f"""
                SELECT case_number, title, parties, description, embedding, embedding <=> %s AS distance
                FROM cases WHERE 1=1{category_filter} ORDER BY distance ASC LIMIT %s;
            """
            params = [query_embedding_np] + query_params + [FETCH_POOL_SIZE]
            cur.execute(semantic_query, params)
            semantic_results_raw = cur.fetchall()
        else:
            # Fallback: Get all cases and calculate similarity in Python
            semantic_query = f"""
                SELECT case_number, title, parties, description, embedding
                FROM cases WHERE 1=1{category_filter} LIMIT %s;
            """
            params = query_params + [FETCH_POOL_SIZE]
            cur.execute(semantic_query, params)
            all_cases = cur.fetchall()
            
            # Calculate similarity in Python
            semantic_results_raw = []
            for case_number, title, parties, description, embedding in all_cases:
                try:
                    # Parse embedding from text
                    if isinstance(embedding, str):
                        case_emb = np.array(ast.literal_eval(embedding), dtype=np.float32)
                    else:
                        case_emb = np.array(embedding, dtype=np.float32)
                    
                    # Calculate cosine distance
                    norm1 = np.linalg.norm(query_embedding_np)
                    norm2 = np.linalg.norm(case_emb)
                    if norm1 > 0 and norm2 > 0:
                        similarity = np.dot(query_embedding_np, case_emb) / (norm1 * norm2)
                        distance = 1.0 - similarity
                    else:
                        distance = 2.0
                    
                    semantic_results_raw.append((case_number, title, parties, description, embedding, distance))
                except:
                    continue
            
            # Sort by distance and limit
            semantic_results_raw.sort(key=lambda x: x[5])
            semantic_results_raw = semantic_results_raw[:FETCH_POOL_SIZE]
        
        print(f"--- SERVER LOG: Found {len(semantic_results_raw)} potential semantic matches. ---")

        # --- Combine, Deduplicate, Cache Embeddings ---
        print("--- SERVER LOG: Combining results, calculating scores... ---")
        all_results_dict = {}
        processed_embeddings_cache = {}

        def process_embedding(case_num, emb_val):
            # Inner function to handle embedding processing and caching
            if case_num in processed_embeddings_cache: return processed_embeddings_cache[case_num]
            try:
                if isinstance(emb_val, str): np_emb = np.array(ast.literal_eval(emb_val), dtype=np.float32)
                elif isinstance(emb_val, (list, np.ndarray)): np_emb = np.array(emb_val, dtype=np.float32)
                else: np_emb = None
                processed_embeddings_cache[case_num] = np_emb if (np_emb is not None and len(np_emb) > 0) else None
                return processed_embeddings_cache[case_num]
            except Exception as e:
                # print(f"--- SERVER LOG: ⚠️ Warn - Embedding processing error for {case_num}: {e}") # Reduce noise
                processed_embeddings_cache[case_num] = None
                return None

        # Process keyword results
        for kw_row in keyword_results_raw:
            case_number, title, parties, desc, emb_val, bonus = kw_row
            if case_number not in all_results_dict:
                all_results_dict[case_number] = {'title': title, 'parties': parties, 'description': desc, 'keyword_bonus': bonus, 'distance': 2.0}
                process_embedding(case_number, emb_val)

        # Process semantic results
        for sem_row in semantic_results_raw:
            case_number, title, parties, desc, emb_val, distance = sem_row
            distance = float(distance)
            if case_number in all_results_dict:
                all_results_dict[case_number]['distance'] = min(all_results_dict[case_number].get('distance', 2.0), distance)
            else:
                 all_results_dict[case_number] = {'title': title, 'parties': parties, 'description': desc, 'keyword_bonus': 0.0, 'distance': distance}
            if case_number not in processed_embeddings_cache:
                process_embedding(case_number, emb_val)

        if not all_results_dict:
            print("--- SERVER LOG: ✅ No combined results found. ---")
            return jsonify([])

        # --- Calculate Final Scores ---
        scored_results_list = []
        query_norm = np.linalg.norm(query_embedding_np)
        if query_norm < 1e-6: query_norm = 1.0

        for case_number, data in all_results_dict.items():
            case_embedding_np = processed_embeddings_cache.get(case_number)
            if case_embedding_np is None: continue

            case_norm = np.linalg.norm(case_embedding_np)
            if case_norm < 1e-6: case_norm = 1.0

            # Calculate cosine similarity manually (always use manual calculation for consistency)
            cosine_sim = np.dot(query_embedding_np, case_embedding_np) / (query_norm * case_norm)
            # Convert to percentage (cosine similarity ranges from -1 to 1, typically 0 to 1 for similar items)
            base_score = max(0.0, float(cosine_sim) * 100.0)
            
            # Add keyword bonus
            final_score = min(100.0, base_score + float(data.get('keyword_bonus', 0.0)))

            scored_results_list.append({
                'case_number': str(case_number),
                'title': str(data.get('title', 'Untitled Case')),
                'parties': str(data.get('parties', 'Unknown vs Unknown')),
                'description': str(data.get('description', 'No content available.')),
                'score': round(final_score, 1)
            })

        print(f"--- SERVER LOG: ✅ Scored {len(scored_results_list)} unique potential results from pool. ---")

        # --- Prioritize Description Diversity ---
        print("--- SERVER LOG: Selecting top results with description diversity... ---")
        scored_results_list.sort(key=lambda x: x.get('score', 0), reverse=True)

        diverse_top_results = []
        seen_description_keys = set()
        description_key_length = 500 # Use first N chars to check uniqueness

        for result in scored_results_list:
            if len(diverse_top_results) >= RESULTS_LIMIT: break
            desc_text = result.get('description', '')
            desc_key = desc_text[:description_key_length]
            if desc_key not in seen_description_keys:
                diverse_top_results.append(result)
                seen_description_keys.add(desc_key)

        # Fill remaining spots if needed
        if len(diverse_top_results) < RESULTS_LIMIT:
            print(f"--- SERVER LOG: Only found {len(diverse_top_results)} unique descriptions. Filling remaining spots... ---")
            remaining_needed = RESULTS_LIMIT - len(diverse_top_results)
            included_case_numbers = {res['case_number'] for res in diverse_top_results}
            for result in scored_results_list:
                if remaining_needed <= 0: break
                if result['case_number'] not in included_case_numbers:
                    diverse_top_results.append(result)
                    included_case_numbers.add(result['case_number'])
                    remaining_needed -= 1

        print(f"--- SERVER LOG: ✅ Returning {len(diverse_top_results)} results prioritizing diversity. ---")

        # Log top results
        for i, result in enumerate(diverse_top_results[:5]):
            print(f"--- SERVER LOG: Top {i+1}: '{str(result.get('title','N/A'))[:40]}...' - Score: {result.get('score','N/A')}% ---")

        # --- Track Search ---
        try:
            user_email = request.headers.get('X-User-Email', 'anonymous')
            print(f"--- SERVER LOG: 📊 Attempting to track search for: {user_email} (query: '{query}', results: {len(diverse_top_results)}) ---")
            if table_exists(cur, 'user_searches'):
                cur.execute("""
                    INSERT INTO user_searches (user_email, query, result_count, searched_at)
                    VALUES (%s, %s, %s, %s);
                """, (user_email, query, len(diverse_top_results), datetime.now(timezone.utc)))
                conn.commit()
                print(f"--- SERVER LOG: ✅ Successfully tracked search for user: {user_email} ---")
            else:
                print("--- SERVER LOG: ⚠️ Skipping search tracking ('user_searches' table not found). ---")
        except Exception as track_error:
            conn.rollback()
            print(f"--- SERVER LOG: ❌ Error tracking search: {track_error} ---")
            import traceback
            traceback.print_exc()

        # Cache results for 5 minutes
        cache_key = f"search:{query}:{category}"
        search_cache.set(cache_key, diverse_top_results)
        print(f"--- SERVER LOG: 💾 Cached search results for: '{query[:50]}' ---")
        
        return jsonify(diverse_top_results)

    except psycopg2.OperationalError as db_err:
         print(f"--- SERVER LOG: ❌ DATABASE CONNECTION FAILED during search: {db_err} ---")
         traceback.print_exc()
         return jsonify({"error": "Database connection failed. Please try again later."}), 503
    except Exception as e:
        print(f"--- SERVER LOG: ❌ UNEXPECTED ERROR during search: {e} ---")
        traceback.print_exc()
        if conn: conn.rollback()
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500
    finally:
        if conn:
            if cur: cur.close()
            conn.close()
            print("--- SERVER LOG: Database connection closed (search). ---")


# ==============================================================================
# --- BROWSE BY CATEGORY ENDPOINT ---
# ==============================================================================
# In api.py

# ... (Keep imports, app setup, model loading, get_db_connection, search_cases, etc.) ...

# ==============================================================================
# --- BROWSE BY CATEGORY ENDPOINT (MODIFIED TO INCLUDE CASE_NUMBER) ---
# ==============================================================================
# ... (Keep rest of api.py: auth endpoints, case details endpoint, main block) ...

# ==============================================================================
# --- AUTHENTICATION & PROFILE ENDPOINTS ---
# ==============================================================================

# Helper function to check if a table exists
def table_exists(cursor, table_name):
    try:
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s);", (table_name,))
        return cursor.fetchone()[0]
    except Exception as e:
        print(f"--- SERVER LOG: ⚠️ Error checking if table '{table_name}' exists: {e}")
        return False

@app.route('/register', methods=['POST'])
def register_user():
    conn = None; cur = None
    try:
        data = request.get_json();
        if not data: return jsonify({"error": "Invalid JSON"}), 400
        full_name = data.get('fullName','').strip(); email = data.get('email','').strip(); password = data.get('password','').strip()
        if not all([full_name, email, password]): return jsonify({"error": "Missing required fields"}), 400
        
        # Hash password with bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        conn = get_db_connection(); cur = conn.cursor()
        if not table_exists(cur, 'users'): raise psycopg2.errors.UndefinedTable("Table 'users' needed for registration.")
        cur.execute("SELECT 1 FROM users WHERE email = %s LIMIT 1;", (email,))
        if cur.fetchone(): return jsonify({"error": "User already exists"}), 409
        cur.execute("INSERT INTO users (name, email, password_hash, created_at) VALUES (%s, %s, %s, %s);", (full_name, email, password_hash, datetime.now(timezone.utc)))
        conn.commit(); print(f"--- SERVER LOG: ✅ Registered: {email} (password hashed) ---"); return jsonify({"message": "User registered"}), 201
    except psycopg2.errors.UndefinedTable as e: print(f"--- SERVER LOG: ❌ SETUP ERROR - {e} ---"); return jsonify({"error": f"Setup error: {e}"}), 503
    except psycopg2.OperationalError as db_err: print(f"--- SERVER LOG: ❌ DB CONNECTION FAILED registration: {db_err} ---"); return jsonify({"error": "Database error"}), 503
    except Exception as e:
        print(f"--- SERVER LOG: ❌ ERROR registration: {e} ---")
        traceback.print_exc()
        if conn:
            conn.rollback()
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500
    finally:
        if conn:
            if cur: cur.close()
            conn.close()

@app.route('/login', methods=['POST'])
def login_user():
    conn = None; cur = None
    try:
        data = request.get_json();
        if not data: return jsonify({"error": "Invalid JSON"}), 400
        email = data.get('email','').strip(); password = data.get('password','').strip()
        if not all([email, password]): return jsonify({"error": "Email/password required"}), 400
        conn = get_db_connection(); cur = conn.cursor()
        if not table_exists(cur, 'users'): raise psycopg2.errors.UndefinedTable("Table 'users' needed for login.")
        
        # Get password_hash from database
        cur.execute("SELECT name, email, password_hash FROM users WHERE email = %s;", (email,))
        user = cur.fetchone()
        
        if user and user[2]:  # Check if user exists and has password_hash
            # Verify password with bcrypt
            if bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
                print(f"--- SERVER LOG: ✅ Login OK: {email} (bcrypt verified) ---")
                return jsonify({"message": "Login successful", "user": {"name": user[0], "email": user[1]}}), 200
            else:
                print(f"--- SERVER LOG: ⚠️ Login FAILED: {email} (wrong password) ---")
                return jsonify({"error": "Invalid credentials"}), 401
        else:
            print(f"--- SERVER LOG: ⚠️ Login FAILED: {email} (user not found or no hash) ---")
            return jsonify({"error": "Invalid credentials"}), 401
            
    except psycopg2.errors.UndefinedTable as e: print(f"--- SERVER LOG: ❌ SETUP ERROR - {e} ---"); return jsonify({"error": f"Setup error: {e}"}), 503
    except psycopg2.OperationalError as db_err: print(f"--- SERVER LOG: ❌ DB CONNECTION FAILED login: {db_err} ---"); return jsonify({"error": "Database error"}), 503
    except Exception as e:
        print(f"--- SERVER LOG: ❌ ERROR login: {e} ---")
        traceback.print_exc()
        return jsonify({"error": f"Login failed: {str(e)}"}), 500
    finally:
        if conn:
            if cur: cur.close()
            conn.close()

def calculate_time_ago(timestamp):
    if not timestamp: return "Unknown"
    try:
        if timestamp.tzinfo is None: timestamp = timestamp.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc); diff = now - timestamp
        seconds = diff.total_seconds(); days = diff.days
        if days > 1: return f"{days} days ago"
        elif days == 1: return "1 day ago"
        elif seconds >= 3600: hours = int(seconds // 3600); return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif seconds >= 60: minutes = int(seconds // 60); return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else: return "Just now"
    except Exception: return "Unknown time"

@app.route('/recent-searches', methods=['GET'])
def get_recent_searches():
    conn = None; cur = None
    try:
        user_email = request.args.get('email', 'anonymous'); limit = request.args.get('limit', 10, type=int)
        print(f"--- SERVER LOG: Fetching recent searches for: {user_email} ---")
        conn = get_db_connection(); cur = conn.cursor()
        if not table_exists(cur, 'user_searches'): raise psycopg2.errors.UndefinedTable("Table 'user_searches' needed for history.")
        cur.execute("SELECT query, results_count, searched_at FROM user_searches WHERE user_email = %s ORDER BY searched_at DESC LIMIT %s;", (user_email, limit))
        searches = cur.fetchall()
        recent_searches = [{"query": r[0], "results_count": r[1], "timestamp": r[2].isoformat() if r[2] else None, "time_ago": calculate_time_ago(r[2])} for r in searches]
        print(f"--- SERVER LOG: ✅ Found {len(recent_searches)} searches ---"); return jsonify(recent_searches), 200
    except psycopg2.errors.UndefinedTable as e: print(f"--- SERVER LOG: ❌ SETUP ERROR - {e} ---"); return jsonify({"error": f"Setup error: {e}"}), 503
    except psycopg2.OperationalError as db_err: print(f"--- SERVER LOG: ❌ DB CONNECTION FAILED history: {db_err} ---"); return jsonify({"error": "Database error"}), 503
    except Exception as e:
        print(f"--- SERVER LOG: ❌ ERROR fetching history: {e} ---")
        traceback.print_exc()
        return jsonify({"error": f"Could not fetch history: {str(e)}"}), 500
    finally:
        if conn:
            if cur: cur.close()
            conn.close()

@app.route('/user-stats', methods=['GET'])
def get_user_stats():
    conn = None; cur = None
    try:
        user_email = request.args.get('email');
        if not user_email: return jsonify({"error": "Email required"}), 400
        print(f"--- SERVER LOG: Fetching stats for: {user_email} ---")
        conn = get_db_connection(); cur = conn.cursor()
        if not table_exists(cur, 'users'): raise psycopg2.errors.UndefinedTable("Table 'users' needed for stats.")
        if not table_exists(cur, 'user_searches'): raise psycopg2.errors.UndefinedTable("Table 'user_searches' needed for stats.")
        bookmarks_table_exists = table_exists(cur, 'user_bookmarks')
        cur.execute("SELECT name, created_at FROM users WHERE email = %s;", (user_email,))
        user_info = cur.fetchone()
        if not user_info: return jsonify({"error": "User not found"}), 404
        user_name, created_at = user_info
        if created_at and created_at.tzinfo is None: created_at = created_at.replace(tzinfo=timezone.utc)
        days_active = max(1, (datetime.now(timezone.utc) - created_at).days) if created_at else 1
        member_since = created_at.strftime("%B %Y") if created_at else "Unknown"
        cur.execute("SELECT COUNT(*) FROM user_searches WHERE user_email = %s;", (user_email,))
        total_searches = cur.fetchone()[0]
        bookmarks_count = 0
        if bookmarks_table_exists: cur.execute("SELECT COUNT(*) FROM user_bookmarks WHERE user_email = %s;", (user_email,)); bookmarks_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM user_searches WHERE user_email = %s AND results_count > 0;", (user_email,))
        successful_searches = cur.fetchone()[0]
        success_rate = round((successful_searches / total_searches) * 100) if total_searches > 0 else 0
        research_hours = (total_searches * 1) // 60
        print(f"--- SERVER LOG: ✅ Stats fetched for {user_email} ---")
        return jsonify({"name": user_name, "member_since": member_since, "days_active": days_active, "total_searches": total_searches, "bookmarks": bookmarks_count, "research_time": f"{research_hours}h", "success_rate": f"{success_rate}%"}), 200
    except psycopg2.errors.UndefinedTable as e: print(f"--- SERVER LOG: ❌ SETUP ERROR - {e} ---"); return jsonify({"error": f"Setup error: {e}"}), 503
    except psycopg2.OperationalError as db_err: print(f"--- SERVER LOG: ❌ DB CONNECTION FAILED stats: {db_err} ---"); return jsonify({"error": "Database error"}), 503
    except Exception as e:
        print(f"--- SERVER LOG: ❌ ERROR fetching stats: {e} ---")
        traceback.print_exc()
        return jsonify({"error": f"Could not fetch stats: {str(e)}"}), 500
    finally:
        if conn:
            if cur: cur.close()
            conn.close()

@app.route('/update-profile', methods=['POST'])
def update_profile():
    conn = None; cur = None
    try:
        data = request.json;
        if not data: return jsonify({"error": "Invalid JSON"}), 400
        user_email = data.get('email'); new_name = data.get('name')
        if not user_email or not new_name: return jsonify({"error": "Email and name required"}), 400
        print(f"--- SERVER LOG: Updating profile for: {user_email} ---")
        conn = get_db_connection(); cur = conn.cursor()
        if not table_exists(cur, 'users'): raise psycopg2.errors.UndefinedTable("Table 'users' needed for update.")
        cur.execute("UPDATE users SET name = %s WHERE email = %s;", (new_name, user_email))
        if cur.rowcount == 0: return jsonify({"error": "User not found"}), 404
        conn.commit(); print(f"--- SERVER LOG: ✅ Profile updated for {user_email} ---"); return jsonify({"message": "Profile updated"}), 200
    except psycopg2.errors.UndefinedTable as e: print(f"--- SERVER LOG: ❌ SETUP ERROR - {e} ---"); return jsonify({"error": f"Setup error: {e}"}), 503
    except psycopg2.OperationalError as db_err: print(f"--- SERVER LOG: ❌ DB CONNECTION FAILED update profile: {db_err} ---"); return jsonify({"error": "Database error"}), 503
    except Exception as e:
        print(f"--- SERVER LOG: ❌ ERROR updating profile: {e} ---")
        traceback.print_exc()
        if conn:
            conn.rollback()
        return jsonify({"error": f"Profile update failed: {str(e)}"}), 500
    finally:
        if conn:
            if cur: cur.close()
            conn.close()

# ==============================================================================
# --- SEARCH HISTORY ENDPOINTS ---
# ==============================================================================
@app.route('/api/search-history', methods=['GET'])
def get_search_history():
    """Get search history for a user"""
    print("\n--- SERVER LOG: Get search history request received ---")
    
    user_email = request.headers.get('X-User-Email', 'anonymous')
    print(f"--- SERVER LOG: Fetching search history for user: {user_email} ---")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if not table_exists(cur, 'user_searches'):
            print("--- SERVER LOG: user_searches table does not exist ---")
            return jsonify({'searches': []}), 200
        
        cur.execute("""
            SELECT id, query, searched_at, result_count
            FROM user_searches
            WHERE user_email = %s
            ORDER BY searched_at DESC
            LIMIT 50
        """, (user_email,))
        
        searches = [{
            'id': row[0],
            'query': row[1],
            'searched_at': row[2].isoformat() if row[2] else None,
            'result_count': row[3] or 0
        } for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        print(f"--- SERVER LOG: Returning {len(searches)} searches ---")
        return jsonify({'searches': searches}), 200
        
    except Exception as e:
        print(f"--- SERVER LOG: Error getting search history: {e} ---")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/clear-search-history', methods=['POST'])
def clear_search_history():
    conn = None; cur = None
    try:
        data = request.json;
        if not data: return jsonify({"error": "Invalid JSON"}), 400
        user_email = data.get('email')
        if not user_email: return jsonify({"error": "Email required"}), 400
        print(f"--- SERVER LOG: Clearing history for: {user_email} ---")
        conn = get_db_connection(); cur = conn.cursor()
        if not table_exists(cur, 'user_searches'): raise psycopg2.errors.UndefinedTable("Table 'user_searches' needed for clear.")
        cur.execute("DELETE FROM user_searches WHERE user_email = %s;", (user_email,))
        deleted_count = cur.rowcount; conn.commit()
        print(f"--- SERVER LOG: ✅ Cleared {deleted_count} records ---"); return jsonify({"message": "History cleared", "deleted_count": deleted_count}), 200
    except psycopg2.errors.UndefinedTable as e: print(f"--- SERVER LOG: ❌ SETUP ERROR - {e} ---"); return jsonify({"error": f"Setup error: {e}"}), 503
    except psycopg2.OperationalError as db_err: print(f"--- SERVER LOG: ❌ DB CONNECTION FAILED clearing history: {db_err} ---"); return jsonify({"error": "Database error"}), 503
    except Exception as e:
        print(f"--- SERVER LOG: ❌ ERROR clearing history: {e} ---")
        traceback.print_exc()
        if conn:
            conn.rollback()
        return jsonify({"error": f"Failed to clear history: {str(e)}"}), 500
    finally:
        if conn:
            if cur: cur.close()
            conn.close()
            print("--- SERVER LOG: DB connection closed (clear history). ---")

# ==============================================================================
# --- USER PREFERENCES ENDPOINTS ---
# ==============================================================================
@app.route('/api/user-preferences', methods=['POST'])
def save_user_preferences():
    """Save user preferences"""
    print("\n--- SERVER LOG: Save preferences request received ---")
    
    user_email = request.headers.get('X-User-Email', 'anonymous')
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Create table if it doesn't exist
        if not table_exists(cur, 'user_preferences'):
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_email VARCHAR(255) PRIMARY KEY,
                    theme VARCHAR(10) DEFAULT 'dark',
                    default_category VARCHAR(100),
                    results_per_page INT DEFAULT 20,
                    email_notifications BOOLEAN DEFAULT true,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        
        # Update or insert preferences
        theme = data.get('theme')
        if theme:
            cur.execute("""
                INSERT INTO user_preferences (user_email, theme, updated_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_email) 
                DO UPDATE SET theme = EXCLUDED.theme, updated_at = EXCLUDED.updated_at
            """, (user_email, theme, datetime.now(timezone.utc)))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"--- SERVER LOG: ✅ Preferences saved for {user_email} ---")
        return jsonify({"message": "Preferences saved successfully"}), 200
        
    except Exception as e:
        print(f"--- SERVER LOG: Error saving preferences: {e} ---")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# --- CHANGE PASSWORD ENDPOINT ---
# ==============================================================================
@app.route('/change-password', methods=['POST'])
def change_password():
    """Change user password"""
    print("\n--- SERVER LOG: Change password request received ---")
    conn = None
    cur = None
    
    try:
        user_email = request.headers.get('X-User-Email')
        if not user_email:
            return jsonify({"error": "User email required"}), 401
        
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({"error": "Current and new password required"}), 400
        
        if len(new_password) < 6:
            return jsonify({"error": "New password must be at least 6 characters"}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if users table exists
        if not table_exists(cur, 'users'):
            return jsonify({"error": "Users table not found"}), 500
        
        # Get current password hash
        cur.execute("SELECT password FROM users WHERE email = %s", (user_email,))
        result = cur.fetchone()
        
        if not result:
            return jsonify({"error": "User not found"}), 404
        
        stored_password_hash = result[0]
        
        # Verify current password
        if not bcrypt.checkpw(current_password.encode('utf-8'), stored_password_hash.encode('utf-8')):
            return jsonify({"error": "Current password is incorrect"}), 401
        
        # Hash new password
        new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update password
        cur.execute("""
            UPDATE users 
            SET password = %s 
            WHERE email = %s
        """, (new_password_hash, user_email))
        
        conn.commit()
        
        print(f"--- SERVER LOG: Password changed successfully for {user_email} ---")
        return jsonify({"message": "Password changed successfully"}), 200
        
    except Exception as e:
        print(f"--- SERVER LOG: Error changing password: {e} ---")
        traceback.print_exc()
        if conn:
            conn.rollback()
        return jsonify({"error": "Failed to change password"}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """Get database statistics"""
    print("\n--- SERVER LOG: Statistics request received ---")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Total cases
        cur.execute("SELECT COUNT(*) FROM cases")
        total_cases = cur.fetchone()[0]
        
        # Cases per category
        cur.execute("""
            SELECT category, COUNT(*) as count 
            FROM cases 
            GROUP BY category 
            ORDER BY count DESC
        """)
        categories = [{"name": row[0], "count": row[1]} for row in cur.fetchall()]
        
        # Recent cases (last 100)
        cur.execute("""
            SELECT COUNT(*) FROM cases 
            WHERE id > (SELECT MAX(id) - 100 FROM cases)
        """)
        recent_cases = cur.fetchone()[0]
        
        stats = {
            "total_cases": total_cases,
            "categories": categories,
            "recent_additions": recent_cases,
            "total_categories": len(categories)
        }
        
        cur.close()
        conn.close()
        
        return jsonify(stats), 200
        
    except Exception as e:
        print(f"--- SERVER LOG: Error getting stats: {e} ---")
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# --- GOOGLE SIGN-IN ENDPOINT ---
# ==============================================================================
@app.route('/google-signin', methods=['POST'])
def google_signin():
    """Handle Google Sign-In authentication"""
    print("\n--- SERVER LOG: Google Sign-In request received ---")
    conn = None
    cur = None
    
    try:
        data = request.get_json()
        email = data.get('email')
        name = data.get('name')
        auth_provider = data.get('auth_provider', 'google')
        
        if not email:
            return jsonify({"error": "Email required"}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if users table exists
        if not table_exists(cur, 'users'):
            print("--- SERVER LOG: Creating users table for Google auth ---")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255),
                    name VARCHAR(255),
                    auth_provider VARCHAR(50) DEFAULT 'email',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        
        # Check if user exists
        cur.execute("SELECT id, email, name FROM users WHERE email = %s", (email,))
        existing_user = cur.fetchone()
        
        if existing_user:
            print(f"--- SERVER LOG: Existing Google user logged in: {email} ---")
            return jsonify({
                "message": "Login successful",
                "user": {
                    "id": existing_user[0],
                    "email": existing_user[1],
                    "name": existing_user[2]
                }
            }), 200
        else:
            # Create new user for Google auth (no password required)
            cur.execute("""
                INSERT INTO users (email, name, auth_provider)
                VALUES (%s, %s, %s)
                RETURNING id, email, name
            """, (email, name, auth_provider))
            new_user = cur.fetchone()
            conn.commit()
            
            print(f"--- SERVER LOG: New Google user registered: {email} ---")
            return jsonify({
                "message": "Registration successful",
                "user": {
                    "id": new_user[0],
                    "email": new_user[1],
                    "name": new_user[2]
                }
            }), 201
        
    except Exception as e:
        print(f"--- SERVER LOG: Error in Google sign-in: {e} ---")
        traceback.print_exc()
        if conn:
            conn.rollback()
        return jsonify({"error": "Google sign-in failed"}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# ==============================================================================
# --- BROWSE BY CATEGORIES ENDPOINT ---
# ==============================================================================
@app.route('/browse', methods=['GET'])
def browse_cases():
    """Browse cases by one or more categories"""
    print("\n--- SERVER LOG: Browse request received ---")
    
    categories_param = request.args.get('categories', '')
    
    if not categories_param:
        return jsonify({"error": "categories parameter is required"}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Handle 'all' special case
        if categories_param == 'all':
            query = """
                SELECT case_number, title, parties, description, category
                FROM cases
                ORDER BY case_number DESC
                LIMIT 500
            """
            cur.execute(query)
        else:
            # Split comma-separated categories
            categories = [cat.strip() for cat in categories_param.split(',')]
            
            # Build query with IN clause
            placeholders = ','.join(['%s'] * len(categories))
            query = f"""
                SELECT case_number, title, parties, description, category
                FROM cases
                WHERE category IN ({placeholders})
                ORDER BY case_number DESC
                LIMIT 500
            """
            cur.execute(query, categories)
        
        results = [{
            'case_number': row[0],
            'title': row[1] or 'Untitled Case',
            'parties': row[2] or 'Unknown',
            'text': row[3] or 'No description available',
            'category': row[4] or 'Uncategorized'
        } for row in cur.fetchall()]
        
        cur.close()
        conn.close()
        
        print(f"--- SERVER LOG: Returning {len(results)} cases for categories: {categories_param} ---")
        return jsonify(results), 200
        
    except Exception as e:
        print(f"--- SERVER LOG: Error in browse: {e} ---")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# --- ANALYTICS DASHBOARD ENDPOINT ---
# ==============================================================================
@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get comprehensive analytics for dashboard (with caching)"""
    print("\n--- SERVER LOG: Analytics request received ---")
    
    # Check cache first
    cached_data = analytics_cache.get('analytics_dashboard')
    if cached_data:
        return jsonify(cached_data), 200
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if required tables exist
        if not table_exists(cur, 'cases'):
            return jsonify({"error": "Cases table not found"}), 503
        
        # Total cases
        cur.execute("SELECT COUNT(*) FROM cases")
        total_cases = cur.fetchone()[0]
        
        # Cases by category
        cur.execute("""
            SELECT category, COUNT(*) as count 
            FROM cases 
            GROUP BY category 
            ORDER BY category
        """)
        cases_by_category = {row[0]: row[1] for row in cur.fetchall()}
        
        # Cases by court
        cur.execute("""
            SELECT 
                COALESCE(court_name, 'Unknown') as court,
                COUNT(*) as count 
            FROM cases 
            GROUP BY court_name 
            ORDER BY count DESC
            LIMIT 10
        """)
        cases_by_court = {row[0]: row[1] for row in cur.fetchall()}
        
        # Cases by year
        cur.execute("""
            SELECT 
                year::text as year,
                COUNT(*) as count 
            FROM cases 
            WHERE year IS NOT NULL
            GROUP BY year 
            ORDER BY year DESC
            LIMIT 10
        """)
        cases_by_year = {str(row[0]): row[1] for row in cur.fetchall()}
        
        # Total searches (with fallback if table doesn't exist)
        if table_exists(cur, 'user_searches'):
            cur.execute("SELECT COUNT(*) FROM user_searches")
            total_searches = cur.fetchone()[0]
            
            # Search trend (last 7 days)
            cur.execute("""
                SELECT 
                    DATE(searched_at) as search_date,
                    COUNT(*) as count
                FROM user_searches
                WHERE searched_at >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY DATE(searched_at)
                ORDER BY search_date
            """)
            search_trend = {str(row[0]): row[1] for row in cur.fetchall()}
            
            # Recent searches
            cur.execute("""
                SELECT 
                    query,
                    user_email,
                    searched_at,
                    result_count
                FROM user_searches
                ORDER BY searched_at DESC
                LIMIT 20
            """)
            recent_searches = [{
                'query': row[0],
                'user_email': row[1],
                'searched_at': row[2].isoformat() if row[2] else None,
                'result_count': row[3] or 0
            } for row in cur.fetchall()]
        else:
            total_searches = 0
            search_trend = {}
            recent_searches = []
        
        # Total users (with fallback if table doesn't exist)
        if table_exists(cur, 'users'):
            cur.execute("SELECT COUNT(*) FROM users")
            total_users = cur.fetchone()[0]
        else:
            total_users = 0
        
        analytics = {
            "total_cases": total_cases,
            "total_categories": len(cases_by_category),
            "total_searches": total_searches,
            "total_users": total_users,
            "cases_by_category": cases_by_category,
            "cases_by_court": cases_by_court,
            "cases_by_year": cases_by_year,
            "search_trend": search_trend,
            "recent_searches": recent_searches
        }
        
        cur.close()
        conn.close()
        
        # Cache the result
        analytics_cache.set('analytics_dashboard', analytics)
        
        return jsonify(analytics), 200
        
    except Exception as e:
        print(f"--- SERVER LOG: Error getting analytics: {e} ---")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# --- BOOKMARKING ENDPOINTS ---
# ==============================================================================
@app.route('/api/bookmarks', methods=['GET'])
def get_bookmarks():
    """Get all bookmarks for a user"""
    print("\n--- SERVER LOG: Get bookmarks request received ---")
    
    user_email = request.headers.get('X-User-Email', 'anonymous')
    print(f"--- SERVER LOG: Fetching bookmarks for user: {user_email} ---")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if tables exist
        if not table_exists(cur, 'user_bookmarks'):
            print("--- SERVER LOG: user_bookmarks table does not exist ---")
            return jsonify({'bookmarks': []}), 200
        
        if not table_exists(cur, 'cases'):
            print("--- SERVER LOG: cases table does not exist ---")
            return jsonify({'bookmarks': []}), 200
        
        cur.execute("""
            SELECT b.case_number, b.bookmarked_at, b.notes,
                   c.title, c.parties, c.category, c.judgment_date, c.court_name
            FROM user_bookmarks b
            JOIN cases c ON b.case_number = c.case_number
            WHERE b.user_email = %s
            ORDER BY b.bookmarked_at DESC
        """, (user_email,))
        
        rows = cur.fetchall()
        print(f"--- SERVER LOG: Found {len(rows)} bookmarks for user {user_email} ---")
        
        bookmarks = [{
            'case_number': row[0],
            'bookmarked_at': row[1].isoformat() if row[1] else None,
            'notes': row[2],
            'title': row[3],
            'parties': row[4],
            'category': row[5],
            'judgment_date': row[6].isoformat() if row[6] else 'N/A',
            'court_name': row[7] or 'N/A'
        } for row in rows]
        
        cur.close()
        conn.close()
        
        print(f"--- SERVER LOG: Returning {len(bookmarks)} bookmarks ---")
        return jsonify({'bookmarks': bookmarks}), 200
        
    except Exception as e:
        print(f"--- SERVER LOG: Error getting bookmarks: {e} ---")
        return jsonify({"error": str(e)}), 500


@app.route('/api/bookmarks', methods=['POST'])
def add_bookmark():
    """Add a bookmark"""
    print("\n--- SERVER LOG: Add bookmark request received ---")
    
    data = request.get_json()
    user_email = request.headers.get('X-User-Email', 'anonymous')
    case_number = data.get('case_number')
    notes = data.get('notes', '')
    
    print(f"--- SERVER LOG: Adding bookmark - User: {user_email}, Case: {case_number} ---")
    
    if not case_number:
        return jsonify({"error": "case_number is required"}), 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if table exists
        if not table_exists(cur, 'user_bookmarks'):
            print("--- SERVER LOG: user_bookmarks table does not exist, creating it ---")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_bookmarks (
                    id SERIAL PRIMARY KEY,
                    user_email VARCHAR(255) NOT NULL,
                    case_number VARCHAR(100) NOT NULL,
                    notes TEXT,
                    bookmarked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_email, case_number)
                )
            """)
            conn.commit()
        
        # Check if bookmark already exists
        cur.execute("""
            SELECT id FROM user_bookmarks 
            WHERE user_email = %s AND case_number = %s
        """, (user_email, case_number))
        
        if cur.fetchone():
            cur.close()
            conn.close()
            print(f"--- SERVER LOG: Bookmark already exists for case {case_number} ---")
            return jsonify({"message": "Bookmark already exists"}), 200
        
        # Add bookmark
        cur.execute("""
            INSERT INTO user_bookmarks (user_email, case_number, notes, bookmarked_at)
            VALUES (%s, %s, %s, %s)
        """, (user_email, case_number, notes, datetime.now(timezone.utc)))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"--- SERVER LOG: ✅ Bookmark added successfully for case {case_number} ---")
        return jsonify({"message": "Bookmark added successfully"}), 201
        
    except Exception as e:
        print(f"--- SERVER LOG: Error adding bookmark: {e} ---")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/bookmarks/<case_number>', methods=['DELETE'])
def delete_bookmark(case_number):
    """Delete a bookmark"""
    print(f"\n--- SERVER LOG: Delete bookmark request for case: {case_number} ---")
    
    user_email = request.headers.get('X-User-Email', 'anonymous')
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            DELETE FROM user_bookmarks 
            WHERE user_email = %s AND case_number = %s
        """, (user_email, case_number))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"message": "Bookmark deleted successfully"}), 200
        
    except Exception as e:
        print(f"--- SERVER LOG: Error deleting bookmark: {e} ---")
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# --- CASE DETAILS ENDPOINT ---
# ==============================================================================
@app.route('/case/<case_number>', methods=['GET'])
def get_case_details(case_number):
    print(f"\n--- SERVER LOG: Fetching details for case: {case_number} ---")
    conn = None; cur = None
    try:
        conn = get_db_connection()
        # Don't register pgvector here - will handle manually if needed
        cur = conn.cursor()
        if not table_exists(cur, 'cases'): raise psycopg2.errors.UndefinedTable("Table 'cases' needed for details.")
        query = "SELECT id, case_number, title, parties, description, embedding, category FROM cases WHERE case_number = %s;"
        cur.execute(query, (case_number,))
        result = cur.fetchone()
        if not result: print(f"--- SERVER LOG: ⚠️ Case {case_number} not found. ---"); return jsonify({"error": "Case not found"}), 404
        case_id, db_case_number, title, parties, description, embedding_val, category = result
        petitioner = title or "Unknown Petitioner"; respondent = parties or "Unknown Respondent"
        case_embedding_np = None
        try:
            if isinstance(embedding_val, str): case_embedding_np = np.array(ast.literal_eval(embedding_val), dtype=np.float32)
            else: case_embedding_np = np.array(embedding_val, dtype=np.float32)
            if len(case_embedding_np) == 0: raise ValueError("Empty embedding")
        except Exception as emb_err: print(f"--- SERVER LOG: ❌ ERROR processing embedding for {db_case_number}: {emb_err} ---")
        similar_cases_list = []
        if case_embedding_np is not None:
            print(f"--- SERVER LOG: Finding similar cases for {db_case_number}... ---")
            try:
                # Get all other cases for similarity comparison
                similar_query = "SELECT case_number, title, parties, description, embedding FROM cases WHERE id != %s LIMIT 100;"
                cur.execute(similar_query, (case_id,))
                all_cases = cur.fetchall()
                
                # Calculate similarity in Python
                case_similarities = []
                for sim_num, sim_title, sim_parties, sim_desc, sim_emb in all_cases:
                    try:
                        # Parse embedding
                        if isinstance(sim_emb, str):
                            sim_emb_np = np.array(ast.literal_eval(sim_emb), dtype=np.float32)
                        else:
                            sim_emb_np = np.array(sim_emb, dtype=np.float32)
                        
                        # Calculate cosine similarity
                        norm1 = np.linalg.norm(case_embedding_np)
                        norm2 = np.linalg.norm(sim_emb_np)
                        if norm1 > 0 and norm2 > 0:
                            similarity = np.dot(case_embedding_np, sim_emb_np) / (norm1 * norm2)
                            similarity_pct = max(0.0, similarity * 100.0)
                            
                            case_similarities.append({
                                "case_number": sim_num,
                                "title": sim_title or '',
                                "parties": sim_parties or '',
                                "description": (sim_desc[:200] + "...") if sim_desc and len(sim_desc) > 200 else (sim_desc or ''),
                                "similarity": float(round(similarity_pct, 1))  # Convert to Python float
                            })
                    except:
                        continue
                
                # Sort by similarity and take top 5
                case_similarities.sort(key=lambda x: x['similarity'], reverse=True)
                similar_cases_list = case_similarities[:5]
                print(f"--- SERVER LOG: Found {len(similar_cases_list)} similar cases. ---")
            except Exception as sim_err:
                print(f"--- SERVER LOG: ⚠️ Error finding similar cases: {sim_err} ---")
                traceback.print_exc()
        else: print(f"--- SERVER LOG: ⚠️ Skipping similar case search due to invalid embedding. ---")
        case_data = {
            "case_number": db_case_number, "title": petitioner, "petitioner": petitioner, "respondent": respondent,
            "parties": f"{petitioner} vs {respondent}", "judgment_date": "N/A", "bench": "N/A", # These fields are still missing from DB
            "category": category or "General", "year": "N/A", "judgment_text": description,
            "similar_cases": similar_cases_list
        }
        print(f"--- SERVER LOG: ✅ Details prepared for {db_case_number}. ---"); return jsonify(case_data), 200
    except psycopg2.errors.UndefinedTable as e: print(f"--- SERVER LOG: ❌ SETUP ERROR - {e} ---"); return jsonify({"error": f"Setup error: {e}"}), 503
    except psycopg2.OperationalError as db_err: print(f"--- SERVER LOG: ❌ DB CONNECTION FAILED case details: {db_err} ---"); return jsonify({"error": "Database error"}), 503
    except Exception as e:
        print(f"--- SERVER LOG: ❌ ERROR fetching case details: {e} ---")
        traceback.print_exc()
        return jsonify({"error": f"Could not retrieve details: {str(e)}"}), 500
    finally:
        if conn:
            if cur: cur.close()
            conn.close()
            print("--- SERVER LOG: DB connection closed (case details). ---")

# ==============================================================================
# --- ADVANCED FEATURES ENDPOINTS (Improvements 3-12) ---
# ==============================================================================

@app.route('/api/advanced-search', methods=['GET'])
def advanced_search():
    """Advanced search with date range, court filters, and full-text query."""
    print("\n\n--- SERVER LOG: Advanced Search Request Received ---")
    try:
        query = request.args.get('q', '').strip()
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        court_name = request.args.get('court', '')
        category = request.args.get('category', '')
        year = request.args.get('year', '')
        limit = int(request.args.get('limit', 20))
        
        print(f"--- Query: '{query}', Year: {year}, Category: {category}, Date: {date_from}-{date_to}, Court: {court_name} ---")
        
        if not model:
            print("--- ERROR: AI model not loaded ---")
            return jsonify({"error": "AI model not available"}), 503
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build dynamic SQL with filters
        base_query = """
            SELECT case_number, title, parties, category, description, 
                   judgment_date, court_name, year, embedding
            FROM cases WHERE 1=1
        """
        params = []
        
        if category:
            base_query += " AND category = %s"
            params.append(category)
        
        if date_from:
            base_query += " AND judgment_date >= %s"
            params.append(date_from)
        
        if date_to:
            base_query += " AND judgment_date <= %s"
            params.append(date_to)
        
        if court_name:
            base_query += " AND LOWER(court_name) LIKE LOWER(%s)"
            params.append(f"%{court_name}%")
        
        if year:
            base_query += " AND year = %s"
            params.append(int(year))
            print(f"--- Year filter applied: {year} ---")
        
        print(f"--- Executing query with {len(params)} params: {params} ---")
        print(f"--- SQL Query: {base_query} ---")
        cur.execute(base_query, tuple(params))
        all_cases = cur.fetchall()
        print(f"--- Found {len(all_cases)} cases matching filters ---")
        
        results = []
        if query:
            # Semantic search on filtered results
            print(f"--- Generating embedding for query: '{query}' ---")
            query_embedding = model.encode(query)
            query_vec = np.array(query_embedding, dtype=np.float32)
            
            for row in all_cases:
                case_embedding_str = row[8]
                if case_embedding_str:
                    try:
                        case_vec = np.fromstring(case_embedding_str.strip('[]'), sep=',', dtype=np.float32)
                        similarity = float(np.dot(query_vec, case_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(case_vec)))
                        results.append({
                            "case_number": row[0],
                            "title": row[1],
                            "parties": row[2],
                            "category": row[3],
                            "description": row[4][:300] if row[4] else '',
                            "judgment_date": row[5].strftime('%Y-%m-%d') if row[5] else 'N/A',
                            "court_name": row[6] or 'N/A',
                            "year": row[7],
                            "similarity": similarity
                        })
                    except Exception:
                        continue
            
            results.sort(key=lambda x: x['similarity'], reverse=True)
            results = results[:limit]
        else:
            # No query - just return filtered cases
            for row in all_cases[:limit]:
                results.append({
                    "case_number": row[0],
                    "title": row[1],
                    "parties": row[2],
                    "category": row[3],
                    "description": row[4][:300] if row[4] else '',
                    "judgment_date": row[5].strftime('%Y-%m-%d') if row[5] else 'N/A',
                    "court_name": row[6] or 'N/A',
                    "year": row[7],
                    "similarity": 0.0,
                    "score": 0.0
                })
        
        cur.close()
        conn.close()
        
        # --- Track Search ---
        try:
            user_email = request.headers.get('X-User-Email', 'anonymous')
            conn_track = get_db_connection()
            cur_track = conn_track.cursor()
            print(f"--- SERVER LOG: 📊 Attempting to track advanced search for: {user_email} ---")
            if table_exists(cur_track, 'user_searches'):
                cur_track.execute("""
                    INSERT INTO user_searches (user_email, query, result_count, searched_at)
                    VALUES (%s, %s, %s, %s);
                """, (user_email, query or 'Advanced Search', len(results), datetime.now(timezone.utc)))
                conn_track.commit()
                print(f"--- SERVER LOG: ✅ Successfully tracked advanced search for user: {user_email} ---")
            cur_track.close()
            conn_track.close()
        except Exception as track_error:
            print(f"--- SERVER LOG: ❌ Error tracking advanced search: {track_error} ---")
            traceback.print_exc()
        
        cur.close()
        conn.close()
        
        print(f"--- SERVER LOG: ✅ Advanced search returning {len(results)} results ---")
        return jsonify({"results": results, "total": len(results)}), 200
        
    except Exception as e:
        print(f"--- SERVER LOG: ❌ Advanced search error: {e} ---")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Duplicate endpoints removed - using the ones defined earlier

@app.route('/api/preferences', methods=['GET', 'POST'])
def user_preferences():
    """Get or update user preferences."""
    try:
        user_email = request.args.get('user_email') or request.json.get('user_email')
        
        if not user_email:
            return jsonify({"error": "Missing user_email"}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        if request.method == 'GET':
            cur.execute("""
                SELECT theme, default_category, results_per_page, email_notifications
                FROM user_preferences
                WHERE user_email = %s
            """, (user_email,))
            
            row = cur.fetchone()
            if row:
                prefs = {
                    "theme": row[0],
                    "default_category": row[1],
                    "results_per_page": row[2],
                    "email_notifications": row[3]
                }
            else:
                # Return defaults
                prefs = {
                    "theme": "light",
                    "default_category": "all",
                    "results_per_page": 20,
                    "email_notifications": False
                }
            
            cur.close()
            conn.close()
            return jsonify(prefs), 200
        
        elif request.method == 'POST':
            data = request.json
            theme = data.get('theme', 'light')
            default_category = data.get('default_category', 'all')
            results_per_page = data.get('results_per_page', 20)
            email_notifications = data.get('email_notifications', False)
            
            # Upsert preferences
            cur.execute("""
                INSERT INTO user_preferences 
                (user_email, theme, default_category, results_per_page, email_notifications)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_email) DO UPDATE SET
                    theme = EXCLUDED.theme,
                    default_category = EXCLUDED.default_category,
                    results_per_page = EXCLUDED.results_per_page,
                    email_notifications = EXCLUDED.email_notifications
            """, (user_email, theme, default_category, results_per_page, email_notifications))
            
            conn.commit()
            cur.close()
            conn.close()
            
            return jsonify({"message": "Preferences updated"}), 200
        
    except Exception as e:
        print(f"--- SERVER LOG: ❌ Preferences error: {e} ---")
        return jsonify({"error": str(e)}), 500

# ==============================================================================
# --- CASE DETAILS AI ENHANCEMENTS ---
# ==============================================================================

@app.route('/api/extract-key-facts/<case_number>', methods=['GET'])
def extract_key_facts(case_number):
    """Extract key facts and issues from case description using NLP"""
    try:
        print(f"--- SERVER LOG: Extracting key facts for case: {case_number} ---")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get case description
        cur.execute("SELECT description FROM cases WHERE case_number = %s", (case_number,))
        result = cur.fetchone()
        
        if not result or not result[0]:
            cur.close()
            conn.close()
            return jsonify({"error": "Case not found"}), 404
        
        description = result[0]
        
        # Extract key facts using enhanced NLP patterns
        import re
        
        facts = []
        issues = []
        arguments = []
        
        # Split into sentences (better splitting)
        sentences = re.split(r'(?<=[.!?])\s+', description)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
        
        # Pattern 1: Background/Facts - First 3-5 meaningful sentences
        for i, sent in enumerate(sentences[:8]):
            if any(keyword in sent.lower() for keyword in ['filed', 'alleged', 'charged', 'accused', 'committed', 'case', 'petition', 'complaint', 'incident', 'occurred']):
                facts.append(sent)
                if len(facts) >= 5:
                    break
        
        # Pattern 2: Legal Issues - Look for specific patterns
        for sent in sentences:
            if any(keyword in sent.lower() for keyword in ['whether', 'question', 'issue', 'contention', 'challenged', 'dispute', 'matter', 'controversy']):
                issues.append(sent)
                if len(issues) >= 5:
                    break
        
        # Pattern 3: Arguments - Legal reasoning
        for sent in sentences:
            if any(keyword in sent.lower() for keyword in ['argued', 'submitted', 'contended', 'counsel', 'pleaded', 'relied', 'held that', 'observed']):
                arguments.append(sent)
                if len(arguments) >= 4:
                    break
        
        # Pattern 4: Extract ALL legal provisions
        sections = []
        # IPC/BNS Sections
        sections.extend(re.findall(r'Section\s+\d+[A-Z]?(?:\s*\([a-z0-9]+\))?\s+(?:of\s+)?(?:IPC|Indian Penal Code|BNS)', description, re.IGNORECASE))
        # CrPC Sections
        sections.extend(re.findall(r'Section\s+\d+[A-Z]?(?:\s*\([a-z0-9]+\))?\s+(?:of\s+)?(?:CrPC|Cr\.P\.C\.|Criminal Procedure Code)', description, re.IGNORECASE))
        # Other Acts
        sections.extend(re.findall(r'Section\s+\d+[A-Z]?(?:\s*\([a-z0-9]+\))?\s+(?:of\s+)?(?:the\s+)?[\w\s]+Act', description, re.IGNORECASE))
        # Constitutional Articles
        sections.extend(re.findall(r'Article\s+\d+[A-Z]?(?:\s*\([a-z0-9]+\))?\s+of\s+(?:the\s+)?Constitution', description, re.IGNORECASE))
        
        # Remove duplicates and clean
        facts = list(dict.fromkeys(facts))[:6]
        issues = list(dict.fromkeys(issues))[:5]
        arguments = list(dict.fromkeys(arguments))[:4]
        sections = list(dict.fromkeys(sections))[:12]
        
        # SMARTER FALLBACKS
        # If no facts found, extract informative sentences about the case
        if not facts:
            for sent in sentences[:10]:
                if len(sent) > 50 and any(word in sent.lower() for word in ['petitioner', 'respondent', 'appellant', 'accused', 'plaintiff', 'defendant']):
                    facts.append(sent)
                    if len(facts) >= 4:
                        break
        
        # If still no facts, use first substantive sentences
        if not facts:
            facts = [s for s in sentences[:5] if len(s) > 60]
        
        # If no issues found, extract court's observations/holdings
        if not issues:
            for sent in sentences:
                if any(word in sent.lower() for word in ['held', 'observed', 'found', 'decided', 'concluded', 'ruled', 'judgment', 'order']):
                    issues.append(sent)
                    if len(issues) >= 3:
                        break
        
        # Combine issues and arguments if issues still empty
        if not issues and arguments:
            issues = arguments[:3]
        
        cur.close()
        conn.close()
        
        print(f"--- SERVER LOG: ✅ Extracted {len(facts)} facts, {len(issues)} issues, {len(sections)} sections ---")
        
        return jsonify({
            "facts": facts if facts else ["Case facts are embedded in the full description above."],
            "issues": issues if issues else ["Legal analysis is available in the full judgment text."],
            "arguments": arguments if arguments else [],
            "sections": sections
        }), 200
        
    except Exception as e:
        print(f"--- SERVER LOG: ❌ Key facts extraction error: {e} ---")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/extract-citations/<case_number>', methods=['GET'])
def extract_citations(case_number):
    """Extract legal citations, acts, and case references"""
    try:
        print(f"--- SERVER LOG: Extracting citations for case: {case_number} ---")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT description FROM cases WHERE case_number = %s", (case_number,))
        result = cur.fetchone()
        
        if not result or not result[0]:
            cur.close()
            conn.close()
            return jsonify({"error": "Case not found"}), 404
        
        description = result[0]
        import re
        
        # Extract IPC Sections
        ipc_sections = re.findall(
            r'Section\s+\d+[A-Z]?(?:\s*\([a-z0-9]+\))?\s+(?:of\s+)?(?:the\s+)?(?:IPC|Indian Penal Code)',
            description, re.IGNORECASE
        )
        
        # Extract CrPC Sections
        crpc_sections = re.findall(
            r'Section\s+\d+[A-Z]?(?:\s*\([a-z0-9]+\))?\s+(?:of\s+)?(?:the\s+)?(?:CrPC|Cr\.?P\.?C\.?|Criminal Procedure Code)',
            description, re.IGNORECASE
        )
        
        # Extract Evidence Act Sections
        evidence_sections = re.findall(
            r'Section\s+\d+[A-Z]?(?:\s*\([a-z0-9]+\))?\s+(?:of\s+)?(?:the\s+)?(?:Evidence Act|Indian Evidence Act)',
            description, re.IGNORECASE
        )
        
        # Extract Constitution Articles
        articles = re.findall(
            r'Article\s+\d+[A-Z]?(?:\s*\([a-z0-9]+\))?\s+(?:of\s+)?(?:the\s+)?Constitution',
            description, re.IGNORECASE
        )
        
        # Extract Other Acts (generic pattern)
        other_acts = re.findall(
            r'(?:the\s+)?[\w\s]{3,50}?\s+Act(?:,\s*\d{4})?',
            description
        )
        # Filter out common false positives and clean
        other_acts = [act.strip() for act in other_acts if len(act.strip()) > 10 and 
                      'Evidence Act' not in act and 'IPC' not in act]
        other_acts = list(dict.fromkeys(other_acts))[:15]
        
        # Extract Case Citations (Party v. Party format)
        case_citations = re.findall(
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\s+(?:v\.|vs\.?|versus)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}(?:\s+\(\d{4}\))?',
            description
        )
        
        # Also find citations in format "State of X v. Y"
        state_citations = re.findall(
            r'State\s+of\s+[\w\s]+?\s+(?:v\.|vs\.?|versus)\s+[\w\s]+?(?=\s|,|\.|\()',
            description, re.IGNORECASE
        )
        
        # Combine and clean case citations
        all_citations = case_citations + state_citations
        all_citations = list(dict.fromkeys(all_citations))[:10]
        
        # Remove duplicates from sections
        ipc_sections = list(dict.fromkeys(ipc_sections))
        crpc_sections = list(dict.fromkeys(crpc_sections))
        evidence_sections = list(dict.fromkeys(evidence_sections))
        articles = list(dict.fromkeys(articles))
        
        cur.close()
        conn.close()
        
        print(f"--- SERVER LOG: ✅ Extracted {len(ipc_sections)} IPC, {len(crpc_sections)} CrPC, {len(all_citations)} case citations ---")
        
        return jsonify({
            "ipc_sections": ipc_sections,
            "crpc_sections": crpc_sections,
            "evidence_sections": evidence_sections,
            "articles": articles,
            "other_acts": other_acts,
            "case_citations": all_citations
        }), 200
        
    except Exception as e:
        print(f"--- SERVER LOG: ❌ Citations extraction error: {e} ---")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/similar-cases/<case_number>', methods=['GET'])
def get_similar_cases(case_number):
    """Find similar cases using vector similarity (Real AI!)"""
    try:
        print(f"--- SERVER LOG: Finding similar cases for: {case_number} ---")
        
        limit = request.args.get('limit', 10, type=int)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get the embedding of the current case
        cur.execute("SELECT embedding, description FROM cases WHERE case_number = %s", (case_number,))
        result = cur.fetchone()
        
        if not result or not result[0]:
            cur.close()
            conn.close()
            return jsonify({"error": "Case not found or no embedding"}), 404
        
        current_embedding = result[0]
        current_desc = result[1]
        
        print(f"--- SERVER LOG: Current case embedding retrieved ---")
        
        # Get all other cases with embeddings
        cur.execute("""
            SELECT 
                case_number,
                title,
                parties,
                category,
                description,
                embedding
            FROM cases
            WHERE case_number != %s AND embedding IS NOT NULL
            LIMIT 500
        """, (case_number,))
        
        all_cases = cur.fetchall()
        print(f"--- SERVER LOG: Found {len(all_cases)} cases to compare ---")
        
        # Calculate similarities using numpy
        similarities = []
        for case in all_cases:
            case_num, title, parties, category, desc, embedding = case
            
            # Convert embeddings to numpy arrays
            if isinstance(current_embedding, str):
                current_emb = np.array(ast.literal_eval(current_embedding))
            else:
                current_emb = np.array(current_embedding)
                
            if isinstance(embedding, str):
                case_emb = np.array(ast.literal_eval(embedding))
            else:
                case_emb = np.array(embedding)
            
            # Calculate cosine similarity
            similarity = np.dot(current_emb, case_emb) / (np.linalg.norm(current_emb) * np.linalg.norm(case_emb))
            
            similarities.append({
                "case_number": case_num,
                "title": title or "Unknown",
                "parties": parties or "Unknown",
                "category": category or "general",
                "description": (desc or "No description")[:300],
                "similarity": int(similarity * 100)
            })
        
        # Sort by similarity (highest first) and get top N
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        results = similarities[:limit]
        
        cur.close()
        conn.close()
        
        print(f"--- SERVER LOG: ✅ Found {len(results)} similar cases, top similarity: {results[0]['similarity'] if results else 0}% ---")
        
        return jsonify({
            "similar_cases": results,
            "total": len(results)
        }), 200
        
    except Exception as e:
        print(f"--- SERVER LOG: ❌ Similar cases error: {e} ---")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ==============================================================================
# --- GOOGLE OAUTH ROUTES ---
# ==============================================================================

@app.route('/auth/google/login')
def google_login():
    """Initiate Google OAuth login"""
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        
        if not user_info:
            return jsonify({"error": "Failed to get user info"}), 400
        
        email = user_info.get('email')
        name = user_info.get('name')
        picture = user_info.get('picture')
        
        # Store user in session
        session['user'] = {
            'email': email,
            'name': name,
            'picture': picture,
            'auth_method': 'google'
        }
        
        # Check if user exists in database, if not create them
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cur.fetchone()
        
        if not existing_user:
            # Create new user
            cur.execute("""
                INSERT INTO users (email, name, password, created_at)
                VALUES (%s, %s, %s, %s)
            """, (email, name, 'oauth_google', datetime.now(timezone.utc)))
            conn.commit()
            print(f"--- SERVER LOG: ✅ New Google user created: {email} ---")
        
        cur.close()
        conn.close()
        
        # Redirect to frontend with success
        return redirect('http://127.0.0.1:5000/DBMS%20UI/index.html?login=success')
        
    except Exception as e:
        print(f"--- SERVER LOG: ❌ OAuth callback error: {e} ---")
        traceback.print_exc()
        return redirect('http://127.0.0.1:5000/DBMS%20UI/login.html?error=oauth_failed')

@app.route('/auth/google/logout')
def google_logout():
    """Logout user"""
    session.pop('user', None)
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/auth/user')
def get_current_user():
    """Get current logged-in user"""
    user = session.get('user')
    if user:
        return jsonify({"user": user, "logged_in": True}), 200
    else:
        return jsonify({"logged_in": False}), 200

# ==============================================================================
# --- MAIN EXECUTION BLOCK ---
# ==============================================================================
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') != 'production'
    
    print("--- Starting Flask Server ---")
    print(f"API will be available at http://0.0.0.0:{port}")
    print("Ensure PostgreSQL is running and database 'legal_search' exists.")
    print("Ensure required tables (cases, users*, user_searches*, user_bookmarks*) exist. (*optional for core search)")
    print("Press CTRL+C to stop the server.")
    
    app.run(debug=debug, host='0.0.0.0', port=port)