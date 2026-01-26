# Puzzle Class Documentation

This document provides detailed documentation for the `Puzzle` class and the object-oriented architecture of PyGriddler.

## Overview

The PyGriddler solver has been refactored to use an object-oriented design with a `Puzzle` class that encapsulates all puzzle state and solving logic. This design provides better encapsulation, testability, and maintainability compared to the original procedural approach.

---

## Puzzle Class

**File:** [puzzle.py](../puzzle.py)

The `Puzzle` class is the main entry point for solving nonogram puzzles. It manages:
- Puzzle metadata (dimensions, colors, description)
- Color possibility tracking (`color_possible` 3D array)
- Line constraints (`lines` dictionary of `PuzzleLine` objects)
- Solving algorithm orchestration
- Solution saving and visualization

### Constructor

```python
def __init__(self, puzzle_id: int, limit_generate: int = 5_000_000)
```

**Parameters:**
- `puzzle_id` (int): Puzzle ID from griddlers.net or example number (1-9)
  - Downloads and parses puzzle automatically using `GriddlerParser`
  - Example: `puzzle_id=4` loads "Beautiful eye" (35x25x7)
  - Example: `puzzle_id=39756` loads puzzle directly by ID
- `limit_generate` (int, optional): Maximum number of solutions to generate eagerly during initialization. Default: 5,000,000

**Initializes:**
- Puzzle metadata attributes (id0, desc, x, y, n_colors, colors)
- `lines`: Dictionary with PuzzleLine objects for each row/column
- `color_possible`: 3D NumPy array of shape `(y, x, n_colors)`, initially all 1s

**Example:**
```python
from puzzle import Puzzle

# Using example number
puzzle = Puzzle(puzzle_id=4, limit_generate=5_000_000)

# Using direct puzzle ID
puzzle = Puzzle(puzzle_id=39756)
```

---

## Instance Attributes

### Metadata

- **`id0`** (int): Puzzle ID from griddlers.net
- **`desc`** (str): Puzzle description (e.g., "Beautiful eye 35 x 25 x 7\n39756")
- **`x`** (int): Width (number of columns)
- **`y`** (int): Height (number of rows)
- **`n_colors`** (int): Total number of colors including white (0)
- **`colors`** (list): Color values, e.g., `[0, 1, 2, 3, 4, 5, 6]`
- **`limit_generate`** (int): Maximum solutions to generate eagerly

### State

- **`color_possible`** (np.ndarray): Shape `(y, x, n_colors)`
  - `color_possible[row, col, color] = 1` means color is possible at that position
  - `color_possible[row, col, color] = 0` means color is ruled out
  - Updated during solving as constraints are applied

- **`lines`** (dict): Dictionary with two keys:
  - `"vertical"`: Dict mapping column index → `PuzzleLine` object
  - `"horizontal"`: Dict mapping row index → `PuzzleLine` object

---

## Methods

### Initialization

#### `initialize() -> None`

Initialize puzzle lines by counting possible solutions and generating initial candidates.

**Algorithm:**
1. For each line (row and column):
   - Count possible solutions using `generate_count()`
   - If count < `limit_generate`:
     - Generate all solutions using `generate()`
     - Mark line as `generated = True`
     - Store solutions in `possible_lines`
   - Otherwise:
     - Mark line as `generated = False`
     - Defer generation until needed during solving
2. Initialize `color_possible` by sweeping through all generated lines

**Side Effects:**
- Updates `status` dict with counts and generated solutions
- Prints progress messages via `utils.msg()`

**Example:**
```python
puzzle = Puzzle(puzzle_data, limit_generate=5_000_000)
puzzle.initialize()  # Count and generate initial solutions
```

---

### Solving

#### `solve(do_plot: bool = False) -> None`

Main solving loop - solves the puzzle completely.

**Parameters:**
- `do_plot` (bool): If True, display real-time matplotlib visualization

**Algorithm:**
```
while not is_solved():
    1. Call refine_solutions() to filter candidates
    2. If do_plot: visualize current state
    3. If no progress made:
       - Call generate_new_solutions()
```

**Side Effects:**
- Modifies `color_possible` array
- Updates `possible_lines` in PuzzleLine objects
- Displays plots if `do_plot=True`

**Example:**
```python
puzzle.solve(do_plot=True)  # Solve with visualization
```

#### `solve_iteration(it: int, do_plot: bool) -> tuple`

Perform one iteration of the solving algorithm.

**Parameters:**
- `it` (int): Iteration number (for logging)
- `do_plot` (bool): Whether to plot current state

**Returns:**
- `color_possible` (np.ndarray): Updated color possibilities
- `generated` (bool): Whether any new solutions were generated
- `worth_checking` (dict): Sets of lines that changed

**Called by:** `solve()`

#### `refine_solutions() -> tuple`

Refine existing solutions based on color constraints.

**Algorithm:**
For each generated line:
1. Extract current color possibilities for that line
2. Filter `possible_lines` to remove invalid candidates
3. Update `color_possible` based on remaining candidates
4. Track which perpendicular lines were affected

