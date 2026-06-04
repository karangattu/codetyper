---
language: python
output_file: demo_from_script.py
typing_speed: 0.01
execute_blocks: true
format_output: true
---

## Setup and run analysis | execute=true, pause_after=2.0
import pandas as pd
import numpy as np

data = {
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'score': [85, 90, 95]
}
df = pd.DataFrame(data)

print("Sample DataFrame:")
print(df)
print(f"\nMean age: {df['age'].mean()}")
