"""Parser for downloading and converting Griddler puzzles from griddlers.net."""

import urllib.request
import os.path
import json
from puzzle_line import PuzzleLine


class GriddlerParser:
    """Handles downloading and parsing puzzles from griddlers.net."""
    
    # Predefined example puzzle mappings
    EXAMPLES = {
        1: 241934,   # Owl - 30 x 35 x 2
        2: 252952,   # Dog - 40 x 45 x 2
        3: 202358,   # Maple leaf - 30 x 30 x 2
        4: 39756,    # Beautiful eye - 35 x 25 x 7
        5: 275510,   # Flamingo - 13 x 20 x 4
        6: 236744,   # Rosebud - 27 x 45 x 8
        7: 233499,   # Santorini - 40 x 50 x 8
        8: 88712,    # Lion - 45 x 45 x 2
        9: 118315,   # Family in the Summer Heat - 50 x 50 x 6 (NOT SOLVED)
    }
    
    def __init__(self, puzzle_id: int):
        """Initialize parser for a specific puzzle ID.
        
        Args:
            puzzle_id: Puzzle ID from griddlers.net or example number (1-9)
        """
        self.puzzle_id = self._resolve_id(puzzle_id)
    
    @staticmethod
    def _resolve_id(puzzle_id: int) -> int:
        """Convert example number to puzzle ID if needed.
        
        Args:
            puzzle_id: Puzzle ID or example number (1-9)
            
        Returns:
            Actual puzzle ID from griddlers.net
        """
        return GriddlerParser.EXAMPLES.get(puzzle_id, puzzle_id)
    
    def _get_title(self) -> str:
        """Fetch puzzle title from griddlers.net.
        
        Returns:
            Puzzle title, or empty string if fetch fails
        """
        link = f'https://www.griddlers.net/nonogram/-/g/{self.puzzle_id}'
        try:
            s = str(urllib.request.urlopen(link).read())
            s2 = f"Griddlers puzzle {self.puzzle_id} - "
            idx = s.find(s2)
            idx1 = idx + len(s2)
            idx2 = idx + len(s2) + 50
            s3 = s[idx1:idx2]
            idx3 = s3.find('"')
            title = s3[:idx3]
        except:
            title = ''
        return title
    
    def _get_desc(self, x: int, y: int, n_colors: int) -> str:
        """Create puzzle description string.
        
        Args:
            x: Width
            y: Height
            n_colors: Number of colors
            
        Returns:
            Description string
        """
        title = self._get_title()
        return f"{title} {x} x {y} x {n_colors}\n{self.puzzle_id}"
    
    def _download_and_write_file(self) -> None:
        """Download puzzle from griddlers.net and save to raw/{id}."""
        s1 = 'https://www.griddlers.net/nonogram/-/g/t1709243262226/i01?p_p_lifecycle=2&p_p_resource_id=griddlerPuzzle&p_p_cacheability=cacheLevelPage&_gpuzzles_WAR_puzzles_id='
        s2 = '&_gpuzzles_WAR_puzzles_lite=false&_gpuzzles_WAR_puzzles_name=touchScreen'
        link = s1 + str(self.puzzle_id) + s2
        s = str(urllib.request.urlopen(link).read())
        
        raw_path = os.path.join('raw', str(self.puzzle_id))
        with open(raw_path, 'w') as f:
            f.write(s)
    
    def _translate_raw_to_json(self) -> None:
        """Parse raw puzzle file and save to json/{id}.json."""
        fname_raw = os.path.join('raw', str(self.puzzle_id))
        fname_json = os.path.join('json', str(self.puzzle_id) + '.json')
        
        with open(fname_raw, 'r') as f:
            s = f.read().split('\\n')
        
        inp_v = eval('[' + s[66].strip('\\t') + ']')
        inp_h = eval('[' + s[69].strip('  ').strip('\\t') + ']')
        used_colors = eval('[' + s[63].strip('  ').strip('\\t') + ']')
        colors = eval('[' + s[57].strip('  ').strip('\\t') + ']')
        colors = [colors[i] for i in used_colors]
        
        lines = {}
        lines["vertical"] = {
            idx: {
                "block_colors": [i[0]-1 for i in j],
                "block_lengths": [i[1] for i in j]
            } for idx, j in enumerate(inp_v)
        }
        lines["horizontal"] = {
            idx: {
                "block_colors": [i[0]-1 for i in j],
                "block_lengths": [i[1] for i in j]
            } for idx, j in enumerate(inp_h)
        }
        
        x = len(inp_v)
        y = len(inp_h)
        n_colors = len(colors)
        
        puzzle_data = {
            "id0": self.puzzle_id,
            "desc": self._get_desc(x, y, n_colors),
            "lines": lines,
            "colors": colors,
            "n_colors": n_colors,
            "x": x,
            "y": y
        }
        
        with open(fname_json, 'w') as f:
            json.dump(puzzle_data, f, indent=2)
    
    def ensure_json_exists(self) -> str:
        """Ensure JSON file exists, downloading and parsing if needed.
        
        Returns:
            Path to JSON file
        """
        fname_json = os.path.join('json', str(self.puzzle_id) + '.json')
        
        if not os.path.isfile(fname_json):
            fname_raw = os.path.join('raw', str(self.puzzle_id))
            if not os.path.isfile(fname_raw):
                self._download_and_write_file()
            self._translate_raw_to_json()
        
        return fname_json
    
    @staticmethod
    def load_puzzle_data(json_path: str) -> dict:
        """Load and parse puzzle data from JSON file.
        
        Args:
            json_path: Path to JSON file
            
        Returns:
            Dictionary with puzzle data and PuzzleLine objects
        """
        with open(json_path, 'r') as f:
            puzzle_data = json.load(f)
        
        # Convert lines dicts to PuzzleLine objects (handles string keys from JSON)
        lines = {}
        n_colors = puzzle_data["n_colors"]
        for ori_key in ["vertical", "horizontal"]:
            lines[ori_key] = {
                int(idx): PuzzleLine(
                    block_colors=tuple(data["block_colors"]),
                    block_lengths=tuple(data["block_lengths"]),
                    n_colors=n_colors,
                    possible_lines=None,
                    generated=False,
                    count=0
                ) for idx, data in puzzle_data.get("lines", puzzle_data.get("status", {}))[ori_key].items()
            }
        puzzle_data["lines"] = lines
        
        return puzzle_data
