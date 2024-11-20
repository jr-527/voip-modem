from piped_worker import PipedWorker
from ofdm1 import generate_segment, BYTES_PER_SYMBOL

class ModulateOFDM(PipedWorker):
    def push(self, data: bytes):
        if len(data) != BYTES_PER_SYMBOL:
            raise ValueError(f"Input must be {BYTES_PER_SYMBOL=} bytes long.")
        segment = generate_segment(data, add_mls=True)*32
        self.target.push(segment)
