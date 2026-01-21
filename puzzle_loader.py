"""
Puzzle loader - handles JSON format conversion and caching
"""
import os
import json
from download import get_id, download_and_write_file, parse_raw_file

def raw_to_json(id0):
    """Convert raw puzzle file to JSON format"""
    inp_v, inp_h, colors = parse_raw_file(id0)
    
    # Convert to JSON structure
    puzzle = {
        "id": id0,
        "width": len(inp_v),
        "height": len(inp_h),
        "n_colors": len(colors),
        "colors": colors,
        "h_constraints": [],  # Horizontal (rows)
        "v_constraints": []   # Vertical (columns)
    }
    
    # Horizontal constraints (inp_h contains row constraints)
    for row in inp_h:
        puzzle["h_constraints"].append({
            "block_lengths": [block[1] for block in row],
            "block_colors": [block[0] - 1 for block in row]
        })
    
    # Vertical constraints (inp_v contains column constraints)
    for col in inp_v:
        puzzle["v_constraints"].append({
            "block_lengths": [block[1] for block in col],
            "block_colors": [block[0] - 1 for block in col]
        })
    
    return puzzle

def load_puzzle(example):
    """
    Load puzzle from JSON cache, converting from raw format or downloading if needed
    
    Args:
        example: Example number (1-9) or direct puzzle ID
    
    Returns:
        dict: Puzzle data with constraints and metadata
    """
    # Resolve to actual puzzle ID
    id0 = get_id({"example": example})
    json_path = os.path.join('json', f'{id0}.json')
    
    # Check if JSON exists
    if os.path.isfile(json_path):
        with open(json_path, 'r') as f:
            return json.load(f)
    
    # Check if raw format exists
    raw_path = os.path.join('raw_format', str(id0))
    if not os.path.isfile(raw_path):
        print(f"Downloading puzzle {id0}...")
        download_and_write_file(id0)
    
    # Convert to JSON
    print(f"Converting puzzle {id0} to JSON format...")
    puzzle = raw_to_json(id0)
    
    # Save JSON for future use
    with open(json_path, 'w') as f:
        json.dump(puzzle, f, indent=2)
    
    return puzzle
