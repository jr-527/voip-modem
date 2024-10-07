import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from defs import write_pipe, repeat_every, log
import time


byte_data = bytes(12000)
def output():
    # log(timestamp())
    time.sleep(.123)
    write_pipe(byte_data)

repeat_every(output, 0.25)

import time
starttime = time.monotonic()
while True:
    print()
    print((time.monotonic()-starttime)%1)
    output()
    time.sleep(0.25 - ((time.monotonic() - starttime) % 0.25))
