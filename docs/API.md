# API Reference

Complete API documentation for PyGriddler classes, methods, and functions.

---

## Table of Contents

1. [puzzle.py - Puzzle Class](#puzzlepy---puzzle-class)
2. [puzzle_line.py - PuzzleLine Class](#puzzle_linepy---puzzleline-class)
3. [griddler_parser.py - Puzzle Loading](#griddler_parserpy---puzzle-loading)
4. [generators.py - Solution Generation](#generatorspy---solution-generation)
5. [utils.py - Utilities](#utilspy---utilities)

---

## puzzle.py - Puzzle Class

### Class: `Puzzle`

Main class for representing and solving nonogram puzzles.

#### Constructor

```python
Puzzle(puzzle_id: int, limit_generate: int = 5_000_000, strategy: str = "generate")
```

**Parameters:**
- `puzzle_id` (int): Puzzle ID from griddlers.net or example number (1-9)
  - Automatically downloads and parses puzzle using GriddlerParser
  - Example: `4` loads "Beautiful eye" (35x25x7)
  - Example: `39756` loads puzzle directly by ID
- `limit_generate` (int): Max solutions to generate eagerly (default: 5,000,000)
- `strategy` (str): Solving strategy when stuck (default: "generate")
  - `"generate"`: Force-generate solutions for complex lines
  - `"assumption"`: Try pixel assumptions to find contradictions

**Example:**
```python
puzzle = Puzzle(puzzle_id=4, limit_generate=5_000_000, strategy="generate")
```

---

#### Class Method: `from_dict(puzzle_dict: dict, limit_generate: int = 5_000_000, strategy: str = "generate") -> Puzzle`

Create a puzzle from a dictionary (custom puzzles or loaded JSON).

**Parameters:**
- `puzzle_dict` (dict): Puzzle data in GriddlerParser JSON format:
  ```python
  {
      "id0": "custom_001",
      "desc": "My puzzle - 5 x 5 x 2",
      "x": 5,  # width
      "y": 5,  # height
      "n_colors": 2,
      "colors": ["ffffff", "000000"],
      "lines": {
          "horizontal": {
              0: {"block_colors": [1], "block_lengths": [3]},
              ...
          },
          "vertical": {
              0: {"block_colors": [1, 1], "block_lengths": [1, 2]},
              ...
          }
      }
  }
  ```
- `limit_generate` (int): Max solutions to generate (default: 5,000,000)
- `strategy` (str): Solving strategy (default: "generate")

**Returns:**
- Puzzle instance

**Example:**
```python
import json
with open('json/39756.json') as f:
    data = json.load(f)
puzzle = Puzzle.from_dict(data)
```

#### Attributes

- `id0` (int): Puzzle ID from griddlers.net
- `desc` (str): Puzzle description
- `x` (int): Width (columns)
- `y` (int): Height (rows)
- `n_colors` (int): Number of colors (including white)
- `colors` (list): Color values
- `limit_generate` (int): Generation limit
- `color_possible` (np.ndarray): Shape `(y, x, n_colors)`, tracks color possibilities
- `lines` (dict): `{"vertical": {idx: PuzzleLine}, "horizontal": {idx: PuzzleLine}}`

#### Methods

##### `initialize() -> None`

Initialize puzzle lines and generate initial solutions.

**Algorithm:**
1. Count possible solutions for each line
2. Generate solutions if count < `limit_generate`
3. Initialize `color_possible` from constraints

**Side Effects:**
- Populates PuzzleLine objects with counts and solutions
- Updates `color_possible` array

**Example:**
```python
puzzle.initialize()
```

---

##### `solve(do_plot: bool = False) -> None`

Main solving loop.

**Parameters:**
- `do_plot` (bool): Enable real-time visualization (default: False)

**Algorithm:**
```
while not solved:
    refine_solutions()
    if do_plot: plot()
    if no progress: generate_new_solutions()
```

**Example:**
```python
puzzle.solve(do_plot=True)
```

---

##### `solve_iteration(it: int, do_plot: bool) -> None`

Perform one iteration of solving.

**Parameters:**
- `it` (int): Iteration number
- `do_plot` (bool): Whether to plot

**Side Effects:**
- Modifies `color_possible`
- Updates `possible_lines` in PuzzleLine objects

---

##### `refine_solutions() -> bool`

Refine existing solutions using color constraints.

**Returns:**
- `True` if `color_possible` was updated, `False` otherwise

**Algorithm:**
1. For each generated line:
   - Extract color possibilities
   - Filter invalid candidates
   - Update color constraints

**Performance:** Core constraint propagation step.

---

##### `generate_new_solutions() -> bool`

Generate solutions for ungerated lines.

**Returns:**
- `True` if any line was generated, `False` if stuck

**Algorithm:**
1. Try generating with constraints
2. If none succeed, force smallest line

---

##### `is_solved() -> bool`

Check if puzzle is completely solved.

**Returns:**
- `True` if all cells have exactly one possible color

**Example:**
```python
if puzzle.is_solved():
    print("Puzzle solved!")
```

---

##### `extract_row(ori: str, idx: int, color: int) -> np.ndarray`

Extract 1D slice of `color_possible` for specific line and color.

**Parameters:**
- `ori` (str): `"vertical"` (column) or `"horizontal"` (row)
- `idx` (int): Line index
- `color` (int): Color index

**Returns:**
- 1D array of possibilities

**Example:**
```python
col_slice = puzzle.extract_row("vertical", 5, 2)
```

---

##### `extract_row_2(ori: str, idx: int) -> np.ndarray`

Extract 2D slice of `color_possible` for all colors in a line.

**Parameters:**
- `ori` (str): Orientation
- `idx` (int): Line index

**Returns:**
- 2D array of shape `(line_length, n_colors)`

---

##### `apply_line_constraints(ori: str, line: int, line_status: PuzzleLine) -> None`

Apply line constraints to `color_possible`.

**Parameters:**
- `ori` (str): Orientation
- `line` (int): Line index
- `line_status` (PuzzleLine): PuzzleLine with constraints

**Side Effects:**
- Modifies `color_possible` array

---

##### `save_solution() -> None`

Save solved puzzle to disk.

**Output Files:**
- `solutions/python/{id}.npy`: NumPy array
- `solutions/python/{id}.json`: JSON representation

**Example:**
```python
puzzle.save_solution()
```

---

##### `save_plot() -> None`

Save visualization to PNG.

**Output File:**
- `solutions/python/png/{id}.png`

**Example:**
```python
puzzle.save_plot()
```

---

## puzzle_line.py - PuzzleLine Class

### Class: `PuzzleLine`

Represents a single row or column constraint.

#### Constructor

```python
PuzzleLine(block_colors: tuple, 
           block_lengths: tuple,
           n_colors: int,
           possible_lines: Optional[np.ndarray] = None,
           generated: bool = False,
           count: int = 0)
```

**Parameters:**
- `block_colors` (tuple): Color of each block, e.g., `(1, 2, 1)`
- `block_lengths` (tuple): Length of each block, e.g., `(3, 5, 2)`
- `n_colors` (int): Total colors in puzzle
- `possible_lines` (np.ndarray, optional): Valid line configurations
- `generated` (bool): Whether solutions have been generated
- `count` (int): Number of possible solutions

**Example:**
```python
line = PuzzleLine(
    block_colors=(1, 2),
    block_lengths=(3, 5),
    n_colors=3
)
```

#### Properties

- `block_colors` (tuple): Read-only block colors
- `block_lengths` (tuple): Read-only block lengths
- `possible_lines` (np.ndarray): Get/set valid configurations
- `generated` (bool): Get/set generation status
- `count` (int): Get/set solution count
- `slice_of_color_possible` (np.ndarray): Cached color possibilities

#### Methods

##### `get_allowed_colors() -> list`

Compute allowed colors at each position.

**Returns:**
- List of sets, where each set contains allowed color indices

**Performance:** Bottleneck operation using pandas for unique values.

**Example:**
```python
allowed = line.get_allowed_colors()
# allowed[0] might be {0, 1} meaning colors 0 and 1 are possible at position 0
```

---

##### `update_from_color_possible(ori: str, line: int, row_data: np.ndarray, msg_func) -> None`

Filter `possible_lines` based on color constraints.

**Parameters:**
- `ori` (str): Orientation (`"horizontal"` or `"vertical"`)
- `line` (int): Line index
- `row_data` (np.ndarray): Color possibilities `(line_length, n_colors)`
- `msg_func`: Logging function

**Side Effects:**
- Updates `possible_lines` and `count`
- Tracks timing in global `_time_keep`

---

### Global Variables

- `_time_unique` (float): Time spent in unique calculations
- `_time_keep` (float): Time spent filtering candidates

---

## griddler_parser.py - Puzzle Loading

### Class: `GriddlerParser`

Handles downloading and parsing puzzles from griddlers.net with three-tier caching.

#### Class Attribute

```python
EXAMPLES = {
    1: 241934,   # Owl - 30 x 35 x 2
    2: 252952,   # Dog - 40 x 45 x 2
    3: 202358,   # Maple leaf - 30 x 30 x 2
    4: 39756,    # Beautiful eye - 35 x 25 x 7
    5: 275510,   # Flamingo - 13 x 20 x 4
    6: 236744,   # Rosebud - 27 x 45 x 8
    7: 233499,   # Santorini - 40 x 50 x 8
    8: 88712,    # Lion - 45 x 45 x 2
    9: 118315,   # Family in the Summer Heat - 50 x 50 x 6
}
```

Maps example numbers (1-9) to puzzle IDs.

---

#### Constructor

```python
GriddlerParser(puzzle_id: int)
```

**Parameters:**
- `puzzle_id` (int): Puzzle ID from griddlers.net or example number (1-9)

**Example:**
```python
parser = GriddlerParser(4)  # Loads "Beautiful eye"
parser = GriddlerParser(39756)  # Direct ID
```

---

#### Method: `ensure_json_exists() -> str`

Ensures JSON file exists for the puzzle using three-tier caching.

**Returns:**
- Path to JSON file (str): `json/{id}.json`

**Cache Levels:**
1. **JSON** (~1ms): Direct load from `json/{id}.json`
2. **Raw** (~50ms): Parse from `raw/{id}`
3. **Download** (~500ms+): Download from griddlers.net, save to raw, parse to JSON

**Side Effects:**
- May download puzzle to `raw/{id}`
- May create `json/{id}.json`

**Example:**
```python
parser = GriddlerParser(4)
json_path = parser.ensure_json_exists()
# Returns: "json/39756.json"
```

---

#### Static Method: `load_puzzle_data(json_path: str) -> dict`

Load and convert JSON file to puzzle_data dictionary.

**Parameters:**
- `json_path` (str): Path to JSON file

**Returns:**
- Dictionary containing:
  - `id0` (int): Puzzle ID
  - `desc` (str): Description (title, dimensions, colors)
  - `x` (int): Width
  - `y` (int): Height
  - `n_colors` (int): Number of colors
  - `colors` (list): Color values
  - `lines` (dict): `{"vertical": {idx: PuzzleLine}, "horizontal": {idx: PuzzleLine}}`

**Example:**
```python
data = GriddlerParser.load_puzzle_data("json/39756.json")
```

---

#### Private Methods

These methods are used internally by the class:

##### `_resolve_id(puzzle_id: int) -> int`

Convert example number to puzzle ID if needed.

**Parameters:**
- `puzzle_id` (int): Puzzle ID or example number (1-9)

**Returns:**
- Actual puzzle ID from griddlers.net (int)

---

##### `_get_title() -> str`

Fetch puzzle title from griddlers.net.

**Returns:**
- Puzzle title (str), or empty string if fetch fails

---

##### `_get_desc() -> str`

Create puzzle description string.

**Returns:**
- Description (e.g., "Beautiful eye 35 x 25 x 7\n39756")

---

##### `_download_and_write_file() -> None`

Download puzzle from griddlers.net and save to `raw/{id}`.

**Side Effects:**
- Creates file `raw/{id}`

---

##### `_translate_raw_to_json() -> dict`

Parse raw puzzle file and save to JSON.

**Returns:**
- Parsed puzzle data (dict)

**Side Effects:**
- Creates file `json/{id}.json`

**Parsing:**
- Extracts dimensions, colors, block constraints
- Adjusts color indices (griddlers.net uses 1-based)
- Creates PuzzleLine objects for rows and columns

---

## generators.py - Solution Generation

All generator functions use `@cache` decorator for memoization.

### Function: `generate(n, block_lengths, block_colors, previous_color) -> np.ndarray`

Generate all valid line configurations.

**Parameters:**
- `n` (int): Line length
- `block_lengths` (tuple): Block sizes
- `block_colors` (tuple): Block colors
- `previous_color` (int): Previous block color (-1 for first)

**Returns:**
- 2D array where each row is a valid configuration

**Example:**
```python
lines = generate(10, (3, 2), (1, 2), -1)
# Returns array like:
# [[0, 0, 1, 1, 1, 0, 2, 2, 0, 0],
#  [0, 1, 1, 1, 0, 0, 2, 2, 0, 0],
#  ...]
```

---

### Function: `generate_count(n, block_lengths, block_colors, previous_color) -> int`

Count valid configurations without generating them.

**Parameters:** Same as `generate()`

**Returns:**
- Number of valid configurations (int)

**Performance:** Faster than `generate()` since no arrays created.

---

### Function: `generate_with_info(n, block_lengths, block_colors, previous_color, info) -> np.ndarray`

Generate with additional color constraints.

**Parameters:**
- First 4 same as `generate()`
- `info` (tuple): Tuple of allowed colors at each position (from `color_possible`)

**Returns:**
- 2D array of valid configurations satisfying constraints

**Use Case:** Lazy generation with current puzzle state.

---

### Function: `generate_count_with_info(n, block_lengths, block_colors, previous_color, info) -> int`

Count valid configurations with constraints.

**Parameters:** Same as `generate_with_info()`

**Returns:**
- Count of valid configurations (int)

---

### Function: `generate_color_possible(n, block_lengths, block_colors, n_colors) -> np.ndarray`

Generate color possibility matrix for a line.

**Parameters:**
- `n` (int): Line length
- `block_lengths` (tuple): Block sizes
- `block_colors` (tuple): Block colors
- `n_colors` (int): Total colors in puzzle

**Returns:**
- 2D array `(n, n_colors)` indicating possible colors at each position

**Use Case:** Initialize `color_possible` during `Puzzle.initialize()`.

---

## utils.py - Utilities

### Function: `totuple(x) -> tuple`

Convert nested lists/arrays to nested tuples (for caching).

**Parameters:**
- `x`: Nested list or array

**Returns:**
- Nested tuple

**Example:**
```python
t = totuple([[1, 2], [3, 4]])
# Returns: ((1, 2), (3, 4))
```

---

### Function: `hex2rgb(hx: str) -> tuple`

Convert hex color to RGB tuple.

**Parameters:**
- `hx` (str): Hex color (e.g., "FF0000")

**Returns:**
- RGB tuple (float values 0-1)

---

### Function: `nice_number(n: int) -> str`

Format large number with separators.

**Parameters:**
- `n` (int): Number to format

**Returns:**
- Formatted string with dots as thousand separators

**Example:**
```python
nice_number(1234567)
# Returns: "  1.234.567"
```

---

### Function: `msg(ori: str, line: int, n: int, status: bool|str, nold: int = None) -> None`

Print status message for line processing.

**Parameters:**
- `ori` (str): Orientation (`"vertical"` or `"horizontal"`)
- `line` (int): Line index
- `n` (int): Solution count
- `status` (bool or str): Status message or bool for generated
- `nold` (int, optional): Previous count for comparison

**Output:**
Prints formatted message like:
```
O0L005 Generated      5.234.567
O1L012 Reduced to     1.234.567 from 5.234.567
```

---

### Function: `plot(title: str, iteration, color_possible: np.ndarray, colors: list, ori: int) -> None`

Display puzzle state using matplotlib.

**Parameters:**
- `title` (str): Puzzle title
- `iteration`: Iteration number or "FINAL"
- `color_possible` (np.ndarray): Color possibility array `(y, x, n_colors)`
- `colors` (list): Color palette (hex values)
- `ori` (int): Orientation (0 or 1)

**Side Effects:**
- Updates matplotlib figure
- Uses `plt.pause()` for animation

**Example:**
```python
plot("Beautiful eye", 5, color_possible, colors, 0)
```

---

### Function: `compare_output_with_blueprint(example_number: int) -> bool`

Compare solver output with reference blueprint.

**Parameters:**
- `example_number` (int): Example ID

**Returns:**
- `True` if output matches blueprint, `False` otherwise

**Side Effects:**
- Prints comparison result
- Shows diff if mismatch

---

## Data Structures

### puzzle_data Dictionary

```python
{
    "id0": int,              # Puzzle ID
    "desc": str,             # Description
    "x": int,                # Width
    "y": int,                # Height
    "n_colors": int,         # Number of colors
    "colors": list,          # Color hex values
    "status": {
        "vertical": {        # Column constraints
            0: PuzzleLine(...),
            1: PuzzleLine(...),
            ...
        },
        "horizontal": {      # Row constraints
            0: PuzzleLine(...),
            ...
        }
    }
}
```

### color_possible Array

```python
np.ndarray  # Shape: (y, x, n_colors)

# Access
color_possible[row, col, color] = 0 or 1

# 1 = color is possible
# 0 = color is impossible
```

### possible_lines Array

```python
np.ndarray  # Shape: (n_candidates, line_length)

# Each row is a valid line configuration
# Values are color indices (0 = white, 1+ = colors)
```

---

## Constants

### generators.py
- `WHITE = 0`: White/background color index
- `ALLOWED = 1`: Color is allowed
- `NOT_ALLOWED = 0`: Color is not allowed

---

## Performance Globals

### puzzle_line.py
- `_time_unique` (float): Cumulative time in unique calculations
- `_time_keep` (float): Cumulative time in filtering operations

These are used by [script.py](../script.py) for performance profiling.

---

## Error Handling

### Common Exceptions

**`Exception("WARNING! No updates possible, but all lines generated - stuck!")`**
- Raised when puzzle cannot be solved further
- Indicates algorithm is stuck (rare)

**`ValueError("Blueprint file for example {example_number} does not exist.")`**
- Raised by `compare_output_with_blueprint()` if blueprint missing

---

## See Also

- [README.md](../README.md): Project overview
- [ARCHITECTURE.md](ARCHITECTURE.md): System architecture
- [PUZZLE_CLASS.md](PUZZLE_CLASS.md): Puzzle class documentation
