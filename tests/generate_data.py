import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from defs import write_pipe, log
import time

try:
    for i in range(123):
        write_pipe(bytes(f"{i} Hello, how are you?\n", encoding="utf-8"))
except:
    pass