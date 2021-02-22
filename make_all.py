# -*- coding: utf-8 -*-

# python3 make_all.py -py python3 -mpb 5 -ao -overwrite -probe

import argparse
import glob
import os
from pprint import pprint
import subprocess
import sys

from lib import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="DATA_DIR", default="data/lines/*.csv", help="Path to input data directory")
parser.add_argument('-ao', dest="AUDIO_ONLY", action="store_true", help="Only output audio?")
parser.add_argument('-vo', dest="VIDEO_ONLY", action="store_true", help="Only output video?")
parser.add_argument('-reverse', dest="REVERSE", action="store_true", help="Reverse the line?")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing files?")
parser.add_argument('-mpb', dest="METERS_PER_BEAT", type=int, default=75, help="Higher numbers creates shorter songs")
parser.add_argument('-sw', dest="STATION_WIDTH", type=float, default=0.125, help="Minimum station width as a percent of the screen width; adjust this to change the overall visual speed")
parser.add_argument('-out', dest="OUTPUT_DIR", default="output/all/", help="Media output file")
parser.add_argument('-py', dest="PYTHON_NAME", default="python", help="Python command name, e.g. python or python3")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Only output commands?")
a = parser.parse_args()

# For passing in express lines with local stops
localLinesMap = {
    "2": "1",
    "3": "1",
    "4": "6",
    "5": "6",
    "A": "C",
    "D": "B",
    "Q": "N"
}

# filter out lines with underscore (e.g. A_LEF)
filenames = glob.glob(a.DATA_DIR)
lines = []
for fn in filenames:
    basename = getBasename(fn)
    if "_" not in basename:
        lines.append({
            "filename": fn,
            "name": basename
        })

for line in lines:
    basename = "subway_line_%s"
    if a.REVERSE:
        basename += "_reverse"
    aout = a.OUTPUT_DIR + basename + ".mp3"
    dout = a.OUTPUT_DIR + basename + ".csv"
    out = a.OUTPUT_DIR + basename + ".mp4"

    command = [a.PYTHON_NAME,
               'make.py',
               '-data', f'data/lines/{line["name"]}.csv',
               '-img', f'img/{line["name"]}.png',
               '-mpb', str(a.METERS_PER_BEAT),
               '-sw', str(a.STATION_WIDTH),
               '-aout', aout,
               '-dout', dout,
               '-out', out]

    if line["name"] in localLinesMap:
        locName = localLinesMap[line["name"]]
        command += ['-loc', f'data/lines/{locName}.csv']

    if a.REVERSE:
        command.append('-reverse')

    if a.AUDIO_ONLY:
        command.append('-ao')
    elif a.VIDEO_ONLY:
        command.append('-vo')
    if a.OVERWRITE:
        command.append('-overwrite')

    print("==============================")
    print(" ".join(command))
    if not a.PROBE:
        finished = subprocess.check_call(command)

print("==============================")
print("Done.")
