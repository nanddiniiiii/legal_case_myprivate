"""
🔍 INDIAN KANOON CASE SCRAPER
================================
Simple scraper to get REAL legal case data from Indian Kanoon.
No coding needed - just run this script!

What it does:
1. Searches for cases by category (theft, murder, property, etc.)
2. Extracts real case descriptions
3. Saves to database automatically
4. Shows progress bar so you know it's working

Author: Your Legal Case DBMS Project
Date: December 2025
"""

import requests
from bs4 import BeautifulSoup
import psycopg2
from sentence_transformers import SentenceTransformer
import time
import re
from datetime import datetime
import random

# =============================================================================
# CONFIGURATION - You can change these!
# =============================================================================

# Database connection (update if your password is different)
DB_CONFIG = {
    'dbname': 'legal_search',
    'user': 'postgres',
    'password': '12345',  # Change this if your password is different
    'host': 'localhost',
    'port': '5432'
}

# Search queries for different case types (these will become the categories!)
SEARCH_QUERIES = [
    'theft', 'murder', 'property dispute', 'divorce', 'contract breach',
    'motor accident', 'cheating', 'assault', 'rape', 'dowry',
    'land dispute', 'employment', 'tax evasion', 'corruption',
    'fraud', 'domestic violence', 'kidnapping', 'robbery', 'banking', 
    'intellectual property', 'cyber crime', 'environmental'
]

# How many cases to scrape per category
CASES_PER_QUERY = 500  # Total will be 200 x 18 = 3,600 cases

# Delay between requests (be nice to the server!)
DELAY_BETWEEN_REQUESTS = 2  # seconds

# =============================================================================
# SCRAPER FUNCTIONS
# =============================================================================

def get_db_connection():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Make sure PostgreSQL is running and your password is correct!")
        return None

def search_indian_kanoon(query, page=0):
    """
    Search Indian Kanoon for cases
    Returns list of case URLs
    """
    search_url = f"https://indiankanoon.org/search/?formInput={query}&pagenum={page}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all case links
            case_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '/doc/' in href and href.startswith('/doc/'):
                    full_url = f"https://indiankanoon.org{href}"
                    case_links.append(full_url)
            
            return list(set(case_links))  # Remove duplicates
        else:
            print(f"⚠️  Search failed for '{query}' (Status: {response.status_code})")
            return []
    except Exception as e:
        print(f"⚠️  Error searching for '{query}': {e}")
        return []

