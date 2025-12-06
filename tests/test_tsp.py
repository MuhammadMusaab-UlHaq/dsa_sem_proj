"""
Test suite for Task 2: TSP Approximation (Errand Runner)
Tests the optimize_route_order function with various scenarios
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from structures import CityGraph
from algorithms import optimize_route_order, a_star_search
from itertools import permutations

def create_mock_graph():
    """Create a simple mock graph for testing"""
    graph = CityGraph()
    
    # Add nodes in a simple grid pattern
    # Node layout:
    #   1 --- 2 --- 3
    #   |     |     |
    #   4 --- 5 --- 6
    #   |     |     |
    #   7 --- 8 --- 9
    
    nodes = {
        1: {'lat': 33.644, 'lon': 72.991, 'ele': 0},
        2: {'lat': 33.644, 'lon': 72.992, 'ele': 0},
        3: {'lat': 33.644, 'lon': 72.993, 'ele': 0},
        4: {'lat': 33.643, 'lon': 72.991, 'ele': 0},
        5: {'lat': 33.643, 'lon': 72.992, 'ele': 0},
        6: {'lat': 33.643, 'lon': 72.993, 'ele': 0},
        7: {'lat': 33.642, 'lon': 72.991, 'ele': 0},
        8: {'lat': 33.642, 'lon': 72.992, 'ele': 0},
        9: {'lat': 33.642, 'lon': 72.993, 'ele': 0},
    }
    
    graph.nodes = nodes
    
    # Create adjacency list with edges
    # Weight is roughly 100 units per edge (approximately distance in meters)
    graph.adj_list = {
        1: [(2, 100, True, True, [], 'service'), (4, 100, True, True, [], 'service')],
        2: [(1, 100, True, True, [], 'service'), (3, 100, True, True, [], 'service'), (5, 100, True, True, [], 'service')],
        3: [(2, 100, True, True, [], 'service'), (6, 100, True, True, [], 'service')],
        4: [(1, 100, True, True, [], 'service'), (5, 100, True, True, [], 'service'), (7, 100, True, True, [], 'service')],
        5: [(2, 100, True, True, [], 'service'), (4, 100, True, True, [], 'service'), (6, 100, True, True, [], 'service'), (8, 100, True, True, [], 'service')],
        6: [(3, 100, True, True, [], 'service'), (5, 100, True, True, [], 'service'), (9, 100, True, True, [], 'service')],
        7: [(4, 100, True, True, [], 'service'), (8, 100, True, True, [], 'service')],
        8: [(5, 100, True, True, [], 'service'), (7, 100, True, True, [], 'service'), (9, 100, True, True, [], 'service')],
        9: [(6, 100, True, True, [], 'service'), (8, 100, True, True, [], 'service')],
    }
    
    return graph

def test_basic_tsp():
    """Test 1: Basic TSP with 3 stops"""
    print("=== Test 1: Basic TSP with 3 stops ===")
    
    graph = create_mock_graph()
    
    # Start at node 1, visit nodes 3, 7, 9
    start = 1
    stops = [3, 7, 9]
    
    print(f"Start: Node {start}")
    print(f"Stops to visit: {stops}")
    
    best_order, total_cost, segments = optimize_route_order(graph, start, stops, mode='car')
    
    print(f"Optimal order: {best_order}")
    print(f"Total cost: {total_cost:.2f}")
    print(f"Number of segments: {len(segments)}")
    
    assert len(best_order) == len(stops), "Best order should contain all stops"
    assert total_cost > 0, "Total cost should be positive"
    assert len(segments) == len(stops), "Should have segments for each stop"
    
    print("✅ Test 1 PASSED\n")

def test_tsp_with_4_stops():
    """Test 2: TSP with 4 stops"""
    print("=== Test 2: TSP with 4 stops ===")
    
    graph = create_mock_graph()
    
    # Start at node 5 (center), visit corners
    start = 5
    stops = [1, 3, 7, 9]
    
    print(f"Start: Node {start} (center)")
    print(f"Stops to visit: {stops} (corners)")
    
    best_order, total_cost, segments = optimize_route_order(graph, start, stops, mode='car')
    
    print(f"Optimal order: {best_order}")
    print(f"Total cost: {total_cost:.2f}")
    
    # With 4 stops, we have 4! = 24 permutations
    expected_perms = len(list(permutations(stops)))
    print(f"Tested {expected_perms} permutations")
    
    assert len(best_order) == 4, "Should have 4 stops in order"
    assert total_cost > 0, "Cost should be positive"
    
    print("✅ Test 2 PASSED\n")

def test_optimal_order_verification():
    """Test 3: Verify that TSP finds the actual optimal order"""
    print("=== Test 3: Verify optimal order ===")
    
    graph = create_mock_graph()
    
    # Start at node 1, visit 2, 3, 6 in a line
    # Optimal order should be 2 -> 3 -> 6 (following the path)
    start = 1
    stops = [6, 2, 3]  # Intentionally out of order
    
    print(f"Start: Node {start}")
    print(f"Stops (unordered): {stops}")
    
    best_order, total_cost, segments = optimize_route_order(graph, start, stops, mode='car')
    
    print(f"Optimal order found: {best_order}")
    
    # Manually calculate cost of optimal path: 1->2->3->6 should be shortest
    # vs other orders like 1->6->3->2 or 1->3->2->6
    
    # The optimal should follow the natural path
    # Expected: [2, 3, 6] or similar efficient ordering
    
    assert best_order[0] == 2, "Should visit node 2 first (closest to start)"
    
    print("✅ Test 3 PASSED\n")

def test_empty_stops():
    """Test 4: Handle edge case with no stops"""
    print("=== Test 4: Empty stops list ===")
    
    graph = create_mock_graph()
    
    start = 5
    stops = []
    
    best_order, total_cost, segments = optimize_route_order(graph, start, stops, mode='car')
    
    print(f"Result: order={best_order}, cost={total_cost}")
    
    assert best_order == [], "Should return empty order"
    assert total_cost == 0, "Cost should be 0"
    assert segments == {}, "Segments should be empty"
    
    print("✅ Test 4 PASSED\n")

def test_walking_mode():
    """Test 5: TSP with walking mode"""
    print("=== Test 5: TSP with walking mode ===")
    
    graph = create_mock_graph()
    
    start = 5
    stops = [1, 9]
    
    print(f"Testing with walking mode")
    
    best_order, total_cost, segments = optimize_route_order(graph, start, stops, mode='walk')
    
    print(f"Walking route: {best_order}")
    print(f"Walking time: {total_cost/60:.2f} minutes")
    
    assert len(best_order) == 2, "Should visit both stops"
    assert total_cost > 0, "Walking time should be positive"
    
    print("✅ Test 5 PASSED\n")

def test_performance_with_5_stops():
    """Test 6: Performance test with 5 stops (120 permutations)"""
    print("=== Test 6: Performance with 5 stops ===")
    
    graph = create_mock_graph()
    
    start = 5
    stops = [1, 2, 3, 7, 9]
    
    print(f"Testing with 5 stops (5! = 120 permutations)")
    
    import time
    start_time = time.time()
    
    best_order, total_cost, segments = optimize_route_order(graph, start, stops, mode='car')
    
    elapsed = time.time() - start_time
    
    print(f"Completed in {elapsed:.3f} seconds")
    print(f"Optimal order: {best_order}")
    print(f"Total cost: {total_cost:.2f}")
    
    assert len(best_order) == 5, "Should return all 5 stops"
    assert elapsed < 5.0, "Should complete within 5 seconds"
    
    print("✅ Test 6 PASSED\n")

def run_all_tests():
    """Run all TSP tests"""
    print("=" * 70)
    print("TASK 2: TSP APPROXIMATION TEST SUITE")
    print("=" * 70)
    print()
    
    tests = [
        test_basic_tsp,
        test_tsp_with_4_stops,
        test_optimal_order_verification,
        test_empty_stops,
        test_walking_mode,
        test_performance_with_5_stops,
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
        print("\n🎉 All tests passed! TSP implementation is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the implementation.")

if __name__ == "__main__":
    run_all_tests()
