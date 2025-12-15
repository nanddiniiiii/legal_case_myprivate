import requests
import json

def test_api_search(query):
    try:
        print(f"=== TESTING API SEARCH FOR: '{query}' ===\n")

        # Ensure the Flask API server (api.py) is running before executing this
        response = requests.get(f'http://127.0.0.1:5000/search?query={query}')

        if response.status_code == 200:
            results = response.json()

            if results:
                print(f"Found {len(results)} results:\n")

                for i, result in enumerate(results[:5], 1):
                    print(f"RESULT {i}:")
                    print(f"  Score: {result.get('score', 'N/A')}%") # Use .get for safety
                    print(f"  Title: {result.get('title', 'N/A')}")
                    # *** FIXED LINE BELOW: Use 'description' instead of 'judgment_text' ***
                    print(f"  Content: {result.get('description', 'No content available.')[:150]}...") 
                    print("-" * 60)

                # Score analysis
                # Use list comprehension with .get() to handle potential missing scores gracefully
                scores = [r.get('score', 0) for r in results if r.get('score') is not None]
                if scores:
                    print(f"\nSCORE ANALYSIS:")
                    print(f"  Highest Score: {max(scores):.1f}%")
                    print(f"  Lowest Score: {min(scores):.1f}%")
                    print(f"  Average Score: {sum(scores)/len(scores):.1f}%")
                else:
                     print("\nSCORE ANALYSIS: No valid scores found in results.")

            else:
                print("✅ API returned successfully, but no matching results were found.")

        else:
            print(f"❌ API Error: Status Code {response.status_code}")
            try:
                error_details = response.json()
                print(f"   Error Details: {error_details.get('error', 'No specific error message provided.')}")
            except json.JSONDecodeError:
                print(f"   Response Content: {response.text}") # Print raw text if not valid JSON

    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        print("   Is the Flask API server (`api.py`) running at http://127.0.0.1:5000?")
    except KeyError as e:
        print(f"❌ Key Error: Could not find key '{e}' in the API response.")
        print(f"   Check if the API response structure matches what the test script expects.")
        if results and len(results) > 0:
             print(f"   Sample result keys: {list(results[0].keys())}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Make sure your api.py is running in another terminal first!
    test_api_search("theft")
    print("\n" + "="*80 + "\n")
    test_api_search("contract")
    print("\n" + "="*80 + "\n")
    test_api_search("murder by poisoning") # Add another test