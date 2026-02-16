"""Multi-part puzzle solver for consecutive griddler puzzles that form a larger image."""

import numpy as np
import matplotlib.pyplot as plt
import time
from typing import Optional, Literal
from puzzle import Puzzle
from utils import plot


class MultiPartPuzzle:
    """Represents a multi-part nonogram puzzle composed of multiple consecutive puzzles."""

    def __init__(
        self,
        start_id: int,
        end_id: int,
        layout: tuple[int, int],
        limit_generate: int = 5_000_000,
        strategy: Literal[None, "force_generate", "guess"] = "force_generate",
        check_ungenerated: bool = True,
    ):
        """Initialize a multi-part puzzle from consecutive puzzle IDs.

        Args:
            start_id: First puzzle ID in the sequence
            end_id: Last puzzle ID in the sequence (inclusive)
            layout: Grid layout as (rows, cols) - e.g., (2, 2) for 2x2 grid
            limit_generate: Maximum number of possible lines to generate for each puzzle
            strategy: Solving strategy - None, "force_generate", or "guess"
            check_ungenerated: Whether to check ungenerated lines during solving
        """
        self.start_id = start_id
        self.end_id = end_id
        self.layout = layout
        self.rows, self.cols = layout
        
        # Validate that we have the right number of puzzles
        n_puzzles = end_id - start_id + 1
        expected = self.rows * self.cols
        if n_puzzles != expected:
            raise ValueError(
                f"Layout {layout} expects {expected} puzzles, "
                f"but ID range {start_id}-{end_id} provides {n_puzzles}"
            )
        
        # Initialize all puzzle parts
        print(f"Initializing multi-part puzzle with {n_puzzles} parts ({self.rows}x{self.cols} layout)")
        self.parts = []
        for puzzle_id in range(start_id, end_id + 1):
            print(f"  Loading puzzle {puzzle_id}...")
            puzzle = Puzzle(
                puzzle_id=puzzle_id,
                limit_generate=limit_generate,
                strategy=strategy,
                check_ungenerated=check_ungenerated,
            )
            self.parts.append(puzzle)
        
        # Store common attributes from first puzzle
        self.n_colors = self.parts[0].n_colors
        self.colors = self.parts[0].colors
        
        # Verify all parts have same colors
        for i, puzzle in enumerate(self.parts):
            if puzzle.n_colors != self.n_colors:
                print(f"Warning: Part {i} has {puzzle.n_colors} colors, expected {self.n_colors}")
            if puzzle.colors != self.colors:
                print(f"Warning: Part {i} has different color palette")

    def solve_all(
        self,
        do_plot: bool = False,
        max_iterations: Optional[int] = None,
        benchmark_output: bool = False,
    ):
        """Solve all parts of the multi-part puzzle.

        Args:
            do_plot: Whether to plot each puzzle as it's solved
            max_iterations: Maximum iterations per puzzle
            benchmark_output: Whether to print benchmark output for each puzzle
        """
        total_start = time.perf_counter()
        
        for i, puzzle in enumerate(self.parts):
            row = i // self.cols
            col = i % self.cols
            print(f"\n{'='*60}")
            print(f"Solving part {i+1}/{len(self.parts)} (row {row}, col {col})")
            print(f"Puzzle ID: {puzzle.id0}")
            print(f"Description: {puzzle.desc}")
            print(f"{'='*60}")
            
            start = time.perf_counter()
            puzzle.solve(
                do_plot=do_plot,
                max_iterations=max_iterations,
                benchmark_output=benchmark_output,
            )
            elapsed = time.perf_counter() - start
            print(f"Part {i+1} completed in {elapsed:.2f}s")
        
        total_elapsed = time.perf_counter() - total_start
        print(f"\n{'='*60}")
        print(f"All {len(self.parts)} parts solved in {total_elapsed:.2f}s")
        print(f"{'='*60}")

    def assemble_image(self) -> np.ndarray:
        """Assemble solved parts into complete image.

        Returns:
            Assembled image as numpy array of shape (total_height, total_width, n_colors)
        """
        # Get dimensions (all parts should have same dimensions for clean assembly)
        part_heights = [p.y for p in self.parts]
        part_widths = [p.x for p in self.parts]
        
        # Find the maximum number of colors across all parts
        max_colors = max(p.n_colors for p in self.parts)
        
        # Calculate dimensions for each row and column
        row_heights = []
        for r in range(self.rows):
            row_parts = self.parts[r * self.cols : (r + 1) * self.cols]
            row_heights.append(max(p.y for p in row_parts))
        
        col_widths = []
        for c in range(self.cols):
            col_parts = [self.parts[r * self.cols + c] for r in range(self.rows)]
            col_widths.append(max(p.x for p in col_parts))
        
        # Create full image array with maximum color count
        full_height = sum(row_heights)
        full_width = sum(col_widths)
        full_image = np.zeros((full_height, full_width, max_colors), dtype=np.bool_)
        
        # Place each part in the correct position
        y_offset = 0
        for row in range(self.rows):
            x_offset = 0
            for col in range(self.cols):
                idx = row * self.cols + col
                puzzle = self.parts[idx]
                
                # Place this part's image (only the colors it has)
                full_image[
                    y_offset : y_offset + puzzle.y,
                    x_offset : x_offset + puzzle.x,
                    :puzzle.n_colors,
                ] = puzzle.color_possible
                
                x_offset += col_widths[col]
            
            y_offset += row_heights[row]
        
        return full_image

    def plot_assembled(self, title: Optional[str] = None, save_path: Optional[str] = None):
        """Plot the assembled multi-part puzzle.

        Args:
            title: Optional title for the plot
            save_path: Optional path to save the plot
        """
        if title is None:
            title = f"Multi-part Puzzle {self.start_id}-{self.end_id}"
        
        # Calculate dimensions for each row and column
        row_heights = []
        for r in range(self.rows):
            row_parts = self.parts[r * self.cols : (r + 1) * self.cols]
            row_heights.append(max(p.y for p in row_parts))
        
        col_widths = []
        for c in range(self.cols):
            col_parts = [self.parts[r * self.cols + c] for r in range(self.rows)]
            col_widths.append(max(p.x for p in col_parts))
        
        # Create full RGB image
        full_height = sum(row_heights)
        full_width = sum(col_widths)
        rgb_image = np.zeros((full_height, full_width, 3))
        
        # Render each part with its own color palette
        y_offset = 0
        for row in range(self.rows):
            x_offset = 0
            for col in range(self.cols):
                idx = row * self.cols + col
                puzzle = self.parts[idx]
                
                # Convert this part to RGB using its own color palette
                part_rgb = np.zeros((puzzle.y, puzzle.x, 3))
                for i in range(puzzle.n_colors):
                    color_hex = puzzle.colors[i]
                    r = int(color_hex[0:2], 16) / 255
                    g = int(color_hex[2:4], 16) / 255
                    b = int(color_hex[4:6], 16) / 255
                    part_rgb[puzzle.color_possible[:, :, i], :] = [r, g, b]
                
                # Place this part in the full image
                rgb_image[
                    y_offset : y_offset + puzzle.y,
                    x_offset : x_offset + puzzle.x,
                    :,
                ] = part_rgb
                
                x_offset += col_widths[col]
            
            y_offset += row_heights[row]
        
        # Create figure
        plt.figure(figsize=(12, 12))
        plt.imshow(rgb_image)
        plt.title(title, fontsize=16)
        plt.axis("off")
        
        # Draw grid lines to show puzzle boundaries
        ax = plt.gca()
        
        # Vertical lines
        x_pos = 0
        for col in range(self.cols):
            if col > 0:
                ax.axvline(x=x_pos - 0.5, color='red', linewidth=2, alpha=0.5)
            x_pos += col_widths[col]
        
        # Horizontal lines
        y_pos = 0
        for row in range(self.rows):
            if row > 0:
                ax.axhline(y=y_pos - 0.5, color='red', linewidth=2, alpha=0.5)
            y_pos += row_heights[row]
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Assembled image saved to {save_path}")
        
        plt.show()

    def save_all_solutions(self):
        """Save individual solution files for each part."""
        for i, puzzle in enumerate(self.parts):
            puzzle.save_solution()
            print(f"Saved solution for part {i+1} (ID: {puzzle.id0})")

    def save_all_plots(self):
        """Save individual plot files for each part."""
        for i, puzzle in enumerate(self.parts):
            puzzle.save_plot()
            print(f"Saved plot for part {i+1} (ID: {puzzle.id0})")

    def get_part_info(self) -> str:
        """Get summary information about all parts.

        Returns:
            Formatted string with part information
        """
        info = []
        info.append(f"Multi-part Puzzle: {self.start_id}-{self.end_id}")
        info.append(f"Layout: {self.rows}x{self.cols} ({len(self.parts)} parts)")
        info.append(f"Colors: {self.n_colors}")
        info.append("")
        
        for i, puzzle in enumerate(self.parts):
            row = i // self.cols
            col = i % self.cols
            info.append(f"Part {i+1} (row {row}, col {col}):")
            info.append(f"  ID: {puzzle.id0}")
            info.append(f"  Size: {puzzle.x}x{puzzle.y}")
            info.append(f"  Description: {puzzle.desc.split(chr(10))[0]}")
            info.append("")
        
        return "\n".join(info)
