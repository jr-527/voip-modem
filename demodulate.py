from piped_worker import PipedWorker
from ofdm1 import (decode_segment, synchronize, SAMPLES_PER_SYMBOL,
    SAMPLES_PER_GUARD, ISI_LENGTH
)
import numpy as np
# import matplotlib.pyplot as plt

class DemodulateOFDM(PipedWorker):
    def __init__(self):
        self.data = np.array([], dtype=np.float32)

    def push(self, data: np.ndarray[tuple[int], np.dtype[np.float32]]):
        # plt.plot(data)
        # plt.show()
        self.data = np.append(self.data, data)
        i = synchronize(self.data)
        if i is None:
            # no signal found, no need to hold on to this part
            self.data = np.array([], dtype=np.float32)
        elif len(self.data) - i < 3*ISI_LENGTH:
            # we got the front of a symbol but not enough, so we wait
            self.data = self.data[i:]
        else:
            # try reading a symbol
            symbol = self.data[i:i+3*ISI_LENGTH]
            self.data = self.data[i+3*ISI_LENGTH:]
            self.target.push(decode_segment(symbol))
