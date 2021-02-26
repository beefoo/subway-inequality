# -*- coding: utf-8 -*-

# Run:
    # python3 make_all.py -py python3 -mpb 5 -sw 0.4 -reverse -do -out "output/all_data/"
    # python3 make_all.py -py python3 -mpb 5 -sw 0.4 -reverse -do -out "output/all_data/" -reverse

import argparse
import glob
import os
from pprint import pprint
import subprocess
import sys

from lib import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="DATA_DIR", default="output/all_data/*.csv", help="Path to input data directory")
a = parser.parse_args()

indexContent = readTextFile("index.template.html")
itemContent = readTextFile("item.template.html")

lineContent = ''
filenames = glob.glob(a.DATA_DIR)
lines = []
for fn in filenames:
    fieldnames, rows = readCsv(fn)
    basename = getBasename(fn)

    lastStation = rows[-1]
    lineDestination = lastStation["Stop Name"]
    lineName = lastStation["lineName"]

    lineContent += f'<li><a href="lines/{basename}/" class="line-card">'
    lineContent += f' <img src="img/{lineName}.png" alt="{lineName} line symbol" />'
    lineContent += f' <span>{lineDestination}</span>'
    lineContent += '</a></li>'

    stationContent = ''
    for row in rows:
        if row["isLocal"] != "":
            continue
        timestamp = formatSeconds(row["ms"]/1000.0)
        seconds = roundInt(row["ms"]/1000.0)
        stationContent += f'<li><a href="?t={seconds}" class="station-time-link" data-seconds="{seconds}">'
        stationContent += f'<span class="timestamp">{timestamp}</span> <span class="name">{row["Stop Name"]}</span> <span class="income">${formatNumber(row["income"])} approx. median household income</span>'
        stationContent += f'</a></li>'
    itemContentOut = itemContent.format(stationContent=stationContent, basename=basename, lineName=lineName, lineDestination=lineDestination)
    lineFilename = f'lines/{basename}/index.html'
    makeDirectories(lineFilename)
    writeTextFile(lineFilename, itemContentOut)

indexContent = indexContent.format(lineContent=lineContent)
writeTextFile("index.html", indexContent)
