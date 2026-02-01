import numpy as np
import pandas as pd
from typing import Optional
import time
from utils import msg, totuple
from generators import calculate_lines, calculate_count, calculate_slice
from utils import NoSolutionError

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
        generated: bool = False,
    ):
        self._ori = ori
        self._idx = idx
        self._n = n
        self._n_colors = n_colors
        self._block_lengths = block_lengths
        self._block_colors = block_colors
        self._limit_generate = limit_generate
        self._check_ungenerated = check_ungenerated
        self._generated = generated
        self._count = 0
        self._lines = None
        self._slice = None
        self.t_keep = 0.0
        self.t_unique = 0.0
        self.t_calculate_count = 0.0
        self.t_generate_lines = 0.0
        self.t_calculate_slice = 0.0

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
    def lines(self) -> Optional[np.ndarray]:
        return self._lines
    
    @lines.setter
    def lines(self, value: Optional[np.ndarray]):
        self._lines = value

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
    def slice(self) -> Optional[np.ndarray]:
        return self._slice

    @slice.setter
    def slice(self, value: Optional[np.ndarray]):
        self._slice = value

    def initialize(self, slice: np.ndarray) -> np.ndarray:
        """Initialize this line by counting possible solutions and generating initial constraints.

        Args:
          slice: Current color_possible slice
        Returns:
          Updated slice (or unchanged slice if no update needed)
        """

        start = time.perf_counter()
        self._count = calculate_count(
            n=self._n,
            n_colors=self._n_colors,
            block_lengths=self._block_lengths,
            block_colors=self._block_colors,
            slice=totuple(slice),
        )
        self.t_calculate_count += time.perf_counter() - start

        if self._count < self._limit_generate:
            start = time.perf_counter()
            self._lines = calculate_lines(
                n=self._n,
                n_colors=self._n_colors,
                block_lengths=self._block_lengths,
                block_colors=self._block_colors,
                slice=totuple(slice),
            )
            self.t_generate_lines += time.perf_counter() - start
            self._generated = True
            msg(
                self._ori,
                self._idx,
                "generated",
                self._count,
            )
            self.update_slice()
            return self.slice

        start = time.perf_counter()
        self.slice = calculate_slice(
            n=self._n,
            n_colors=self._n_colors,
            block_lengths=self._block_lengths,
            block_colors=self._block_colors,
            slice=totuple(slice),
        )
        self.t_calculate_slice += time.perf_counter() - start
        msg(
            self._ori,
            self._idx,
            "reduced slice sum",
            np.sum(self._slice),
            np.sum(slice),
        )

        return self.slice

    def update(self, slice: np.ndarray, force_generate: bool = False) -> np.ndarray:
        """Update this line based on color_possible constraints.

        Args:
          slice: Current color_possible slice
          force_generate: Whether to force generation even if count is high

        Returns:
          Updated slice (or unchanged slice if no update needed)
        """

        if self._generated:
            # If the relevant slice hasn't changed, skip
            if np.all(self._slice == slice):
                return slice

            old_count = self._count
            self.filter_lines(slice)

            if self._count == 0:
                # This should only happen for contradictions within assumptions
                raise NoSolutionError
            self.update_slice()
            msg(self._ori, self._idx, "reduced", self._count, old_count)

            return self._slice

        start = time.perf_counter()
        self._count = calculate_count(
            n=self._n,
            n_colors=self._n_colors,
            block_lengths=self._block_lengths,
            block_colors=self._block_colors,
            slice=totuple(slice),
        )
        self.t_calculate_count += time.perf_counter() - start
        if self._count < self._limit_generate or force_generate:
            start = time.perf_counter()
            self._lines = calculate_lines(
                n=self._n,
                n_colors=self._n_colors,
                block_lengths=self._block_lengths,
                block_colors=self._block_colors,
                slice=totuple(slice),
            )
            self.t_generate_lines += time.perf_counter() - start
            self._generated = True
            msg(
                self._ori,
                self._idx,
                "generated",
                self._count,
            )
            self.update_slice()
            return self.slice

        if self._check_ungenerated:
            # If the relevant slice hasn't changed, skip
            if np.all(self._slice == slice):
                return slice
            start = time.perf_counter()
            self._slice = calculate_slice(
                n=self._n,
                n_colors=self._n_colors,
                block_lengths=self._block_lengths,
                block_colors=self._block_colors,
                slice=totuple(slice),
            )
            self.t_calculate_slice += time.perf_counter() - start
            msg(
                self._ori,
                self._idx,
                "reduced slice sum",
                np.sum(self._slice),
                np.sum(slice),
            )

        return self._slice

    def filter_lines(self, slice: np.ndarray):
        """Update this line's lines based on color constraints.

        Args:
          slice: Extracted slice (len_line x n_colors)
        """
        lines0 = self._lines
        start = time.perf_counter()
        # Vectorized filtering: build single mask for all constraints
        keep_mask = np.ones(len(lines0), dtype=bool)
        for color in range(self._n_colors):
            extracted_row = slice[:, color]
            invalid_positions = np.where(~extracted_row)[0]
            if len(invalid_positions) > 0:
                # Lines that have this color at any invalid position should be removed
                keep_mask &= ~(lines0[:, invalid_positions] == color).any(
                    axis=1
                )
        lines0 = lines0[keep_mask, :]
        self.t_keep += time.perf_counter() - start
        self._count = len(lines0)
        self._lines = lines0

    def update_slice(self):
        """Reduce the possible lines to the color possible slice of this line"""
        if not self.generated:
            raise RuntimeError(
                "Line must be generated before getting color possible slice."
            )

        # Possibly the computational bottleneck
        start = time.perf_counter()
        self.slice = np.zeros(
            (self.n, self._n_colors), dtype=np.bool_
        )
        for idx in range(self.n):
            allowed_colors = pd.unique(self._lines[:, idx])
            for color in allowed_colors:
                self.slice[idx, color] = True
        self.t_unique += time.perf_counter() - start
