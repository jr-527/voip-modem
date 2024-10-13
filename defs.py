import sys
import os
import time
from datetime import datetime
from typing import Callable, Any, NoReturn
import functools
import operator

windows_pipe_init = [False]

def timestamp() -> str:
    """
    Returns a string timestamp of the current time, ie
    "2024-01-12 00:25:51.698313" or "2024-10-06 17:10:29.712207"
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

def log(msg: str, *args: tuple[str]):
    """
    Writes a log message to stdout. Has an identical call signature to printf.
    I recommend doing log(timestamp() + log_msg)
    """
    if len(args) == 0:
        print(msg, file=sys.stderr)
    else:
        print(msg%args, file=sys.stderr)

def write_pipe(data: bytes):
    """Writes `data` to stdout. Blocks until it's done."""
    sys.stdout.buffer.write(data)
    sys.stdout.flush()

def short_read_pipe(max_bytes: int) -> bytes:
    """
    Reads up to `max_bytes` bytes from stdin.
    """
    global windows_pipe_init
    # global os
    if sys.platform == "win32" and not windows_pipe_init[0]:
        windows_pipe_init[0] = True
        # set sys.stdin to binary mode
        import msvcrt
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    return os.read(0, max_bytes)

def read_pipe(num_bytes: int) -> bytes:
    """
    Reads `num_bytes` bytes from stdin. Blocks until it's done.
    """
    # global os
    global windows_pipe_init
    if sys.platform == "win32" and not windows_pipe_init[0]:
        windows_pipe_init[0] = True
        # set sys.stdin to binary mode
        import msvcrt
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    out: list[bytes] = []
    num_read: int = 0
    while num_read < num_bytes:
        data = os.read(0, num_bytes-num_read)
        if len(data) == 0:
            raise RuntimeError("stdin EOF")
        num_read += len(data)
        out.append(data)
    return functools.reduce(operator.add, out)

def repeat_every(func: Callable[[], Any], delay: float) -> NoReturn:
    """
    Calls `func` every `delay` seconds (`func` must finish executing before then).

    If we just do

    ~~~python
    while True:
        output_stuff()
        time.sleep(delay)
    ~~~

    Then each iteration will take slightly longer than delay, and it'll drift.
    """
    start_time = time.monotonic()
    prev = start_time
    while True:
        now = time.monotonic()
        if now - prev >= 2*delay:
            errmsg = "Execution too slow! Took %f s to execute (has to execute in %f s)"
            errmsg %= (now-prev, delay)
            raise RuntimeError(errmsg)
        prev = now
        func()
        time.sleep(delay - ((time.monotonic() - start_time) % delay))