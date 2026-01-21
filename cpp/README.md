# C++ Accelerated Nonogram Solver

## Architecture

The solver is split into two parts:

### Python Layer (High-level)
- `download.py` - Downloads puzzles from web
- `utils.py` - Visualization and utility functions
- `test.py` - Test framework
- `cpp_wrapper.py` - Python interface to C++ solver

### C++ Layer (Performance-critical)
- `cpp/nonogram_solver.h` - Core solver class definition
- `cpp/nonogram_solver.cpp` - Implementation (to be created)
- `cpp/python_bindings.cpp` - pybind11 interface

## Building the C++ Extension

### Prerequisites
```bash
# Install pybind11
pip install pybind11

# Clone pybind11 into cpp directory (or install via package manager)
cd cpp
git clone https://github.com/pybind/pybind11.git
cd ..
```

### Build on Windows
```bash
# Create build directory
mkdir cpp/build
cd cpp/build

# Configure with CMake
cmake .. -DCMAKE_BUILD_TYPE=Release

# Build
cmake --build . --config Release

# Copy the .pyd file to project root
copy Release/nonogram_cpp*.pyd ../..
```

### Build on Linux/Mac
```bash
mkdir cpp/build
cd cpp/build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j4
cp nonogram_cpp*.so ../..
```

### Alternative: Use setup.py
```bash
pip install -e .
```

## Usage

### Direct C++ Interface
```python
from cpp_wrapper import solve_nonogram

# Your existing code remains the same
inp = get_input('233499')
result = solve_nonogram(inp, verbose=True)
```

### Fallback to Python
If C++ module is not built, automatically falls back to Python implementation.

## Implementation Steps

1. ✅ Design interface (NonogramSolver class)
2. ✅ Create Python bindings structure
3. ✅ Setup build system (CMake + setup.py)
4. ⏳ Implement nonogram_solver.cpp
5. ⏳ Build and test
6. ⏳ Benchmark and optimize

## Expected Performance

Target: 5-10x speedup over Python
- Python: ~9 seconds for Example 7
- C++: ~1-2 seconds (estimated)

## Data Flow

```
Python (download.py)
    ↓ (puzzle definition)
Python (cpp_wrapper.py)
    ↓ (constraints)
C++ (NonogramSolver)
    ↓ (solve)
Python (numpy array result)
    ↓
Python (visualization)
```

## Benefits

1. **Performance**: C++ is 5-10x faster for intensive loops
2. **Memory**: Better control over memory allocation
3. **Compatibility**: Python code for I/O and viz remains unchanged
4. **Debugging**: Can develop/test in Python, then switch to C++
5. **Portability**: Falls back to Python if C++ not available
