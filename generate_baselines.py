"""
Generate baseline outputs for regression testing.
Run this script to create reference solutions for examples 1-7.
"""

import numpy as np
import pickle
import os
from download import get_input
from solution import initialize, solve

def generate_baseline(example_num):
    """Generate and save baseline for a single example"""
    print(f"\n{'='*60}")
    print(f"Generating baseline for Example {example_num}")
    print(f"{'='*60}")
    
    inp = {
        "limit_generate": 5_000_000,
        "plot": False,
        "example": example_num
    }
    
    get_input(inp)
    print(f"Puzzle: {inp['desc']}")
    
    initialize(inp)
    result = solve(inp)
    
    # Save the result
    baseline_dir = "test_baselines"
    os.makedirs(baseline_dir, exist_ok=True)
    
    baseline_file = os.path.join(baseline_dir, f"example_{example_num}.pkl")
    
    baseline_data = {
        "example": example_num,
        "result": result,
        "x": inp["x"],
        "y": inp["y"],
        "n_colors": inp["n_colors"],
        "desc": inp["desc"]
    }
    
    with open(baseline_file, 'wb') as f:
        pickle.dump(baseline_data, f)
    
    # Also save as text for inspection
    text_file = os.path.join(baseline_dir, f"example_{example_num}.txt")
    with open(text_file, 'w') as f:
        f.write(f"Example {example_num}: {inp['desc']}\n")
        f.write(f"Size: {inp['x']} x {inp['y']}, Colors: {inp['n_colors']}\n\n")
        f.write("Solution:\n")
        for row in result:
            f.write(' '.join(f'{val:2d}' for val in row) + '\n')
    
    print(f"✓ Baseline saved to {baseline_file}")
    print(f"✓ Text output saved to {text_file}")
    
    # Check if fully solved
    unsolved = np.sum(result == -1)
    if unsolved == 0:
        print(f"✓ Puzzle FULLY SOLVED!")
    else:
        total_cells = result.shape[0] * result.shape[1]
        solved_pct = 100 * (total_cells - unsolved) / total_cells
        print(f"⚠ Partially solved: {solved_pct:.1f}% ({total_cells - unsolved}/{total_cells} cells)")
    
    return result, unsolved == 0

if __name__ == "__main__":
    print("Generating baseline solutions for examples 1-7")
    print("This will take some time for larger puzzles...")
    
    results = {}
    
    for example in range(1, 8):
        try:
            result, fully_solved = generate_baseline(example)
            results[example] = {
                "success": True,
                "fully_solved": fully_solved,
                "shape": result.shape
            }
        except Exception as e:
            print(f"✗ Error generating baseline for example {example}: {e}")
            results[example] = {
                "success": False,
                "error": str(e)
            }
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for example, info in results.items():
        if info["success"]:
            status = "FULLY SOLVED" if info["fully_solved"] else "PARTIAL"
            print(f"Example {example}: ✓ {status} - Shape: {info['shape']}")
        else:
            print(f"Example {example}: ✗ FAILED - {info['error']}")
    
    print("\nBaselines ready for testing!")
