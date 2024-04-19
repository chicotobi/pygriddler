from download import get_id, get_input
from solution import initialize, solve

id0 = get_id(7)

inp = get_input(id0)

inp["limit_generate"] = 5_000_000

initialize(inp)

solve(inp)  