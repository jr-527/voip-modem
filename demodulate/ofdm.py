import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from defs import read_pipe, write_pipe, log
from common_algorithms.ofdm1 import decode_segment, synchronize, BYTES_PER_SYMBOL, SAMPLES_PER_SYMBOL, SAMPLES_PER_GUARD
import numpy as np
import matplotlib.pyplot as plt

def main():
    while 1:
        data = np.frombuffer(read_pipe(SAMPLES_PER_SYMBOL*4), dtype=np.float32)
        idx = None
        while 1:
            idx = synchronize(data)
            if idx is None:
                continue
            elif SAMPLES_PER_GUARD < idx:
                data = np.append(data, read_pipe((SAMPLES_PER_SYMBOL-idx)*4))
            else: # 0 <= idx <= SAMPLES_PER_GUARD
                break
        # We lost some of the guard interval but who cares
        write_pipe(decode_segment(data[idx:]))


try:
    main()
except:
    pass