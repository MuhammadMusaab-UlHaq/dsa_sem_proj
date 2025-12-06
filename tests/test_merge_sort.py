"""
Test suite for Task 3: Merge Sort (Nearby POI Sorter)
Tests the merge_sort function with various scenarios
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from structures import merge_sort
import random

def test_basic_sorting():
    """Test 1: Sort simple list of numbers"""
    print("=== Test 1: Basic number sorting ===")
    
    data = [64, 34, 25, 12, 22, 11, 90]
    sorted_data = merge_sort(data, key=lambda x: x)
    
    expected = [11, 12, 22, 25, 34, 64, 90]
    
    print(f"Original: {data}")
    print(f"Sorted:   {sorted_data}")
    print(f"Expected: {expected}")
    
    assert sorted_data == expected, f"Expected {expected}, got {sorted_data}"
    print("✅ Test 1 PASSED\n")


def test_poi_sorting_by_distance():
    """Test 2: Sort POIs by distance (main use case)"""
    print("=== Test 2: Sort POIs by distance ===")
    
    pois = [
        {'name': 'Cafeteria', 'distance': 250},
        {'name': 'Library', 'distance': 150},
        {'name': 'Gate 1', 'distance': 500},
        {'name': 'Hostel', 'distance': 100},
        {'name': 'Lab', 'distance': 300},
    ]
    
    sorted_pois = merge_sort(pois, key=lambda x: x['distance'])
    
    print("Sorted POIs by distance:")
    for poi in sorted_pois:
        print(f"  {poi['name']}: {poi['distance']}m")
    
    # Verify order
    distances = [poi['distance'] for poi in sorted_pois]
    expected_distances = [100, 150, 250, 300, 500]
    
    assert distances == expected_distances, f"Expected {expected_distances}, got {distances}"
    assert sorted_pois[0]['name'] == 'Hostel', "Closest should be Hostel"
    assert sorted_pois[-1]['name'] == 'Gate 1', "Farthest should be Gate 1"
    
    print("✅ Test 2 PASSED\n")


def test_empty_list():
    """Test 3: Handle empty list"""
    print("=== Test 3: Empty list ===")
    
    data = []
    sorted_data = merge_sort(data, key=lambda x: x)
    
    assert sorted_data == [], "Empty list should return empty list"
    print("Result: []")
    print("✅ Test 3 PASSED\n")


def test_single_element():
    """Test 4: Single element list"""
    print("=== Test 4: Single element ===")
    
    data = [42]
    sorted_data = merge_sort(data, key=lambda x: x)
    
    assert sorted_data == [42], "Single element should return same list"
    print("Result: [42]")
    print("✅ Test 4 PASSED\n")


def test_already_sorted():
    """Test 5: Already sorted list"""
    print("=== Test 5: Already sorted list ===")
    
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    sorted_data = merge_sort(data, key=lambda x: x)
    
    assert sorted_data == data, "Already sorted list should remain same"
    print("Original: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]")
    print("Sorted:   [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]")
    print("✅ Test 5 PASSED\n")


def test_reverse_sorted():
    """Test 6: Reverse sorted list"""
    print("=== Test 6: Reverse sorted list ===")
    
    data = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    sorted_data = merge_sort(data, key=lambda x: x)
    
    expected = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    assert sorted_data == expected, f"Expected {expected}, got {sorted_data}"
    print("Original: [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]")
    print("Sorted:   [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]")
    print("✅ Test 6 PASSED\n")


def test_duplicates():
    """Test 7: List with duplicate values"""
    print("=== Test 7: List with duplicates ===")
    
    data = [5, 2, 8, 2, 9, 1, 5, 5]
    sorted_data = merge_sort(data, key=lambda x: x)
    
    expected = [1, 2, 2, 5, 5, 5, 8, 9]
    
    assert sorted_data == expected, f"Expected {expected}, got {sorted_data}"
    print(f"Original: {data}")
    print(f"Sorted:   {sorted_data}")
    print("✅ Test 7 PASSED\n")


def test_negative_numbers():
    """Test 8: List with negative numbers"""
    print("=== Test 8: Negative numbers ===")
    
    data = [-5, 3, -1, 7, -9, 0, 4]
    sorted_data = merge_sort(data, key=lambda x: x)
    
    expected = [-9, -5, -1, 0, 3, 4, 7]
    
    assert sorted_data == expected, f"Expected {expected}, got {sorted_data}"
    print(f"Original: {data}")
    print(f"Sorted:   {sorted_data}")
    print("✅ Test 8 PASSED\n")


def test_large_dataset():
    """Test 9: Large dataset (100 elements)"""
    print("=== Test 9: Large dataset (100 elements) ===")
    
    import time
    
    # Generate random data
    data = [random.randint(1, 1000) for _ in range(100)]
    
    start_time = time.time()
    sorted_data = merge_sort(data, key=lambda x: x)
    elapsed = time.time() - start_time
    
    # Verify it's sorted
    for i in range(len(sorted_data) - 1):
        assert sorted_data[i] <= sorted_data[i + 1], "List is not properly sorted"
    
    print(f"Sorted 100 elements in {elapsed:.4f} seconds")
    print(f"First 5: {sorted_data[:5]}")
    print(f"Last 5:  {sorted_data[-5:]}")
    print("✅ Test 9 PASSED\n")


def test_complex_objects():
    """Test 10: Sort complex objects by different keys"""
    print("=== Test 10: Complex objects with different keys ===")
    
    students = [
        {'name': 'Alice', 'grade': 85, 'age': 20},
        {'name': 'Bob', 'grade': 92, 'age': 19},
        {'name': 'Charlie', 'grade': 78, 'age': 21},
        {'name': 'Diana', 'grade': 95, 'age': 20},
    ]
    
    # Sort by grade
    by_grade = merge_sort(students, key=lambda s: s['grade'])
    print("Sorted by grade:")
    for s in by_grade:
        print(f"  {s['name']}: {s['grade']}")
    
    assert by_grade[0]['name'] == 'Charlie', "Lowest grade should be Charlie"
    assert by_grade[-1]['name'] == 'Diana', "Highest grade should be Diana"
    
    # Sort by name (alphabetically)
    by_name = merge_sort(students, key=lambda s: s['name'])
    print("\nSorted by name:")
    for s in by_name:
        print(f"  {s['name']}")
    
    assert by_name[0]['name'] == 'Alice', "First alphabetically should be Alice"
    
    print("✅ Test 10 PASSED\n")


def test_stability():
    """Test 11: Verify merge sort is stable"""
    print("=== Test 11: Stability test ===")
    
    # Items with same key should maintain original order
    data = [
        {'name': 'A', 'priority': 1, 'order': 1},
        {'name': 'B', 'priority': 2, 'order': 2},
        {'name': 'C', 'priority': 1, 'order': 3},
        {'name': 'D', 'priority': 2, 'order': 4},
    ]
    
    sorted_data = merge_sort(data, key=lambda x: x['priority'])
    
    # Items with priority 1: A should come before C (original order)
    priority_1_items = [item for item in sorted_data if item['priority'] == 1]
    
    print("Items with priority 1:")
    for item in priority_1_items:
        print(f"  {item['name']} (original order: {item['order']})")
    
    assert priority_1_items[0]['name'] == 'A', "Stable sort should preserve order"
    assert priority_1_items[1]['name'] == 'C', "Stable sort should preserve order"
    
    print("✅ Test 11 PASSED (Merge sort is stable)\n")


def test_no_builtin_sort():
    """Test 12: Verify we're not using Python's built-in sort"""
    print("=== Test 12: Verify no built-in sort usage ===")
    
    import inspect
    import structures
    import re
    
    # Get source code of merge_sort and _merge functions
    merge_sort_source = inspect.getsource(structures.merge_sort)
    merge_helper_source = inspect.getsource(structures._merge)
    
    # Remove comments and docstrings to avoid false positives
    merge_sort_code = re.sub(r'#.*', '', merge_sort_source)
    merge_sort_code = re.sub(r'""".*?"""', '', merge_sort_code, flags=re.DOTALL)
    merge_sort_code = re.sub(r"'''.*?'''", '', merge_sort_code, flags=re.DOTALL)
    
    merge_helper_code = re.sub(r'#.*', '', merge_helper_source)
    merge_helper_code = re.sub(r'""".*?"""', '', merge_helper_code, flags=re.DOTALL)
    
    # Check that .sort() or sorted() are not in the actual code
    assert '.sort(' not in merge_sort_code, "merge_sort should not use .sort()"
    assert 'sorted(' not in merge_sort_code, "merge_sort should not use sorted()"
    assert '.sort(' not in merge_helper_code, "_merge should not use .sort()"
    assert 'sorted(' not in merge_helper_code, "_merge should not use sorted()"
    
    print("Verified: merge_sort and _merge do NOT use Python's built-in .sort() or sorted()")
    print("✅ Test 12 PASSED\n")


def run_all_tests():
    """Run all merge sort tests"""
    print("=" * 70)
    print("TASK 3: MERGE SORT TEST SUITE")
    print("=" * 70)
    print()
    
    tests = [
        test_basic_sorting,
        test_poi_sorting_by_distance,
        test_empty_list,
        test_single_element,
        test_already_sorted,
        test_reverse_sorted,
        test_duplicates,
        test_negative_numbers,
        test_large_dataset,
        test_complex_objects,
        test_stability,
        test_no_builtin_sort,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test_func.__name__} FAILED: {e}\n")
            failed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} ERROR: {e}\n")
            failed += 1
    
    print("=" * 70)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print("\n🎉 All tests passed! Merge sort implementation is correct.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the implementation.")


if __name__ == "__main__":
    run_all_tests()
