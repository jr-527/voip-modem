import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from defs import read_pipe, write_pipe

class Demodulator:
    SYMBOL_SIZE = 1024
    def init(self) -> bytes:
        """
        Returns a `bytes` object of length self.SYMBOL_SIZE representing the
        first complete symbol read from stdin.

        The input signal is unlikely to be synchronized with stdin, ie
        ~~~text
        signal input: [  first symbol ][ second symbol ][  third symbol ]
        what we get:        [ received data ]
        ~~~
        This function's job is to discard the end of the first symbol, read from stdin
        until we get to the end of the second symbol, and return that symbol:
        ~~~text
        signal input: [  first symbol ][ second symbol ][  third symbol ]
        what we get:        [ received data ]
                            (discarded)[kept][more read]
        then we return                 [ data returned ]
        ~~~
        """
        data: bytes = read_pipe(self.SYMBOL_SIZE)
        num_discarded = 123
        data = data[num_discarded:] + read_pipe(num_discarded)
        return data
    

    def handle(self, data: bytes):
        """
        This function's job is to handle one full symbol, writing the
        demodulated data to stdout.
        data: One full symbol
        """
        write_pipe(bytes(128))

    def run(self):
        packet_size = 1024
        data: bytes = self.init()
        while True:
            self.handle(data)
            data = read_pipe(self.SYMBOL_SIZE)


if __name__ == "__main__":
    Demodulator().run()