**Returns:**
- `color_possible` (np.ndarray): Updated color possibilities
- `old` (np.ndarray): Previous color_possible for change detection
- `worth_checking` (dict): Lines that need rechecking

**Performance:** This is the core constraint propagation step. Most time is spent here.

#### `generate_new_solutions() -> tuple`

Generate new line solutions when needed (lazy generation).

**Algorithm:**
1. For each ungerated line:
   - Attempt to generate with current color constraints using `generate_with_info()`
2. If no lines could be generated:
   - Find the smallest ungerated line (by solution count)
   - Force generate it without constraints
   - Mark as generated

**Returns:**
- `color_possible` (np.ndarray): Updated color possibilities
- `any_generated` (bool): Whether any solutions were generated

**When called:** Only when `refine_solutions()` makes no progress

#### `is_solved() -> bool`

Check if puzzle is completely solved.

**Returns:**
- `True` if all cells have exactly one possible color
- `False` otherwise

**Algorithm:**
```python
return np.all(np.sum(color_possible, axis=2) == 1)
```

---

### Helper Methods

#### `extract_row(ori: str, idx: int, color: int) -> np.ndarray`

Extract a 1D slice of `color_possible` for a specific line and color.

**Parameters:**
- `ori` (str): `"vertical"` (column) or `"horizontal"` (row)
- `idx` (int): Column or row index
- `color` (int): Color index

**Returns:**
- 1D array of possibilities for that line and color

**Example:**
```python
# Get color 2 possibilities for column 5
col_slice = puzzle.extract_row("vertical", 5, 2)
```

#### `extract_row_2(ori: str, idx: int) -> np.ndarray`

Extract a 2D slice of `color_possible` for all colors in a line.

**Parameters:**
- `ori` (str): `"vertical"` (column) or `"horizontal"` (row)
- `idx` (int): Column or row index

**Returns:**
- 2D array of shape `(line_length, n_colors)`

**Example:**
```python
# Get all color possibilities for row 3
row_slice = puzzle.extract_row_2("horizontal", 3)
```

#### `apply_line_constraints(ori: str, line: int, line_status: PuzzleLine) -> None`

Apply constraints from a PuzzleLine to update `color_possible`.

**Parameters:**
- `ori` (str): Orientation (`"vertical"` or `"horizontal"`)
- `line` (int): Line index
- `line_status` (PuzzleLine): PuzzleLine object with constraints

**Side Effects:**
- Modifies `color_possible` array based on line's `possible_lines`

---

### Output Methods

#### `save_solution() -> None`

Save solved puzzle as `.npy` and `.json` files.

**Output Files:**
- `solutions/python/{id}.npy`: NumPy array of solution
- `solutions/python/{id}.json`: JSON representation

**Format:**
- Solution is a 2D array where each cell contains its color index
- Derived from `color_possible` by finding the unique color at each position

**Example:**
```python
puzzle.solve()
puzzle.save_solution()  # Saves to solutions/python/39756.npy and .json
```

#### `save_plot() -> None`

Save visualization as PNG file.

**Output File:**
- `solutions/python/png/{id}.png`

**Uses:** `utils.plot()` to generate the visualization

**Example:**
```python
puzzle.save_plot()  # Saves to solutions/python/png/39756.png
```

---

## PuzzleLine Class

**File:** [puzzle_line.py](../puzzle_line.py)

The `PuzzleLine` class represents a single row or column constraint in the puzzle.

### Constructor

```python
def __init__(self, 
             block_colors: tuple, 
             block_lengths: tuple,
             n_colors: int,
             possible_lines: Optional[np.ndarray] = None,
             generated: bool = False,
             count: int = 0)
```

**Parameters:**
- `block_colors` (tuple): Color of each block, e.g., `(1, 2, 1)` for color1, color2, color1
- `block_lengths` (tuple): Length of each block, e.g., `(3, 5, 2)` for 3 cells, 5 cells, 2 cells
- `n_colors` (int): Total number of colors in puzzle
- `possible_lines` (np.ndarray, optional): 2D array of valid line configurations
- `generated` (bool): Whether solutions have been generated
- `count` (int): Number of possible solutions

### Properties

- **`block_colors`** (tuple): Read-only block colors
- **`block_lengths`** (tuple): Read-only block lengths
- **`possible_lines`** (np.ndarray): Get/set valid line configurations
- **`generated`** (bool): Get/set generation status
- **`count`** (int): Get/set solution count

### Methods

#### `get_allowed_colors(color_possible_slice: np.ndarray) -> list`

Compute which colors are still possible at each position based on current constraints.

**Parameters:**
- `color_possible_slice` (np.ndarray): 2D array `(line_length, n_colors)` from `Puzzle.extract_row_2()`

**Returns:**
- List of sets, where each set contains allowed color indices at that position

**Performance:** This is a bottleneck operation. Uses pandas for unique value calculation.

#### `filter_possible_lines(color_possible_slice: np.ndarray) -> int`

Remove invalid candidates from `possible_lines` based on color constraints.

**Parameters:**
- `color_possible_slice` (np.ndarray): Current color possibilities

**Returns:**
- Number of lines removed

**Side Effects:**
- Updates `possible_lines` to only contain valid candidates

