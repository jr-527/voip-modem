import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from pipe_setup import run_pipe

try:
    run_pipe(["record/record.py", "play/play.py"])
except:
    pass