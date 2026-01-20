"""
Regression tests for the nonogram solver.

These tests compare solver outputs against known-good baseline solutions
generated from the current (correct but slow) solver implementation.

To regenerate baselines, run: python generate_baselines.py
"""

import unittest
import numpy as np
import pickle
import os
import time
from download import get_input
from solution import initialize, solve


class TestSolverRegression(unittest.TestCase):
    """Regression tests comparing solver output to baseline solutions"""
    
    @classmethod
    def setUpClass(cls):
        """Load all baselines once before running tests"""
        cls.baseline_dir = "test_baselines"
        cls.baselines = {}
        
        # Check if baselines exist
        if not os.path.exists(cls.baseline_dir):
            raise FileNotFoundError(
                f"Baseline directory '{cls.baseline_dir}' not found. "
                f"Run 'python generate_baselines.py' first to create baselines."
            )
        
        # Load all baselines
        for example_num in range(1, 8):
            baseline_file = os.path.join(cls.baseline_dir, f"example_{example_num}.pkl")
            if os.path.exists(baseline_file):
                with open(baseline_file, 'rb') as f:
                    cls.baselines[example_num] = pickle.load(f)
            else:
                print(f"Warning: Baseline for example {example_num} not found")
    
    def _test_example(self, example_num):
        """Helper method to test a single example against its baseline"""
        # Check if baseline exists
        if example_num not in self.baselines:
            self.skipTest(f"Baseline for example {example_num} not available")
        
        baseline = self.baselines[example_num]
        
        # Run solver
        inp = {
            "limit_generate": 5_000_000,
            "plot": False,
            "example": example_num
        }
        
        get_input(inp)
        initialize(inp, verbose=False)
        result = solve(inp, verbose=False)
        
        # Compare with baseline
        baseline_result = baseline["result"]
        
        # Check shape
        self.assertEqual(result.shape, baseline_result.shape,
                        f"Result shape {result.shape} != baseline shape {baseline_result.shape}")
        
        # Check dimensions match metadata
        self.assertEqual(result.shape[0], baseline["y"],
                        f"Result height {result.shape[0]} != expected {baseline['y']}")
        self.assertEqual(result.shape[1], baseline["x"],
                        f"Result width {result.shape[1]} != expected {baseline['x']}")
        
        # Compare arrays
        if not np.array_equal(result, baseline_result):
            # Find differences
            diff_mask = (result != baseline_result)
            num_diffs = np.sum(diff_mask)
            total_cells = result.size
            
            # Show some differences for debugging
            diff_positions = np.argwhere(diff_mask)[:10]  # First 10 differences
            diff_details = []
            for pos in diff_positions:
                i, j = pos
                diff_details.append(
                    f"  Position ({i},{j}): got {result[i,j]}, expected {baseline_result[i,j]}"
                )
            
            self.fail(
                f"Result differs from baseline in {num_diffs}/{total_cells} cells:\n" +
                "\n".join(diff_details)
            )
    
    def test_example_1_owl(self):
        """Test Example 1: Owl (30x35x2)"""
        self._test_example(1)
    
    def test_example_2_dog(self):
        """Test Example 2: Dog (40x45x2)"""
        self._test_example(2)
    
    def test_example_3_maple_leaf(self):
        """Test Example 3: Maple Leaf (30x30x2)"""
        self._test_example(3)
    
    def test_example_4_beautiful_eye(self):
        """Test Example 4: Beautiful Eye (35x25x7)"""
        self._test_example(4)
    
    def test_example_5_flamingo(self):
        """Test Example 5: Flamingo (13x20x4)"""
        self._test_example(5)
    
    def test_example_6_rosebud(self):
        """Test Example 6: Rosebud (27x45x8)"""
        self._test_example(6)
    
    def test_example_7_santorini(self):
        """Test Example 7: Santorini (40x50x8)"""
        self._test_example(7)


class TestSolverProperties(unittest.TestCase):
    """Tests for solver properties and invariants"""
    
    def test_solve_returns_numpy_array(self):
        """Test that solve returns a numpy array"""
        inp = {
            "limit_generate": 5_000_000,
            "plot": False,
            "example": 5  # Small fast example
        }
        
        get_input(inp)
        initialize(inp, verbose=False)
        result = solve(inp, verbose=False)
        
        self.assertIsInstance(result, np.ndarray)
    
    def test_solve_output_shape_matches_input(self):
        """Test that output dimensions match puzzle dimensions"""
        inp = {
            "limit_generate": 5_000_000,
            "plot": False,
            "example": 5
        }
        
        get_input(inp)
        x, y = inp["x"], inp["y"]
        
        initialize(inp, verbose=False)
        result = solve(inp, verbose=False)
        
        self.assertEqual(result.shape, (y, x),
                        f"Result shape {result.shape} should be ({y}, {x})")
    
    def test_solve_output_values_in_valid_range(self):
        """Test that all output values are valid color indices or -1 (unsolved)"""
        inp = {
            "limit_generate": 5_000_000,
            "plot": False,
            "example": 5
        }
        
        get_input(inp)
        n_colors = inp["n_colors"]
        
        initialize(inp, verbose=False)
        result = solve(inp, verbose=False)
        
        # All values should be -1 (unsolved) or 0 to n_colors-1
        self.assertTrue(np.all((result >= -1) & (result < n_colors)),
                       f"All values should be in range [-1, {n_colors-1}]")
    
    def test_solve_deterministic(self):
        """Test that solver produces same result on multiple runs"""
        inp1 = {
            "limit_generate": 5_000_000,
            "plot": False,
            "example": 5
        }
        
        get_input(inp1)
        initialize(inp1, verbose=False)
        result1 = solve(inp1, verbose=False)
        
        # Run again
        inp2 = {
            "limit_generate": 5_000_000,
            "plot": False,
            "example": 5
        }
        
        get_input(inp2)
        initialize(inp2, verbose=False)
        result2 = solve(inp2, verbose=False)
        
        np.testing.assert_array_equal(result1, result2,
                                     "Solver should be deterministic")


class TestSolverBenchmark(unittest.TestCase):
    """Benchmark tests for solver performance"""
    
    def test_benchmark_example_7_santorini(self):
        """Benchmark Example 7: Santorini (40x50x8) - run 3 times, report median"""
        times = []
        
        for run in range(3):
            inp = {
                "limit_generate": 5_000_000,
                "plot": False,
                "example": 7
            }
            
            get_input(inp)
            initialize(inp, verbose=False)
            
            start_time = time.perf_counter()
            result = solve(inp, verbose=False)
            end_time = time.perf_counter()
            
            elapsed = end_time - start_time
            times.append(elapsed)
            print(f"  Run {run + 1}: {elapsed:.3f}s")
        
        median_time = sorted(times)[1]  # Median of 3 values
        print(f"\n  Median time: {median_time:.3f}s")
        print(f"  All times: {[f'{t:.3f}s' for t in times]}")
        
        # Verify the result is correct
        self.assertEqual(result.shape, (50, 40))
        self.assertTrue(np.all(result >= -1))


if __name__ == '__main__':
    unittest.main(verbosity=2)