#### `update_color_possible(color_possible_slice: np.ndarray) -> int`

Update color possibilities based on remaining valid lines.

**Parameters:**
- `color_possible_slice` (np.ndarray): Current color possibilities (modified in-place)

**Returns:**
- Number of cells that changed

**Side Effects:**
- Modifies `color_possible_slice` to reflect constraints from `possible_lines`

---

## Usage Examples

### Basic Usage

```python
from download import get_input
from puzzle import Puzzle

# Configure and load puzzle
config = {"example": 4, "limit_generate": 5_000_000, "plot": False}
puzzle_data = get_input(config)

# Create puzzle instance
puzzle = Puzzle(puzzle_data, limit_generate=config["limit_generate"])

# Initialize and solve
puzzle.initialize()
puzzle.solve(do_plot=False)

# Save results
puzzle.save_solution()
puzzle.save_plot()
```

### With Visualization

```python
from download import get_input
from puzzle import Puzzle
import matplotlib.pyplot as plt

plt.ion()  # Interactive mode for live updates

config = {"example": 5, "limit_generate": 5_000_000, "plot": True}
puzzle_data = get_input(config)

puzzle = Puzzle(puzzle_data, limit_generate=config["limit_generate"])
puzzle.initialize()
puzzle.solve(do_plot=True)  # Shows live solving progress

puzzle.save_solution()
puzzle.save_plot()

plt.ioff()
plt.show()  # Keep final plot visible
```

### Multiple Puzzles

```python
from download import get_input
from puzzle import Puzzle

# Solve multiple puzzles in sequence
for example_id in [1, 2, 3, 4, 5]:
    config = {"example": example_id, "limit_generate": 5_000_000}
    puzzle_data = get_input(config)
    
    puzzle = Puzzle(puzzle_data, limit_generate=config["limit_generate"])
    puzzle.initialize()
    puzzle.solve(do_plot=False)
    puzzle.save_solution()
    
    print(f"Solved puzzle {puzzle.id0}: {puzzle.desc}")
```

### Custom Puzzle ID

```python
from download import get_input
from puzzle import Puzzle

# Solve any puzzle from griddlers.net by ID
config = {"example": 123456, "limit_generate": 10_000_000}
puzzle_data = get_input(config)

puzzle = Puzzle(puzzle_data, limit_generate=config["limit_generate"])
puzzle.initialize()
puzzle.solve(do_plot=False)
puzzle.save_solution()
```

---

## Design Benefits

### 1. Encapsulation
All puzzle state is contained within the `Puzzle` object:
- No global variables
- No passing large arrays between functions
- Clear ownership of data

### 2. Reusability
Multiple puzzles can be instantiated and solved independently:
```python
puzzle1 = Puzzle(data1, limit_generate=5_000_000)
puzzle2 = Puzzle(data2, limit_generate=10_000_000)

puzzle1.solve()
puzzle2.solve()
```

### 3. Testability
Easier to unit test individual methods:
```python
def test_is_solved():
    puzzle = Puzzle(simple_puzzle_data, limit_generate=1000)
    puzzle.initialize()
    assert not puzzle.is_solved()
    
    puzzle.solve()
    assert puzzle.is_solved()
```

### 4. Maintainability
Clear separation of concerns:
- `Puzzle`: Orchestration and solving
- `PuzzleLine`: Individual constraint tracking
- `generators`: Solution generation algorithms
- `download`: Puzzle loading and caching

### 5. Extensibility
Easy to add new features:
- Custom solving strategies (inherit from `Puzzle`)
- Alternative generation algorithms
- Different saving formats
- Solving statistics and analytics

---

## Migration from Procedural Code

### Old Pattern (Deprecated)
```python
from solution import initialize, solve
from download import get_input

inp = get_input(config)
initialize(inp)
solve(inp)
```

### New Pattern (Recommended)
```python
from puzzle import Puzzle
from download import get_input

puzzle_data = get_input(config)
puzzle = Puzzle(puzzle_data, limit_generate=config["limit_generate"])
puzzle.initialize()
puzzle.solve(do_plot=config.get("plot", False))
puzzle.save_solution()
```

### Backward Compatibility

The old procedural interface is still available via wrapper functions in `solution.py` for compatibility with existing scripts, but the `Puzzle` class is the recommended approach for new code.

---

## Performance Considerations

### Memory Usage

Memory scales with:
- Puzzle dimensions (x × y × n_colors for `color_possible`)
- Number of generated lines and their solution counts
- `limit_generate` setting (higher = more eager generation = more memory)

### Speed Optimization

**limit_generate** tuning:
- **Too low**: Slower solving (more lazy generation)
- **Too high**: Slower initialization and higher memory
- **Sweet spot**: 1M - 10M depending on puzzle size

**Bottlenecks** (from profiling):
1. `PuzzleLine.get_allowed_colors()`: Finding unique values
2. `PuzzleLine.filter_possible_lines()`: Filtering candidates

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed performance analysis.

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md): System architecture and algorithm details
- [API.md](API.md): Complete API reference
- [../README.md](../README.md): Project overview and quick start
