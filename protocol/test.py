import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from defs import read_pipe, write_pipe, log

class Protocol:
    pass