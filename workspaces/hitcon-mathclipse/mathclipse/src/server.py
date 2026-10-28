import json
import math

def one(step):
    if type(step) is not list or len(step) != 1 or type(step[0]) not in (str, int):
        raise ValueError("bad step")
    return step[0]

def slot(path):
    obj = math
    for step in path[:-1]:
        obj = getattr(obj, step) if type(step) is str else obj[one(step)]
    key = one(path[-1])
    return obj, key, obj[key]

pairs = json.loads(input("> "))

assert len(pairs) == 2 and all(
    len(pair) == 2 and all(1 <= len(path) <= 6 for path in pair)
    for pair in pairs
) and sum(len(path) for pair in pairs for path in pair) <= 19

resolved = [(slot(a), slot(b)) for a, b in pairs]

for (x, i, u), (y, j, v) in resolved:
    x[i], y[j] = v, u
