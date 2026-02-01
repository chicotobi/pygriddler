from functools import cache
import numpy as np
from utils import totuple

WHITE = 0

@cache
def _solve_line_recursive(
    n, n_colors, block_lengths, block_colors, slice, mode, previous_color=-1
):
    """Unified recursive function for nonogram line solving.
    
    Args:
        mode: 'count', 'lines', or 'slice'
    """
    # Base case: line length is zero
    if n == 0:
        if mode == "count":
            return True, 1
        elif mode == "lines":
            return True, np.zeros((1, 0), dtype=np.uint8)
        else:  # mode == "slice"
            return True, np.zeros((0, n_colors), dtype=np.bool_)

    # Ensure slice is a tuple (already handled by wrappers/recursive calls)
    slice_arr = np.asarray(slice, dtype=np.bool_)

    # Initialization for mode-specific results
    if mode == "slice":
        result = np.zeros((n, n_colors), dtype=np.bool_)
    elif mode == "lines":
        possible_lines = []
    elif mode == "count":
        count = 0

    # Case: no more blocks to place
    if len(block_lengths) == 0:
        if np.all(slice_arr[:, WHITE]):
            if mode == "count":
                return True, 1
            elif mode == "lines":
                return True, np.zeros((1, n), dtype=np.uint8)
            else:  # mode == "slice"
                result[:, WHITE] = True
                return True, result
        else:
            return False, None

    # Constraint boundaries calculation
    n_same_colored_neighbours = sum(np.diff(block_colors) == 0)
    max_zeroes_left_side_from_input = n - sum(block_lengths) - n_same_colored_neighbours
    non_white = np.where(~slice_arr[:, WHITE])[0]
    max_zeroes_left_side_from_slice = non_white[0] if len(non_white) > 0 else n

    i1 = min(max_zeroes_left_side_from_input, max_zeroes_left_side_from_slice)
    
    length0 = block_lengths[0]
    color0 = block_colors[0]
    i0 = 1 if color0 == previous_color else 0

    at_least_one_successful_placement = False
    
    for i in range(i0, i1 + 1):
        # Check if current block can be placed
        if not all(slice_arr[i : (i + length0), color0]):
            continue

        # Recursive call
        res = _solve_line_recursive(
            n=n - i - length0,
            n_colors=n_colors,
            block_lengths=block_lengths[1:],
            block_colors=block_colors[1:],
            slice=totuple(slice_arr[i + length0 :, :]),
            mode=mode,
            previous_color=color0,
        )

        success, part_res = res
        if not success:
            continue
        
        at_least_one_successful_placement = True
        
        if mode == "count":
            count += part_res
        elif mode == "lines":
            n_part = part_res.shape[0]
            tmp = np.zeros((n_part, n), dtype=np.uint8)
            tmp[:, i : (i + length0)] = color0
            tmp[:, (i + length0) :] = part_res
            possible_lines.append(tmp)
        elif mode == "slice":
            # Build up result by ORing current placement and recursive result
            result[:i, WHITE] = True
            result[i : (i + length0), color0] = True
            result[i + length0 :, :] |= part_res

    if at_least_one_successful_placement:
        if mode == "count":
            return True, count
        elif mode == "lines":
            return True, np.concatenate(possible_lines, axis=0)
        else:  # mode == "slice"
            return True, result
    else:
        return False, None


def generate_lines(n, n_colors, block_lengths, block_colors, slice, previous_color=-1):
    return _solve_line_recursive(
        n, n_colors, block_lengths, block_colors, totuple(slice), "lines", previous_color
    )


def calculate_count(n, n_colors, block_lengths, block_colors, slice, previous_color=-1):
    return _solve_line_recursive(
        n, n_colors, block_lengths, block_colors, totuple(slice), "count", previous_color
    )


def calculate_slice(n, n_colors, block_lengths, block_colors, slice, previous_color=-1):
    return _solve_line_recursive(
        n, n_colors, block_lengths, block_colors, totuple(slice), "slice", previous_color
    )