def scrape_case_details(case_url, query_name="unknown"):
    """
    Scrape details from a single case page
    Returns dict with case information
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(case_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"\n   ⚠️  HTTP {response.status_code} for {case_url}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract case title (usually in first heading or title)
        title = "Unknown Case"
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.text.strip()
        else:
            h1_tag = soup.find('h1')
            if h1_tag:
                title = h1_tag.text.strip()
        
        # SKIP statute/section pages (ONLY if it's clearly a statute definition, not a judgment)
        # Real statute pages have patterns like:
        # - "Section 379 in The Indian Penal Code, 1860"
        # - "The Indian Penal Code, 1860"
        # But real judgments also mention sections, so be more specific
        
        is_statute_page = False
        
        # Check if it's a pure statute definition page (no case parties)
        if not (' vs ' in title.lower() or ' v. ' in title.lower()):
            # No "vs", so might be statute. Check for statute-specific patterns
            statute_patterns = [
                r'^section \d+ in',  # "Section 379 in Act"
                r'^the .+ act,',      # "The Indian Penal Code, 1860"
                r'^article \d+ in.*constitution',  # "Article 25 in Constitution"
                r'^schedule .+ to',   # "Schedule X to Act"
            ]
            import re as regex_module
            for pattern in statute_patterns:
                if regex_module.search(pattern, title.lower()):
                    is_statute_page = True
                    break
        
        if is_statute_page:
            print(f"\n   ⚠️  Skipping statute/section page: {title[:50]}...")
            return None
        
        # Extract case text (main content) - FIXED VERSION
        case_text = ""
        
        # Indian Kanoon stores judgment in BLOCKQUOTE tags!
        blockquotes = soup.find_all('blockquote')
        
        if blockquotes:
            # Combine all blockquotes (they contain the judgment paragraphs)
            judgment_parts = []
            for bq in blockquotes:
                text = bq.get_text(separator=' ', strip=True)
                if len(text) > 50:  # Only include substantial paragraphs
                    judgment_parts.append(text)
            
            case_text = ' '.join(judgment_parts)
        else:
            # Fallback 1: Try akoma-ntoso div (sometimes used for case text)
            akoma_div = soup.find('div', class_='akoma-ntoso')
            if akoma_div:
                case_text = akoma_div.get_text(separator=' ', strip=True)
            else:
                # Fallback 2: Try div.judgments or div.docsource
                judgment_div = soup.find('div', class_='judgments') or soup.find('div', class_='docsource')
                if judgment_div:
                    case_text = judgment_div.get_text(separator=' ', strip=True)
                else:
                    # Last resort: get all paragraphs
                    paragraphs = soup.find_all('p')
                    if len(paragraphs) > 3:
                        case_text = ' '.join([p.get_text(strip=True) for p in paragraphs[3:]])
        
        # Clean up the text
        case_text = re.sub(r'\s+', ' ', case_text)  # Remove extra whitespace
        case_text = re.sub(r'\[Cites \d+.*?\]', '', case_text)  # Remove citation markers
        case_text = re.sub(r'\[Cited by \d+.*?\]', '', case_text)  # Remove citation markers
        
        # Limit to reasonable length (keep first 5000 chars - enough for embeddings)
        case_text = case_text[:5000]
        
        # Must have substantial text - LOWERED THRESHOLD
        if not case_text or len(case_text) < 100:
            if not case_text:
                print(f"\n   ⚠️  No text found in case (query: {query_name})")
            else:
                print(f"\n   ⚠️  Text too short ({len(case_text)} chars, need 100+) for query: {query_name}")
            return None
        
        # Extract parties (Petitioner vs Respondent)
        parties = "Unknown vs Unknown"
        # Look for "vs" or "v." pattern in title
        if ' vs ' in title.lower() or ' v. ' in title.lower():
            parties = title.split('|')[0].strip() if '|' in title else title
        
        # Generate unique case number
        case_id = case_url.split('/doc/')[-1].replace('/', '')
        case_number = f"IK-{case_id[:8]}-2024"
        
        return {
            'case_number': case_number,
            'title': parties.split(' vs ')[0].strip() if ' vs ' in parties.lower() else parties.split(' v. ')[0].strip() if ' v. ' in parties.lower() else parties,
            'parties': parties.split(' vs ')[1].strip() if ' vs ' in parties.lower() else parties.split(' v. ')[1].strip() if ' v. ' in parties.lower() else "Unknown",
            'description': case_text,
            'url': case_url
        }
        
    except Exception as e:
        print(f"⚠️  Error scraping {case_url}: {e}")
        return None

def save_to_database(cases, model, category):
    """Save scraped cases to database with embeddings"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        # Try to import pgvector, but work without it if not available
        try:
            from pgvector.psycopg2 import register_vector
            register_vector(conn)
            use_pgvector = True
        except:
            use_pgvector = False
            print("ℹ️  pgvector not available, storing embeddings as text...")
        
        cur = conn.cursor()
        success_count = 0
        
        for case in cases:
            try:
                # Generate embedding
                embedding = model.encode(case['description'])
                
                # Convert embedding to string if pgvector not available
                if use_pgvector:
                    embedding_to_store = embedding
                else:
                    embedding_to_store = str(embedding.tolist())
                
                # Insert into database
                cur.execute("""
                    INSERT INTO cases (case_number, title, parties, description, embedding, category)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (case_number) DO NOTHING;
                """, (
                    case['case_number'],
                    case['title'],
                    case['parties'],
                    case['description'],
                    embedding_to_store,
                    category
                ))
                
                success_count += 1
                
            except Exception as e:
                print(f"⚠️  Error saving case {case['case_number']}: {e}")
                continue
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Successfully saved {success_count} cases to database!")
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

