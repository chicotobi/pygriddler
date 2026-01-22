from download import get_input
from solution import initialize, solve
import matplotlib.pyplot as plt
import sys
import os.path

plt.ion()

inp = {}
inp["limit_generate"] = 5_000_000
inp["plot"] = True
inp["example"] = 4

# Redirect stdout to file
# sys.stdout = open('output.txt', 'w')

inp = get_input(inp)
initialize(inp)
solve(inp)

# Restore stdout
# sys.stdout.close()
# sys.stdout = sys.__stdout__

# Compare output with blueprint
# compare_output_with_blueprint(inp["id0"])

plt.ioff()  # Turn off interactive mode
plt.show()  # Show the final plot and wait  