import matplotlib.pyplot as plt
import matplotlib.colors
import numpy as np


def totuple(x):
    return tuple(tuple(i) for i in x)


def hex2rgb(hx):
    return tuple(int(hx[i : i + 2], 16) / 256 for i in (0, 2, 4))


def nice_number(n):
    x = 6
    s = " " * (x * 3 - len(str(n))) + str(n)
    s2 = ".".join([s[3 * i : 3 * i + 3] for i in range(x)])
    return s2


def msg(ori, line, msg_type, n, nold=None):
    ori = {"vertical": 0, "horizontal": 1}[ori]
    line = "0" * (3 - len(str(line))) + str(line)

    if msg_type == "generated":
        msg = f"{'Generated':<20}{nice_number(n)}"
    elif msg_type == "counted":
        msg = f"{'Counted':<20}{nice_number(n)}"
    elif msg_type == "reduced":
        if n == nold:
            msg = f"{'Same at':<20}{nice_number(n)}"
        else:
            if n == 1:
                msg = f"{'Finished':<20}{nice_number(n)} from {nice_number(nold)}"
            else:
                msg = f"{'Reduced to':<20}{nice_number(n)} from {nice_number(nold)}"
    elif msg_type == "reduced slice sum":
        if n == nold:
            msg = f"{'Slice sum same at':<20}{nice_number(n)}"
        else:
            msg = (
                f"{'Slice sum reduced to':<20}{nice_number(n)} from {nice_number(nold)}"
            )

    print(f"O{ori}L{line} {msg}")


def plot(title, iteration, color_possible, colors, ori):
    plt.clf()
    if ori == "horizontal":
        color_possible = np.transpose(color_possible, axes=(1, 0, 2))

    colors = ["808080"] + colors
    cmap = [hex2rgb(i) for i in colors]
    cmap = matplotlib.colors.ListedColormap(cmap)

    x, y, ncolors = color_possible.shape
    data = -1 * np.ones((x, y))
    for i in range(x):
        for j in range(y):
            if sum(color_possible[i, j, :]) == 1:
                # print(np.where(color_possible[i,j,:]))
                data[i, j] = np.where(color_possible[i, j, :])[0][0] + 1
            else:
                data[i, j] = -1
    plt.imshow(data, interpolation="nearest", cmap=cmap, vmin=-1, vmax=len(colors))
    plt.gca().get_xaxis().set_visible(False)
    plt.gca().get_yaxis().set_visible(False)
    plt.title(title + " - " + str(iteration))
    plt.gcf().canvas.draw()
    plt.gcf().canvas.flush_events()
    plt.show(block=False)
    plt.pause(0.05)  # Longer pause to ensure display updates


class NoSolutionError(Exception):
    """Raised when a puzzle line or configuration has no valid solution.

    This typically indicates either:
    1. An impossible puzzle constraint
    2. A contradiction discovered during assumption-based solving
    """

    pass


class NoUpdateError(Exception):
    """Raised when a puzzle line or configuration has no valid solution.

    This typically indicates either:
    1. An inconclusive puzzle constraint
    """

    pass
