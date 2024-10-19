import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from pipe_setup import run_pipe

try:
    run_pipe(["tests/generate_data.py", "modulate/ofdm.py", "demodulate/ofdm.py"])
except:
    pass