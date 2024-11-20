'''
import sys
import os
import time
from datetime import datetime
from typing import Callable, Any, NoReturn
import functools
import operator
from multiprocessing.connection import Client, Listener
from threading import Thread
from abc import ABCMeta, abstractmethod

windows_pipe_init = [False]

def timestamp() -> str:
    """
    Returns a string timestamp of the current time, ie
    "2024-01-12 00:25:51.698313" or "2024-10-06 17:10:29.712207"
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

def log(msg, *args):
    """
    Writes a log message to stdout. Has an identical call signature to printf.
    I recommend doing log(timestamp() + log_msg)
    """
    if len(args) == 0:
        print(msg, file=sys.stderr)
    else:
        print(str(msg)%args, file=sys.stderr)

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



class PythonIPC(metaclass=ABCMeta):
    """You need to implement main_loop_iteration and receive_message"""
    def __init__(self, address: tuple[str, int], mode: str):
        """
        address: ast.literal_eval(sys.argv[1])
        mode: "client" or "host"
        """
        self._interrupt = False
        assert mode in ("client", "host")
        self.mode = mode
        self.address = address
        self.connection_started = False
        if self.mode == "host":
            self.listener = Listener(self.address, authkey=b"voip-modem password!")
            self.address = self.listener.address


    def __del__(self):
        self.stop()


    def _thread_func_recv(self):
        try:
            while not self._interrupt:
                if self._conn.poll():
                    x = self._conn.recv_bytes().decode("utf-8")
                    msg_type = x[0]
                    msg = x[1:]
                    self.receive_message(msg, msg_type)
                time.sleep(.05)
        except:
            self._interrupt = True


    def _thread_main_loop(self):
        try:
            while not self._interrupt:
                time.sleep(.05)
                self.main_loop_iteration()
        except:
            self._interrupt = True


    def start_connection(self):
        self.connection_started = True
        if self.mode == "client":
            self.address = self.address
            self._conn = Client(self.address, authkey=b"voip-modem password!")
        else:
            self._conn = self.listener.accept()
        thread1 = Thread(target=self._thread_func_recv)
        thread1.start()


    def run_main_loop(self):
        if not self.connection_started:
            self.start_connection()
        thread = Thread(target=self._thread_main_loop)
        thread.start()


    def send_message(self, message: str, message_type=">"):
        out = bytes(message_type, encoding="utf-8")
        out += bytes(message, encoding="utf-8")
        self._conn.send_bytes(out)


    def stop(self):
        self._interrupt = True
        if self.mode == "host":
            self.listener.close()
    

    def is_alive(self):
        return not self._interrupt


    @abstractmethod
    def main_loop_iteration(self):
        """Needs to be implemented. Can just return without doing anything."""
        raise NotImplementedError
    
    @abstractmethod
    def receive_message(self, message: str, message_type: str):
        """
        Needs to be implemented. This gets called whenever a message is received.
        message: Whatever message
        message_type: String with len 1. ">" for plain text, "j" for json, "q" means the other end is signing off
        """
        raise NotImplementedError
'''