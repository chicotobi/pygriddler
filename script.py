from download import get_input
from solution import initialize, solve
import matplotlib.pyplot as plt
import sys
import os.path

def compare_output_with_blueprint(example_number):
  blueprint_file = os.path.join('blueprint', f'{example_number}.txt')
  if not os.path.isfile(blueprint_file):
    raise ValueError(f"Blueprint file for example {example_number} does not exist.")
  with open('output.txt', 'r') as f:
    output = f.read()
  with open(blueprint_file, 'r') as f:
    blueprint = f.read()
  match = output == blueprint
  print(f"\n{'✓ SUCCESS' if match else '✗ FAILURE'}: Output {'matches' if match else 'does not match'} blueprint")
  return match

plt.ion()

inp = {}
inp["limit_generate"] = 5_000_000
inp["plot"] = True
inp["example"] = 4

# Redirect stdout to file
sys.stdout = open('output.txt', 'w')

inp = get_input(inp)
initialize(inp)
solve(inp)

# Restore stdout
sys.stdout.close()
sys.stdout = sys.__stdout__

# Compare output with blueprint
compare_output_with_blueprint(inp["id0"])

plt.ioff()  # Turn off interactive mode
plt.show()  # Show the final plot and wait  