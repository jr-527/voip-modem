import sys
import os
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from defs import write_pipe, read_pipe, log
import random

try:
    while True:
        data = read_pipe(1)
        if random.random() > 0.95:
            which_bit = random.choice(list(range(8)))
            x = int(data[0])
            x ^= 1 << which_bit
            write_pipe(bytes([x]))
        else:
            write_pipe(data)
except RuntimeError:
    log("%s reached EOF" % __file__)
