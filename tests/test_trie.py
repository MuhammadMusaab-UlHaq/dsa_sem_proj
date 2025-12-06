"""
Quick test script to verify Trie implementation for Task 1
"""
from src.structures import Trie

def test_trie_basic():
    """Test basic Trie operations"""
    print("=== Testing Trie Implementation ===\n")
    
    # Create Trie instance
    trie = Trie()
    
    # Test data - simulating POIs
    test_pois = [
        {"name": "NUST Gate 1", "type": "gate", "lat": 33.6415, "lon": 72.9910},
        {"name": "NUST Gate 2", "type": "gate", "lat": 33.6420, "lon": 72.9915},
        {"name": "Concordia 1", "type": "hostel", "lat": 33.6425, "lon": 72.9920},
        {"name": "Concordia 2", "type": "hostel", "lat": 33.6430, "lon": 72.9925},
        {"name": "Conference Hall", "type": "building", "lat": 33.6435, "lon": 72.9930},
        {"name": "Cafeteria", "type": "cafe", "lat": 33.6440, "lon": 72.9935},
        {"name": "Central Library", "type": "library", "lat": 33.6445, "lon": 72.9940},
        {"name": "Gate 3 Service Entry", "type": "gate", "lat": 33.6450, "lon": 72.9945},
    ]
    
    # Insert POIs into Trie
    print("1. Inserting POIs into Trie...")
    for poi in test_pois:
        trie.insert(poi['name'], poi)
    print(f"   ✅ Inserted {len(test_pois)} POIs\n")
    
    # Test 1: Search for "gate"
    print("2. Testing prefix search: 'gate'")
    results = trie.search_prefix("gate")
    print(f"   Found {len(results)} results:")
    for r in results:
        print(f"   - {r['name']} ({r['data']['type']})")
    print()
    
    # Test 2: Search for "conc"
    print("3. Testing prefix search: 'conc'")
    results = trie.search_prefix("conc")
    print(f"   Found {len(results)} results:")
    for r in results:
        print(f"   - {r['name']} ({r['data']['type']})")
    print()
    
    # Test 3: Search for "nust"
    print("4. Testing prefix search: 'nust'")
    results = trie.search_prefix("nust")
    print(f"   Found {len(results)} results:")
    for r in results:
        print(f"   - {r['name']} ({r['data']['type']})")
    print()
    
    # Test 4: Search for "caf"
    print("5. Testing prefix search: 'caf'")
    results = trie.search_prefix("caf")
    print(f"   Found {len(results)} results:")
    for r in results:
        print(f"   - {r['name']} ({r['data']['type']})")
    print()
    
    # Test 5: Search for non-existent prefix
    print("6. Testing prefix search: 'xyz' (should find nothing)")
    results = trie.search_prefix("xyz")
    print(f"   Found {len(results)} results")
    if not results:
        print("   ✅ Correctly returns empty list for non-existent prefix")
    print()
    
    # Test 6: Case insensitivity
    print("7. Testing case insensitivity: 'GATE' vs 'gate'")
    results_upper = trie.search_prefix("GATE")
    results_lower = trie.search_prefix("gate")
    print(f"   'GATE' found: {len(results_upper)} results")
    print(f"   'gate' found: {len(results_lower)} results")
    if len(results_upper) == len(results_lower):
        print("   ✅ Case insensitive search working correctly")
    print()
    
    print("=== All Trie Tests Completed ✅ ===")

if __name__ == "__main__":
    test_trie_basic()
