
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from defs import read_pipe, write_pipe, log
from common_algorithms.ofdm1 import generate_segment, BYTES_PER_SYMBOL
import numpy as np
import matplotlib.pyplot as plt

try:
    while 1:
        data = read_pipe(BYTES_PER_SYMBOL)
        segment = generate_segment(data)
        write_pipe(segment.tobytes())
except:
    # out of data
    pass