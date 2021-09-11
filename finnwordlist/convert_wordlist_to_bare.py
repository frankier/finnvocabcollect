import sys

line_it = iter(sys.stdin)
next(line_it)

for row in line_it:
    print(row.split(",", 1)[0])
