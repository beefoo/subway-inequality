# -*- coding: utf-8 -*-

import argparse
import os
from pprint import pprint
import subprocess
import sys

from lib import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="FILES", default="output/subway_line_2.mp4,output/subway_line_2_rtl.mp4", help="Input text file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="output/subway_line_2_loop.mp4", help="Media output file")
a = parser.parse_args()

files = a.FILES.strip().split(",")

# Write to temporary file
basename = getBasename(a.OUTPUT_FILE)
tmpFilename = "tmp_%s.txt" % basename
with open(tmpFilename, 'w') as f:
    for fn in files:
        f.write("file '%s'\n" % fn)

# for more options: https://ffmpeg.org/ffmpeg-formats.html#concat
# https://trac.ffmpeg.org/wiki/Concatenate
# ffmpeg -f concat -safe 0 -i mylist.txt -c copy output
command = ['ffmpeg',
           '-f', 'concat',
           '-safe', '0',
           '-i', tmpFilename,
           '-c', 'copy', # https://ffmpeg.org/ffmpeg.html#Stream-copy
           a.OUTPUT_FILE]

print(" ".join(command))
finished = subprocess.check_call(command)

# delete temp file
os.remove(tmpFilename)

print("Done.")
