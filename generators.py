from functools import cache
import numpy as np
from utils import totuple

WHITE = 0

@cache
def generate_lines(
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
            a3 = generate_lines(
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
def calculate_count(
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
            tmp = calculate_count(
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
def calculate_slice(
    n, n_colors, block_lengths, block_colors, slice, previous_color=-1
):
    # Our check before makes sure that this call only happens with
    # block_lengths == block_colors == []
    # So this is always possible and fine
    if n == 0:
        return True, np.zeros((0, n_colors), dtype=np.bool_)

    slice = np.asarray(slice, dtype=np.bool_)

    result = np.zeros((n, n_colors), dtype=np.bool_)

    # If there are no more blocks to place
    if len(block_lengths) == 0:
        # If for all remaining positions white is allowed, we return success
        if np.all(slice[:, WHITE]):
            result[:, WHITE] = True
            return True, result
        # Otherwise we return failure
        else:
            return False, None

    # We can estimate the maximum number of whites allowed on the left side

    # How far can we push the blocks to the left?
    n_same_colored_neighbours = sum(np.diff(block_colors) == 0)
    max_zeroes_left_side_from_input = n - sum(block_lengths) - n_same_colored_neighbours

    # How many whites are allowed on the left side?
    non_white = np.where(~slice[:, WHITE])[0]
    max_zeroes_left_side_from_slice = non_white[0] if len(non_white) > 0 else n

    # The maximum number of whites allowed on the left side is the minimum of the two
    i1 = min(
        max_zeroes_left_side_from_input, max_zeroes_left_side_from_slice
    )

    # If we are the same color as the previous block, we have to start at 1
    length0 = block_lengths[0]
    color0 = block_colors[0]
    if color0 == previous_color:
        i0 = 1
    else:
        i0 = 0
    
    # We try to start the block at every possible position
    at_least_one_successful_placement = False
    for i in range(i0, i1 + 1):

        # If the next block is not even allowed at that place, we continue
        if not all(slice[i : (i + length0), color0]):
            continue

        # So now assume it placed and calculate the remaining blocks
        success, part_result = calculate_slice(
                n=n - i - length0,
                n_colors=n_colors,
                block_lengths=block_lengths[1:],
                block_colors=block_colors[1:],
                slice=totuple(slice[i + length0 :, :]),
                previous_color=color0
            )

        # If it is not possible, we continue
        if not success:
            continue
        
        # For the whole function, it is important to log at least one successful placement
        at_least_one_successful_placement = True

        # Build up the result for this starting position
        tmp_result = np.zeros((n, n_colors), dtype=np.bool_)
        tmp_result[:i, WHITE] = True
        tmp_result[i : (i + length0), color0] = True
        tmp_result[i + length0:, :] = part_result

        # OR with previous results
        result |= tmp_result

    if at_least_one_successful_placement:
        return True, result
    else:
        return False, None
