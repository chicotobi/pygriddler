# Call Logic Documentation

## Overview
The puzzle loading system uses a three-tier caching strategy to optimize performance:
1. JSON cache (fastest)
2. Raw file cache (medium)
3. Network download (slowest)

## File Structure
```
pygriddler/
├── raw/          # Raw puzzle files downloaded from griddlers.net
├── json/         # Parsed puzzle data in JSON format
└── download.py   # Main logic for fetching and parsing puzzles
```

## Function Call Flow

### Main Entry Point: `get_input(inp)`
```
get_input(inp)
    ↓
    get_id(inp) → Returns puzzle ID based on example number
    ↓
    Check if json/{id}.json exists?
    ├─ YES → Load from JSON file (fastest path)
    └─ NO  → Continue to raw file check
             ↓
             Check if raw/{id} exists?
             ├─ YES → Skip download
             └─ NO  → download_and_write_file(id)
                      ↓
                      Download from griddlers.net
                      Save to raw/{id}
             ↓
             translate_raw_to_json(id)
             ↓
             Parse raw file
             Save to json/{id}.json
             Return puzzle data
    ↓
    Populate inp dictionary with puzzle data
    Return inp
```

## Functions

### `get_id(inp)`
- **Input**: Dictionary with `example` key (1-9)
- **Output**: Puzzle ID number
- **Purpose**: Maps example numbers to specific puzzle IDs from griddlers.net

### `get_title(id0)`
- **Input**: Puzzle ID
- **Output**: Puzzle title string
- **Purpose**: Scrapes the puzzle title from the griddlers.net webpage

### `get_desc(id0, x, y, n_colors)`
- **Input**: Puzzle ID, dimensions, and color count
- **Output**: Formatted description string
- **Purpose**: Creates a human-readable puzzle description

### `download_and_write_file(id0)`
- **Input**: Puzzle ID
- **Output**: None (writes to file)
- **Purpose**: Downloads raw puzzle data and saves to `raw/{id}`
- **Network**: Makes HTTP request to griddlers.net API

### `translate_raw_to_json(id0)`
- **Input**: Puzzle ID
- **Output**: Dictionary with parsed puzzle data
- **Purpose**: Parses raw file and converts to structured JSON format
- **File Operations**:
  - Reads from `raw/{id}`
  - Writes to `json/{id}.json`
- **Data Extracted**:
  - Vertical constraints (inp_v)
  - Horizontal constraints (inp_h)
  - Color palette
  - Puzzle dimensions

### `get_input(inp)`
- **Input**: Dictionary with `example` key
- **Output**: Enhanced dictionary with full puzzle data
- **Purpose**: Main orchestrator that implements the three-tier caching strategy
- **Flow**:
  1. Check JSON cache → fastest
  2. Check raw cache → medium
  3. Download if needed → slowest
  4. Translate raw to JSON if needed
  5. Return puzzle data

## Data Structure

### Input Dictionary (`inp`)
```python
inp = {
    "example": int,           # Example number (1-9)
    "limit_generate": int,    # Generation limit for solver
    "plot": bool,             # Whether to plot results
    # ... other solver parameters
}
```

### Output Dictionary (after `get_input`)
```python
inp = {
    # Original fields preserved
    "example": int,
    "limit_generate": int,
    "plot": bool,
    
    # Added fields
    "id0": int,                           # Puzzle ID
    "desc": str,                          # Puzzle description
    "x": int,                             # Width
    "y": int,                             # Height
    "n_colors": int,                      # Number of colors
    "colors": list,                       # Color palette
    "status": {
        0: {col_idx: {                    # Vertical constraints
            "block_colors": [int],
            "block_lengths": [int]
        }},
        1: {row_idx: {                    # Horizontal constraints
            "block_colors": [int],
            "block_lengths": [int]
        }}
    }
}
```

## Performance Optimization

| Load Method | Speed | When Used |
|-------------|-------|-----------|
| JSON cache  | ~1ms  | Puzzle previously solved |
| Raw cache   | ~50ms | Puzzle downloaded but not parsed |
| Download    | ~500ms+ | First time accessing puzzle |

## Error Handling

- Missing raw file → Triggers download
- Missing JSON file → Triggers translation
- JSON integer key conversion → Handles JSON's string key limitation
- Network errors → Caught in `get_title()` with empty string fallback
