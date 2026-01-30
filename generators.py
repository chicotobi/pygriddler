from functools import cache
import numpy as np
from utils import totuple

WHITE = 0

@cache
def generate_from_slice(
    n, n_colors, block_lengths, block_colors, slice, previous_color=-1
):
    if n == 0:
        return np.zeros((1, 0), dtype=np.uint8)
    slice = np.asarray(slice, dtype=np.bool_)
    if len(block_lengths) == 0:
        if all(slice[:, WHITE]):
            return np.zeros((1, n), dtype=np.uint8)
        else:
            return np.zeros((0, n), dtype=np.uint8)
    possible_lines = []
    n_same_colored_neighbours = sum(np.diff(block_colors) == 0)
    max_zeroes_left_side_from_input = n - sum(block_lengths) - n_same_colored_neighbours

    # Find the first index where no white is allowed
    non_white = np.where(~slice[:, WHITE])[0]
    max_zeroes_left_side_from_slice = non_white[0] if len(non_white) > 0 else n

    length0 = block_lengths[0]
    color0 = block_colors[0]

    max_zeroes_left_side = min(
        max_zeroes_left_side_from_input, max_zeroes_left_side_from_slice
    )
    if block_colors[0] == previous_color:
        i0 = 1
    else:
        i0 = 0
    for i in range(i0, max_zeroes_left_side + 1):
        # We checked that the white blocks are allowed, now check, if the colored block is allowed:
        if all(slice[i : (i + length0), color0]):
            a3 = generate_from_slice(
                n=n - i - length0,
                n_colors=n_colors,
                block_lengths=block_lengths[1:],
                block_colors=block_colors[1:],
                slice=totuple(slice[i + length0 :,]),
                previous_color=color0,
            )
            nrow, _ = a3.shape
            if a3.shape[0] > 0:
                a1 = np.zeros((nrow, i), dtype=np.uint8)
                a2 = np.ones((nrow, length0), dtype=np.uint8) * color0
                a = np.concatenate((a1, a2, a3), axis=1)
                possible_lines.append(a)
    if len(possible_lines) > 0:
        return np.concatenate(possible_lines)
    else:
        return np.zeros((0, n), dtype=np.uint8)


@cache
def generate_count_from_slice(
    n, n_colors, block_lengths, block_colors, slice, previous_color=-1
):
    if n == 0:
        return 1
    slice = np.asarray(slice, dtype=np.bool_)
    if len(block_lengths) == 0:
        if all(slice[:, WHITE]):
            return 1
        else:
            return 0
    count = 0
    n_same_colored_neighbours = sum(np.diff(block_colors) == 0)
    max_zeroes_left_side_from_input = n - sum(block_lengths) - n_same_colored_neighbours

    # Find the first index where no white is allowed
    non_white = np.where(~slice[:, WHITE])[0]
    max_zeroes_left_side_from_slice = non_white[0] if len(non_white) > 0 else n

    length0 = block_lengths[0]
    color0 = block_colors[0]

    max_zeroes_left_side = min(
        max_zeroes_left_side_from_input, max_zeroes_left_side_from_slice
    )
    if block_colors[0] == previous_color:
        i0 = 1
    else:
        i0 = 0
    for i in range(i0, max_zeroes_left_side + 1):
        # We checked that the white blocks are allowed, now check, if the colored block is allowed:
        if all(slice[i : (i + length0), color0]):
            tmp = generate_count_from_slice(
                n=n - i - length0,
                n_colors=n_colors,
                block_lengths=block_lengths[1:],
                block_colors=block_colors[1:],
                slice=totuple(slice[i + length0 :,]),
                previous_color=color0,
            )
            count += tmp
    return count


@cache
def generate_color_possible_from_slice(
    n, n_colors, block_lengths, block_colors, slice, previous_color=-1
):
    slice = np.asarray(slice, dtype=np.bool_)

    result = np.zeros((n, n_colors), dtype=np.bool_)

    if n == 0:
        return np.zeros((0, n_colors), dtype=np.bool_)

    if len(block_lengths) == 0:
        result[:, WHITE] = slice[:, WHITE]
        return result

    n_same_colored_neighbours = sum(np.diff(block_colors) == 0)
    max_zeroes_left_side_from_input = n - sum(block_lengths) - n_same_colored_neighbours

    # Find the first index where no white is allowed
    non_white = np.where(~slice[:, WHITE])[0]
    max_zeroes_left_side_from_slice = non_white[0] if len(non_white) > 0 else n

    length0 = block_lengths[0]
    color0 = block_colors[0]

    max_zeroes_left_side = min(
        max_zeroes_left_side_from_input, max_zeroes_left_side_from_slice
    )
    if block_colors[0] == previous_color:
        i0 = 1
    else:
        i0 = 0
    for i in range(i0, max_zeroes_left_side + 1):
        # We checked that the white blocks are allowed, now check, if the colored block is allowed:
        if all(slice[i : (i + length0), color0]):
            a2 = generate_color_possible_from_slice(
                n=n - i - length0,
                n_colors=n_colors,
                block_lengths=block_lengths[1:],
                block_colors=block_colors[1:],
                slice=totuple(slice[i + length0 :, :]),
                previous_color=color0,
            )

            # Build result for this starting position
            a1 = np.zeros((i + length0, n_colors), dtype=np.bool_)
            a1[:i, WHITE] = True  # Mark whites as possible
            a1[i : (i + length0), color0] = True  # Mark current color as possible
            a = np.concatenate((a1, a2), axis=0)

            # OR with previous results
            result = np.logical_or(result, a)

    return result
