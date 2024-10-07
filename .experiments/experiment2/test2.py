import sys

total_length = 0
for line in sys.stdin:
    total_length += len(line)
    print(total_length)
print("test2.py done")
