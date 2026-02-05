import random
import builtins


def clamp(v, vmin, vmax):
    return max(vmin, min(v, vmax))


def rnd(v1, v2=None):
    if v2:
      return random.randint(v1, v2)
    return random.randint(0, v1)


def frnd(v1, v2=None):
    if v2:
      return random.uniform(v1, v2)
    return random.uniform(0, v1)


builtins.clamp = clamp
builtins.rnd = rnd
builtins.frnd = frnd
