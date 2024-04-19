from download import get_input
from solution import initialize, solve

inp = {}
inp["limit_generate"] = 5_000_000
inp["plot"] = True
inp["example"] = 7

get_input(inp)
initialize(inp)
solve(inp)  