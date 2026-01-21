"""
Python wrapper for C++ nonogram solver.
Provides compatibility with existing Python code.
"""
import numpy as np

# Try to import C++ module, fall back to Python if not available
try:
    from nonogram_cpp import NonogramSolver as CppSolver
    HAS_CPP = True
except ImportError:
    HAS_CPP = False
    print("Warning: C++ module not available, using Python implementation")

def create_cpp_solver(inp):
    """
    Create C++ solver from Python input dictionary.
    
    Args:
        inp: Dictionary with keys:
            - x, y: dimensions
            - n_colors: number of colors
            - status: dict with orientation -> line -> constraints
    
    Returns:
        NonogramSolver instance (C++ or Python fallback)
    """
    if not HAS_CPP:
        return None
    
    x = inp["x"]
    y = inp["y"]
    n_colors = inp["n_colors"]
    
    # Extract constraints for horizontal (orientation 0) and vertical (orientation 1)
    h_constraints = []
    v_constraints = []
    
    # Horizontal lines (rows)
    for idx in range(y):
        if idx in inp["status"][0]:
            h_constraints.append({
                "block_lengths": inp["status"][0][idx]["block_lengths"],
                "block_colors": inp["status"][0][idx]["block_colors"]
            })
        else:
            h_constraints.append({"block_lengths": [], "block_colors": []})
    
    # Vertical lines (columns)  
    for idx in range(x):
        if idx in inp["status"][1]:
            v_constraints.append({
                "block_lengths": inp["status"][1][idx]["block_lengths"],
                "block_colors": inp["status"][1][idx]["block_colors"]
            })
        else:
            v_constraints.append({"block_lengths": [], "block_colors": []})
    
    return CppSolver(x, y, n_colors, h_constraints, v_constraints)


def initialize_cpp(inp, verbose=True):
    """
    Initialize C++ solver (equivalent to Python initialize function).
    """
    if not HAS_CPP:
        from solution import initialize as py_initialize
        return py_initialize(inp, verbose)
    
    solver = create_cpp_solver(inp)
    solver.initialize(inp.get("limit_generate", 5_000_000))
    
    # Store solver in inp for later use
    inp["_cpp_solver"] = solver
    
    return solver


def solve_cpp(inp, verbose=True):
    """
    Solve using C++ solver (equivalent to Python solve function).
    
    Returns:
        numpy array of shape (y, x) with color indices
    """
    if not HAS_CPP:
        from solution import solve as py_solve
        return py_solve(inp, verbose)
    
    # Get or create solver
    if "_cpp_solver" not in inp:
        solver = create_cpp_solver(inp)
        solver.initialize(inp.get("limit_generate", 5_000_000))
    else:
        solver = inp["_cpp_solver"]
    
    result = solver.solve(verbose)
    return result


# Convenience function for one-shot solving
def solve_nonogram(inp, verbose=True):
    """
    Complete solve function: initialize + solve.
    """
    initialize_cpp(inp, verbose)
    return solve_cpp(inp, verbose)
