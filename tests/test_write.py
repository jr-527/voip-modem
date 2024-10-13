import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from defs import write_pipe, repeat_every

def write_stuff():
    write_pipe(bytes(1024))

repeat_every(write_stuff, 0.5)