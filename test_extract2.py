import sys
import os

sys.path.append(r'd:\FreeCadAgent\sketch2cad\backend\agents\parameter')

from extractor import extract_parameters

try:
    print(extract_parameters("ten meters", ["length"]))
except Exception as e:
    print("Error:", e)
