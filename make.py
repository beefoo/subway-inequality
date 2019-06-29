# -*- coding: utf-8 -*-

import argparse
import os
from pprint import pprint
import sys

from lib import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-data', dest="DATA_FILE", default="data/preprocessed_stations.csv", help="Input csv file with preprocessed data")
parser.add_argument('-instruments', dest="INSTRUMENTS_FILE", default="data/instruments.csv", help="Input csv file with instruments config")
parser.add_argument('-line', dest="LINE", default="2", help="Line to process")
parser.add_argument('-dir', dest="MEDIA_DIRECTORY", default="audio/", help="Input media directory")
parser.add_argument('-width', dest="WIDTH", default=1920, type=int, help="Output video width")
parser.add_argument('-height', dest="HEIGHT", default=1080, type=int, help="Output video height")
parser.add_argument('-fps', dest="FPS", default=60, type=int, help="Output video frames per second")
parser.add_argument('-outframe', dest="OUTPUT_FRAME", default="tmp/frame.%s.png", help="Output frames pattern")
parser.add_argument('-db', dest="MASTER_DB", type=float, default=0.0, help="Master +/- decibels to be applied to final audio")
parser.add_argument('-out', dest="OUTPUT_FILE", default="output/subway_line_%s.mp4", help="Output media file")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just view statistics")
a = parser.parse_args()