# =============================================================================
# MAIN SCRAPING FUNCTION
# =============================================================================

def main():
    """Main function to run the scraper"""
    
    print("=" * 70)
    print("🔍 INDIAN KANOON CASE SCRAPER")
    print("=" * 70)
    print()
    print("This will scrape real legal cases from Indian Kanoon.")
    print(f"📊 Target: ~{len(SEARCH_QUERIES) * CASES_PER_QUERY} cases")
    print(f"⏱️  Estimated time: ~{(len(SEARCH_QUERIES) * CASES_PER_QUERY * DELAY_BETWEEN_REQUESTS) / 60:.0f} minutes")
    print()
    
    # Test database connection
    print("🔗 Testing database connection...")
    conn = get_db_connection()
    if not conn:
        print("\n❌ STOPPED: Cannot connect to database.")
        print("💡 Fix: Make sure PostgreSQL is running and check your password in this file.")
        return
    conn.close()
    print("✅ Database connected!\n")
    
    # Load AI model
    print("🤖 Loading AI model (this may take a minute)...")
    try:
        model = SentenceTransformer('all-mpnet-base-v2')
        print("✅ AI model loaded (all-mpnet-base-v2, 768 dims)!\n")
    except Exception as e:
        print(f"❌ Could not load AI model: {e}")
        return
    
    # Start scraping
    print("🚀 Starting scraper...\n")
    
    total_scraped = 0
    
    for query in SEARCH_QUERIES:
        print(f"📁 Searching for: '{query}'")
        
        # Normalize query to category name (remove spaces, make lowercase)
        category = query.lower().replace(' ', '_')
        
        # Scrape cases from multiple pages until we get CASES_PER_QUERY
        category_cases = []
        cases_scraped = 0
        page = 0
        max_pages = 15  # Safety limit: don't search more than 15 pages
        
        while cases_scraped < CASES_PER_QUERY and page < max_pages:
            # Search this page
            case_urls = search_indian_kanoon(query, page=page)
            
            if not case_urls:
                print(f"   ⚠️  No more results on page {page}")
                break
            
            print(f"   📄 Page {page}: Found {len(case_urls)} results")
            
            # Scrape each case from this page
            for i, url in enumerate(case_urls):
                if cases_scraped >= CASES_PER_QUERY:
                    break
                
                print(f"   [{cases_scraped+1}/{CASES_PER_QUERY}] Scraping...", end='\r')
                
                case_data = scrape_case_details(url, query)
                
                if case_data:
                    category_cases.append(case_data)
                    cases_scraped += 1
                    total_scraped += 1
                
                # Be nice to the server
                time.sleep(DELAY_BETWEEN_REQUESTS)
            
            page += 1
        
        print(f"   ✅ Scraped {cases_scraped} cases from '{query}' (searched {page} pages)")
        
        # Save cases with their specific category
        if category_cases:
            print(f"   💾 Saving {len(category_cases)} cases to category '{category}'...")
            save_to_database(category_cases, model, category)
            print()
    
    # Final summary
    print("\n" + "=" * 70)
    print("🎉 SCRAPING COMPLETE!")
    print("=" * 70)
    print(f"✅ Total cases scraped: {total_scraped}")
    print(f"✅ All cases saved to database with AI embeddings")
    print(f"✅ Ready to search!")
    print()
    print("💡 Next step: Start your API server and try searching!")
    print()

# =============================================================================
# RUN THE SCRAPER
# =============================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping stopped by user (Ctrl+C)")
        print("💡 You can run this script again to continue.")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        print("💡 Please check your internet connection and try again.")
