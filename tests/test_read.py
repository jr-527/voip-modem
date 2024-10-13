
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from defs import read_pipe

while 1:
    x = read_pipe(1024)
    print(len(x), sum(x))