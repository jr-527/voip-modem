import time
import sys
write = sys.stdout.buffer.write
def err(string):
    print(string, file=sys.stderr)

write(bytes([i%128 for i in range(1024)]))
sys.stdout.flush()
err("test1.py done writing")
