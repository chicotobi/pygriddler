import numpy as np
import pandas as pd
from typing import Optional
import time
from utils import msg, totuple
from generators import generate, generate_count
from generators import generate_from_slice, generate_count_from_slice
from generators import generate_color_possible_from_slice
from utils import NoSolutionError

# Global counter for benchmarking get_color_possible_slice bottleneck
_time_unique = 0.0
_time_keep = 0.0


class PuzzleLine:
    """Tracks the state of a single row/column in the puzzle."""

    def __init__(
        self,
        ori: str,
        idx: int,
        n: int,
        n_colors: int,
        block_lengths: tuple,
        block_colors: tuple,
        limit_generate: int = 5_000_000,
        check_ungenerated: bool = False,
        possible_lines: Optional[np.ndarray] = None,
        generated: bool = False,
        count: int = 0,
    ):
        self._ori = ori
        self._idx = idx
        self._n = n
        self._n_colors = n_colors
        self._block_lengths = block_lengths
        self._block_colors = block_colors
        self._limit_generate = limit_generate
        self._check_ungenerated = check_ungenerated
        self._possible_lines = possible_lines
        self._generated = generated
        self._count = count
        self._slice_of_color_possible = None

    @property
    def n(self) -> int:
        return self._n

    @property
    def n_colors(self) -> int:
        return self._n_colors

    @property
    def block_lengths(self) -> tuple:
        return self._block_lengths

    @property
    def block_colors(self) -> tuple:
        return self._block_colors

    @property
    def check_ungenerated(self) -> bool:
        return self._check_ungenerated

    @property
    def possible_lines(self) -> Optional[np.ndarray]:
        return self._possible_lines

    @possible_lines.setter
    def possible_lines(self, value: Optional[np.ndarray]):
        self._possible_lines = value

    @property
    def generated(self) -> bool:
        return self._generated

    @generated.setter
    def generated(self, value: bool):
        self._generated = value

    @property
    def count(self) -> int:
        return self._count

    @count.setter
    def count(self, value: int):
        self._count = value

    @property
    def slice_of_color_possible(self) -> Optional[np.ndarray]:
        return self._slice_of_color_possible

    @slice_of_color_possible.setter
    def slice_of_color_possible(self, value: Optional[np.ndarray]):
        self._slice_of_color_possible = value

    def update(self, slice: np.ndarray) -> np.ndarray:
        """Update this line based on color_possible constraints.

        Args:
          slice: Current color_possible slice

        Returns:
          Updated slice (or unchanged slice if no update needed)
        """

        if self._generated:
            # If the relevant slice of color_possible hasn't changed, skip
            if np.all(self._slice_of_color_possible == slice):
                return slice

            new_slice, new_count = self.update_from_color_possible(slice)
            if new_count == 0:
                # This should only happen for contradictions within assumptions
                raise NoSolutionError(
                    f"Line {self._ori} {self._idx} has no possible solutions left!"
                )

            return new_slice
        elif self._check_ungenerated:
            new_slice = generate_color_possible_from_slice(
                n=self._n,
                n_colors=self._n_colors,
                block_lengths=self._block_lengths,
                block_colors=self._block_colors,
                slice=totuple(slice),
            )
            msg(
                self._ori,
                self._idx,
                "reduced slice sum",
                np.sum(new_slice),
                np.sum(slice),
            )
            return new_slice
        else:
            return slice

    def update_from_color_possible(self, row_data: np.ndarray):
        """Update this line's possible_lines based on color_possible constraints.

        Args:
          row_data: Extracted row data (len_line x n_colors)
        """
        global _time_keep
        old_count = self._count
        possible_lines0 = self._possible_lines
        start = time.perf_counter()
        # Vectorized filtering: build single mask for all constraints
        keep_mask = np.ones(len(possible_lines0), dtype=bool)
        for color in range(self._n_colors):
            extracted_row = row_data[:, color]
            invalid_positions = np.where(~extracted_row)[0]
            if len(invalid_positions) > 0:
                # Lines that have this color at any invalid position should be removed
                keep_mask &= ~(possible_lines0[:, invalid_positions] == color).any(
                    axis=1
                )
        possible_lines0 = possible_lines0[keep_mask, :]
        _time_keep += time.perf_counter() - start
        self._count = len(possible_lines0)
        self._possible_lines = possible_lines0
        msg(self._ori, self._idx, "reduced", self._count, old_count)
        return self.get_slice(), self._count

    def get_slice(self):
        """Reduce the possible lines to the color_possible slice of this line"""
        global _time_unique
        if not self.generated:
            raise RuntimeError(
                "Line must be generated before getting color possible slice."
            )

        # Possibly the computational bottleneck
        start = time.perf_counter()
        y = np.zeros((self.n, self._n_colors), dtype=np.bool_)
        for idx in range(self.n):
            allowed_colors = pd.unique(self._possible_lines[:, idx])
            for color in allowed_colors:
                y[idx, color] = True
        _time_unique += time.perf_counter() - start

        self.slice_of_color_possible = y
        return y

    def generate_count(self) -> int:
        """Wrapper for generate_count - counts possible line configurations."""
        self._count = generate_count(
            n=self._n,
            block_lengths=self._block_lengths,
            block_colors=self._block_colors,
        )
        return self._count

    def generate(self) -> np.ndarray:
        """Wrapper for generate - generates all possible line configurations.

        Sets possible_lines and generated flag internally, returns color_possible slice.
        """
        self._possible_lines = generate(
            n=self._n,
            block_lengths=self._block_lengths,
            block_colors=self._block_colors,
        )
        self._generated = True
        return self.get_slice()

    def generate_count_from_slice(self, slice: np.ndarray) -> int:
        """Wrapper for generate_count_from_slice - counts possible configurations given constraints."""
        self._count = generate_count_from_slice(
            n=self._n,
            n_colors=self._n_colors,
            block_lengths=self._block_lengths,
            block_colors=self._block_colors,
            slice=totuple(slice),
        )
        return self._count

    def generate_from_slice(self, slice: np.ndarray) -> np.ndarray:
        """Wrapper for generate_from_slice - generates possible configurations given constraints.

        Sets possible_lines and generated flag internally, returns color_possible slice.
        """
        self._possible_lines = generate_from_slice(
            n=self._n,
            n_colors=self._n_colors,
            block_lengths=self._block_lengths,
            block_colors=self._block_colors,
            slice=totuple(slice),
        )
        self._generated = True
        return self.get_slice()

    def generate_color_possible_from_slice(self, slice: np.ndarray) -> np.ndarray:
        """Wrapper for generate_color_possible_from_slice - generates color possibilities from slice."""
        return generate_color_possible_from_slice(
            n=self._n,
            n_colors=self._n_colors,
            block_lengths=self._block_lengths,
            block_colors=self._block_colors,
            slice=totuple(slice),
        )

    def initialize(self, slice: np.ndarray) -> np.ndarray:
        """Initialize this line by counting and optionally generating solutions.

        Args:
          slice: Current color_possible slice

        Returns:
          Updated color_possible slice
        """
        n_pos = self.generate_count_from_slice(slice)
        new_slice = self.generate_color_possible_from_slice(slice)

        if n_pos < self._limit_generate:
            new_slice = self.generate()
            msg(self._ori, self._idx, "generated", n_pos, self._generated)
        else:
            msg(self._ori, self._idx, "counted", n_pos, self._generated)

        return new_slice
