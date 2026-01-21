# PyGriddler - Nonogram Solver

A high-performance nonogram (griddler) puzzle solver with both Python and C++ implementations.

## Features

- **Dual Solver Support**: Choose between Python or C++ solver
- **Automatic Puzzle Management**: Download, convert, and cache puzzles
- **JSON Format**: Clean, standardized puzzle representation
- **Visualization**: Built-in plotting support
- **Smart Caching**: Puzzles downloaded once, converted to JSON, then loaded instantly

## Quick Start

1. **Configure settings** in `script.py`:
```python
USE_CPP_SOLVER = False  # True for C++, False for Python
EXAMPLE = 5              # Example number (1-9) or direct puzzle ID
PLOT = True              # Show visualization
VERBOSE = True           # Show solving progress
```

2. **Run the solver**:
```bash
python script.py
```

## Puzzle Format

All puzzles use a standardized JSON format:

```json
{
  "id": 275510,
  "width": 13,
  "height": 20,
  "n_colors": 4,
  "colors": ["#ffffff", "#000000", "#ff0000", "#00ff00"],
  "h_constraints": [
    {
      "block_lengths": [2, 3],
      "block_colors": [1, 2]
    }
  ],
  "v_constraints": [
    {
      "block_lengths": [1, 4],
      "block_colors": [0, 1]
    }
  ]
}
```

### Format Details

- **id**: Puzzle ID from griddlers.net
- **width**: Number of columns (vertical constraints)
- **height**: Number of rows (horizontal constraints)
- **n_colors**: Number of colors in the puzzle
- **colors**: Hex color values for each color index
- **h_constraints**: Horizontal (row) constraints - one per row
- **v_constraints**: Vertical (column) constraints - one per column
- Each constraint contains:
  - `block_lengths`: Length of each consecutive block
  - `block_colors`: Color index for each block (0-indexed)

## Architecture

### Directory Structure

```
pygriddler/
├── raw_format/       # Downloaded raw puzzle files
├── json/             # Cached JSON puzzles
├── solutions/        # Saved solutions (future)
├── cpp/              # C++ solver source
│   ├── build/        # CMake build output
│   └── pybind11/     # Python bindings library
└── *.py              # Python solver and utilities
```

### Puzzle Loading Workflow

1. **User requests puzzle** by example number or ID
2. **puzzle_loader.load_puzzle()** checks JSON cache
3. If not cached:
   - Check if raw format exists
   - Download from griddlers.net if needed
   - Parse raw format with `download.parse_raw_file()`
   - Convert to JSON with `puzzle_loader.raw_to_json()`
   - Save JSON for future use
4. **Return puzzle dict** ready for solver

### Key Modules

- **script.py**: Main entry point, supports both solvers
- **puzzle_loader.py**: Puzzle loading and JSON caching
- **download.py**: Download puzzles and parse raw format
- **solution.py**: Python solver implementation
- **generators.py**: Line generation algorithms
- **utils.py**: Plotting and helper functions
- **nonogram_cpp**: C++ solver Python extension (compiled)

## Solver Comparison

| Feature | Python Solver | C++ Solver |
|---------|---------------|------------|
| Speed | Moderate | Fast |
| Verbose Output | Yes | Yes |
| Plotting | Yes | Yes |
| Dependencies | NumPy | pybind11 |
| Build Required | No | Yes (CMake) |

## Example Puzzles

| Example | Name | Size | Colors | ID |
|---------|------|------|--------|-----|
| 1 | Owl | 30×35 | 2 | 241934 |
| 2 | Dog | 40×45 | 2 | 252952 |
| 3 | Maple Leaf | 30×30 | 2 | 202358 |
| 4 | Beautiful Eye | 35×25 | 7 | 39756 |
| 5 | Flamingo | 13×20 | 4 | 275510 |
| 6 | Rosebud | 27×45 | 8 | 236744 |
| 7 | Santorini | 40×50 | 8 | 233499 |
| 8 | Lion | 45×45 | 2 | 88712 |

## Building C++ Solver

```bash
cd cpp
mkdir build
cd build
cmake ..
cmake --build . --config Release
```

The compiled extension (`nonogram_cpp.*.pyd`) will be in `cpp/build/Release/`.

## Migration Notes

### Old Format (Deprecated)
```python
{
  "status": {
    0: {idx: {"block_colors": [...], "block_lengths": [...]}},  # vertical
    1: {idx: {"block_colors": [...], "block_lengths": [...]}}   # horizontal
  },
  "x": width,
  "y": height,
  ...
}
```

### New Format (Current)
- Uses lists (`h_constraints`, `v_constraints`) instead of nested dicts
- Consistent naming: `width`/`height` instead of `x`/`y`
- Removed orientation indexing (`0`/`1`)
- All code now uses the new format
- No backwards compatibility - clean codebase

## Performance

The C++ solver typically runs 10-100x faster than Python for large puzzles due to:
- Compiled native code
- Optimized memory layout
- Efficient constraint propagation

## License

See LICENSE file for details.
