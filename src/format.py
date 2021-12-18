#!/usr/bin/env python
# Program to format strings coming out of `jq`. Used
# in `get_tesla_gateway_meter_data.sh`.
import re
import sys

out = sys.stdin.read()
fs = out.strip().split(",")

# Fix up the date to remove decimal seconds
fs[0] = re.sub(r"\.\d+-", "-", fs[0])

# Format floats
fs[1:7] = [f"{float(n):8.2f}" for n in fs[1:7]]

# Print modified record
print(", ".join(fs))
