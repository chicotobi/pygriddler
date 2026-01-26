# PyGriddler

A high-performance Python solver for nonogram puzzles (also known as griddlers, hanjie, picross) sourced from [griddlers.net](https://www.griddlers.net). Supports multi-color puzzles with optimized constraint propagation and intelligent solution generation.

## Features

- 🚀 **Fast Solving**: Optimized constraint propagation with caching
- 🎨 **Multi-Color Support**: Handles complex colored nonogram puzzles
- 📦 **Three-Tier Caching**: JSON → Raw → Download for fast puzzle loading
- 🔍 **Smart Generation**: Lazy and eager solution generation based on complexity
- 📊 **Visualization**: Real-time matplotlib visualization of solving progress
- 💾 **Solution Export**: Save solutions as .npy arrays and .json files

## Installation

### Prerequisites

- Python 3.8+
- NumPy
- Matplotlib
- Pandas

### Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd pygriddler

# Install dependencies
pip install numpy matplotlib pandas
```

## Quick Start

```python
from download import get_input
from puzzle import Puzzle

# Configure puzzle (example 4 = "Beautiful eye" 35x25x7)
config = {
    "example": 4,
    "limit_generate": 5_000_000,
    "plot": True
}

# Load puzzle data
puzzle_data = get_input(config)

# Create and solve puzzle
puzzle = Puzzle(puzzle_data, limit_generate=config["limit_generate"])
puzzle.initialize()
puzzle.solve(do_plot=config["plot"])

# Save results
puzzle.save_solution()
puzzle.save_plot()
```

## Example Puzzles

The system includes 9 predefined example puzzles:

| Example | ID | Name | Size | Colors | Difficulty |
|---------|-----|------|------|--------|-----------|
| 1 | 241934 | Owl | 30×35 | 2 | Easy |
| 2 | 252952 | Dog | 40×45 | 2 | Medium |
| 3 | 202358 | Maple Leaf | 30×30 | 2 | Easy |
| 4 | 39756 | Beautiful Eye | 35×25 | 7 | Medium |
| 5 | 275510 | Flamingo | 13×20 | 4 | Easy |
| 6 | 236744 | Rosebud | 27×45 | 8 | Hard |
| 7 | 233499 | Santorini | 40×50 | 8 | Hard |
| 8 | 88712 | Lion | 45×45 | 2 | Medium |
| 9 | 118315 | Family in Summer Heat | 50×50 | 6 | Unsolved |

You can also use any puzzle ID from griddlers.net:

```python
config = {"example": 39756, "limit_generate": 5_000_000, "plot": False}
```

## Project Structure

```
pygriddler/
├── README.md              # This file
├── docs/                  # Documentation
│   ├── ARCHITECTURE.md    # System architecture and call flow
│   ├── PUZZLE_CLASS.md    # Puzzle class documentation
│   └── API.md             # API reference
├── puzzle.py              # Main Puzzle class
├── puzzle_line.py         # PuzzleLine class for individual constraints
├── generators.py          # Solution generation algorithms
├── download.py            # Puzzle loading and caching
├── utils.py               # Utility functions (plotting, logging)
├── script.py              # Main execution script
├── raw/                   # Raw puzzle files from griddlers.net
├── json/                  # Parsed puzzle data
├── blueprint/             # Reference solutions for validation
└── solutions/             # Solver output
    └── python/            # .npy and .json solution files
```

## How It Works

### 1. Puzzle Loading (Three-Tier Cache)

```
get_input() → JSON cache? → Raw cache? → Download from griddlers.net
              ↓ (~1ms)       ↓ (~50ms)    ↓ (~500ms)
              ✓              ✓             Parse & Save
```

### 2. Initialization

- Count possible solutions for each row/column
- Generate solutions eagerly if count < `limit_generate`
- Mark complex lines for lazy generation

### 3. Solving Algorithm

```
Initialize → Refine Solutions → Check Progress
                ↑                    ↓
                └── Generate New ←──┘
                     (if no progress)
```

**Refine Solutions**: Filter candidates based on color constraints
**Generate New**: Create solutions for ungerated lines with current constraints

### 4. Output

- Solutions saved to `solutions/python/{id}.npy` and `.json`
- Plots saved to `solutions/python/png/{id}.png`

## Configuration Options

### `limit_generate`
Maximum number of possible lines to generate eagerly for a single row/column.
- **Default**: 5,000,000
- **Lower values**: Faster initialization, more lazy generation during solving
- **Higher values**: Slower initialization, faster solving

### `plot`
Enable real-time visualization of solving progress.
- **True**: Show matplotlib plot (slower, interactive)
- **False**: No visualization (faster, batch mode)

### `example`
Puzzle selection:
- **1-9**: Predefined examples
- **Any integer**: Direct puzzle ID from griddlers.net

## Performance

Typical solve times on modern hardware:

| Puzzle Size | Colors | Time |
|-------------|--------|------|
| 13×20 | 4 | < 1s |
| 30×35 | 2 | 2-5s |
| 35×25 | 7 | 5-15s |
| 40×50 | 8 | 30-60s |
| 45×45 | 2 | 10-30s |

Performance bottlenecks:
- **Unique calculation**: Finding unique values in possible lines
- **Keep calculation**: Filtering valid candidates

Runtime summary is printed at the end of execution.

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)**: System design and call flow
- **[Puzzle Class](docs/PUZZLE_CLASS.md)**: Object-oriented design details
- **[API Reference](docs/API.md)**: Complete API documentation

## Limitations

- Some very complex puzzles may not solve (e.g., Example 9)
- Memory usage scales with puzzle size and number of colors
- No support for puzzles with special rules or unique constraints

## Contributing

Contributions welcome! Areas for improvement:
- Additional solving heuristics
- Memory optimization for large puzzles
- Parallelization of constraint propagation
- GUI interface

## License

[Specify your license here]

## Acknowledgments

- Puzzles from [griddlers.net](https://www.griddlers.net)
- Inspired by nonogram solving algorithms and constraint satisfaction techniques
