# -*- coding: utf-8 -*-

# python3 make.py -loc "data/lines/1.csv" -overwrite
# python3 make.py -loc "data/lines/1.csv" -rtl -overwrite
# python3 combine.py
# python3 make.py -data "data/lines/A_LEF.csv" -loc "data/lines/C.csv" -img "img/A.png" -sw 0.281 -tw 0.29 -overwrite
# python3 make.py -data "data/lines/A_LEF.csv" -loc "data/lines/C.csv" -img "img/A.png" -sw 0.281 -tw 0.29 -rtl -overwrite
# python3 combine.py -in "output/subway_line_A.mp4,output/subway_line_A_rtl.mp4" -out "output/subway_line_A_loop.mp4"
# python3 make.py -data "data/lines/7.csv" -img "img/7.png" -sw 0.2345 -tw 0.27125 -reverse -overwrite
# python3 make.py -data "data/lines/7.csv" -img "img/7.png" -sw 0.2345 -tw 0.27125 -reverse -rtl -overwrite
# python3 combine.py -in "output/subway_line_7.mp4,output/subway_line_7_rtl.mp4" -out "output/subway_line_7_loop.mp4"

import argparse
import gizeh
import numpy as np
import os
from PIL import Image, ImageDraw, ImageFont
from pprint import pprint
import sys

from lib import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-data', dest="DATA_FILE", default="data/lines/2.csv", help="Input csv file with preprocessed data")
parser.add_argument('-loc', dest="DATA_LOCAL_FILE", default="", help="Input csv file with preprocessed data of a local train that should 'fill in' stations in-between express trains")
parser.add_argument('-img', dest="IMAGE_FILE", default="img/2.png", help="Subway bullet image")
parser.add_argument('-instruments', dest="INSTRUMENTS_FILE", default="data/instruments.csv", help="Input csv file with instruments config")
parser.add_argument('-dir', dest="MEDIA_DIRECTORY", default="audio/", help="Input media directory")
parser.add_argument('-width', dest="WIDTH", default=1920, type=int, help="Output video width")
parser.add_argument('-height', dest="HEIGHT", default=1080, type=int, help="Output video height")
parser.add_argument('-pad0', dest="PAD_START", default=2000, type=int, help="Pad start in ms")
parser.add_argument('-pad1', dest="PAD_END", default=2000, type=int, help="Pad end in ms")
parser.add_argument('-fps', dest="FPS", default=60, type=int, help="Output video frames per second")
parser.add_argument('-outframe', dest="OUTPUT_FRAME", default="tmp/line_%s/frame.%s.png", help="Output frames pattern")
parser.add_argument('-aout', dest="AUDIO_OUTPUT_FILE", default="output/subway_line_%s.mp3", help="Output audio file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="output/subway_line_%s.mp4", help="Output media file")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing files?")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just view statistics?")
parser.add_argument('-reverse', dest="REVERSE", action="store_true", help="Reverse the line?")
parser.add_argument('-rtl', dest="RIGHT_TO_LEFT", action="store_true", help="Play from right to left?")
parser.add_argument('-ao', dest="AUDIO_ONLY", action="store_true", help="Only output audio?")
parser.add_argument('-vo', dest="VIDEO_ONLY", action="store_true", help="Only output video?")
parser.add_argument('-viz', dest="VISUALIZE_SEQUENCE", action="store_true", help="Output a visualization of the sequence")
parser.add_argument('-frame', dest="SINGLE_FRAME", default=-1, type=int, help="Output just a single frame")

# Music config
parser.add_argument('-db', dest="MASTER_DB", type=float, default=1.2, help="Master +/- decibels to be applied to final audio")
parser.add_argument('-bpm', dest="BPM", type=int, default=120, help="Beats per minute, e.g. 60, 75, 100, 120, 150")
parser.add_argument('-mpb', dest="METERS_PER_BEAT", type=int, default=75, help="Higher numbers creates shorter songs")
parser.add_argument('-dpb', dest="DIVISIONS_PER_BEAT", type=int, default=4, help="e.g. 4 = quarter notes, 8 = eighth notes")
parser.add_argument('-pm', dest="PRICE_MULTIPLIER", type=float, default=1.3, help="Makes instruments more expensive; higher numbers = less instruments playing")
parser.add_argument('-vdur', dest="VARIANCE_MS", type=int, default=20, help="+/- milliseconds an instrument note should be off by to give it a little more 'natural' feel")

# Visual design config
parser.add_argument('-sw', dest="STATION_WIDTH", type=float, default=0.25, help="Minumum station width as a percent of the screen width; adjust this to change the overall visual speed")
parser.add_argument('-tw', dest="TEXT_WIDTH", type=float, default=0.3, help="Station text width as a percent of the screen width")
parser.add_argument('-cy', dest="CENTER_Y", type=float, default=0.475, help="Center y as a percent of screen height")
parser.add_argument('-bty', dest="BOROUGH_TEXT_Y", type=float, default=0.575, help="Borough text center y as a percent of screen height")
parser.add_argument('-sty', dest="STATION_TEXT_Y", type=float, default=0.325, help="Station text center y as a percent of screen height")
parser.add_argument('-cw', dest="CIRCLE_WIDTH", type=int, default=90, help="Circle radius in pixels assuming 1920x1080")
parser.add_argument('-lh', dest="LINE_HEIGHT", type=int, default=28, help="Height of horizontal line in pixels assuming 1920x1080")
parser.add_argument('-bh', dest="BOUNDARY_HEIGHT", type=int, default=166, help="Height of boundary line in pixels assuming 1920x1080")
parser.add_argument('-bw', dest="BOUNDARY_WIDTH", type=int, default=3, help="Width of boundary line in pixels assuming 1920x1080")
parser.add_argument('-bm', dest="BOUNDARY_MARGIN", type=int, default=48, help="Horizontal margin of boundary line in pixels assuming 1920x1080")
parser.add_argument('-mw', dest="MARKER_WIDTH", type=int, default=8, help="Height of horizontal line in pixels assuming 1920x1080")
parser.add_argument('-sts', dest="STATION_TEXT_SIZE", type=int, default=60, help="Station text size in pixels assuming 1920x1080")
parser.add_argument('-stm', dest="STATION_TEXT_MARGIN", type=int, default=20, help="Station text bottom margin in pixels assuming 1920x1080")
parser.add_argument('-slm', dest="STATION_LETTER_MARGIN", type=int, default=1, help="Space after each station text letter in pixels assuming 1920x1080")
parser.add_argument('-bts', dest="BOROUGH_TEXT_SIZE", type=int, default=48, help="Borough text size in pixels assuming 1920x1080")
parser.add_argument('-blm', dest="BOROUGH_LETTER_MARGIN", type=int, default=1, help="Space after each borough text letter in pixels assuming 1920x1080")
parser.add_argument('-dw', dest="DIVIDER_WIDTH", type=int, default=28, help="Line divider in pixels assuming 1920x1080")
parser.add_argument('-dd', dest="DIVIDER_DISTANCE", type=float, default=0.333, help="Distance between dividers as a percent of screen width")
parser.add_argument('-dc', dest="DIVIDER_COLOR", default="#666666", help="Distance between dividers as a percent of screen width")
parser.add_argument('-bg', dest="BG_COLOR", default="#000000", help="Background color")
parser.add_argument('-tc', dest="TEXT_COLOR", default="#eeeeee", help="Text color")
parser.add_argument('-atc', dest="ALT_TEXT_COLOR", default="#aaaaaa", help="Secondary text color")
parser.add_argument('-mc', dest="MARKER_COLOR", default="#dddddd", help="Marker color")
parser.add_argument('-sfont', dest="STATION_FONT", default="fonts/OpenSans-Bold.ttf", help="Station font")
parser.add_argument('-bfont', dest="BOROUGH_FONT", default="fonts/OpenSans-SemiBold.ttf", help="Borough font")
parser.add_argument('-map', dest="MAP_IMAGE", default="img/nyc.png", help="Station font")
parser.add_argument('-mcoord', dest="MAP_COORDS", default=" -74.1261,40.9087,-73.7066,40.5743", help="Top left, bottom right point")
parser.add_argument('-mapm', dest="MAP_MARGIN", type=int, default=30, help="Margin of map in pixels assuming 1920x1080")
parser.add_argument('-mapw', dest="MAP_W", type=int, default=260, help="Map width in pixels assuming 1920x1080")
parser.add_argument('-mlw', dest="MAP_LINE_WIDTH", type=int, default=4, help="Map line in pixels assuming 1920x1080")
parser.add_argument('-mlc', dest="MAP_LINE_COLOR", default="#eeeeee", help="Secondary text color")
a = parser.parse_args()

startTime = logTime()

# Calculations
BEAT_MS = roundInt(60.0 / a.BPM * 1000)
ROUND_TO_NEAREST = roundInt(1.0 * BEAT_MS / a.DIVISIONS_PER_BEAT)

basename = getBasename(a.DATA_FILE)
if "_" in basename:
    basename, _ = tuple(basename.split("_"))
if a.RIGHT_TO_LEFT:
    basename += "_rtl"

# Read data
_, stations = readCsv(a.DATA_FILE)
_, instruments = readCsv(a.INSTRUMENTS_FILE)
lstations = []
if len(a.DATA_LOCAL_FILE):
    _, lstations = readCsv(a.DATA_LOCAL_FILE)

# Parse instruments
instruments = prependAll(instruments, ("file", a.MEDIA_DIRECTORY))
instruments = [i for i in instruments if i["active"] > 0]
instruments = addIndices(instruments, "index")
for i, instrument in enumerate(instruments):
    instruments[i]["from_beat_ms"] = roundInt(1.0 * BEAT_MS / instrument["from_tempo"])
    instruments[i]["to_beat_ms"] = roundInt(1.0 * BEAT_MS / instrument["to_tempo"])
    instruments[i]["interval_ms"] = roundInt(instrument["interval_phase"] * BEAT_MS)
    instruments[i]["price"] = instrument["price"] * a.PRICE_MULTIPLIER

# Buy instruments based on a specified budget
def buyInstruments(station, instrumentsShelf):
    budget = station['income'] / 12.0
    percentile = station['percentile']
    instrumentsCart = []
    for i in instrumentsShelf:
        # skip if not in bracket
        if percentile < i['bracket_min'] or percentile >= i['bracket_max']:
            continue
        # add to cart if in budget
        elif i['price'] < budget:
            budget -= i['price']
            instrumentsCart.append(i.copy())
        # out of budget, finished
        else:
            break
    return instrumentsCart

# Add local stations in-between express ones
if len(lstations) > 0:
    lbasename = getBasename(a.DATA_LOCAL_FILE)
    estations = {}
    addStations = []
    for i, s in enumerate(stations):
        lines = str(s["Daytime Routes"]).split(" ")
        if lbasename in lines:
            estations[s["Station ID"]] = s.copy()
    sortByStart = None
    currentLStations = []
    for i, s in enumerate(lstations):
        if s["Station ID"] in estations:
            if sortByStart is not None and len(currentLStations) > 0:
                step = 1.0 / (len(currentLStations) + 1)
                for j, ls in enumerate(currentLStations):
                    currentLStations[j]["sortBy"] = sortByStart + (j+1) * step
                    currentLStations[j]["isLocal"] = True
                addStations += currentLStations
                currentLStations = []
            sortByStart = estations[s["Station ID"]]["sortBy"]
        elif sortByStart is not None:
            currentLStations.append(s)
    stations += addStations
    # stations = sorted(stations, key=lambda d: d["sortBy"])
    # for s in stations:
    #     if "isLocal" in s:
    #         print(" --"+s["Stop Name"])
    #     else:
    #         print(s["Stop Name"])
    # sys.exit()

# Parse stations
stations = sorted(stations, key=lambda d: d["income"])
stations = addNormalizedValues(stations, "income", "nIncome")
stations = addIndices(stations, "incomeIndex")
isReverse = a.REVERSE
if a.RIGHT_TO_LEFT:
    isReverse = (not isReverse)
stations = sorted(stations, key=lambda d: d["sortBy"], reverse=isReverse)
stations = addIndices(stations, "index")
stationCount = len(stations)
ms = a.PAD_START
for i, station in enumerate(stations):
    stations[i]["percentile"] = 1.0 * station["incomeIndex"] / stationCount * 100
    # stations[i]["percentile"] = min(99.999, 1.0 * station["nIncome"] * 100)
    stations[i]["instruments"] = buyInstruments(stations[i], instruments)
    # print(len(stations[i]["instruments"]))
    distance = beats = duration = 0
    if i < stationCount-1:
        distance = earthDistance(stations[i+1]['GTFS Latitude'], stations[i+1]['GTFS Longitude'], station['GTFS Latitude'], station['GTFS Longitude'])
        beats = roundInt(1.0 * distance / a.METERS_PER_BEAT)
        duration = beats * BEAT_MS
        boroughNext = stations[i+1]["Borough"]
    stations[i]["distance"] = distance
    stations[i]["beats"] = beats
    stations[i]["duration"] = duration
    stations[i]["vduration"] = duration
    stations[i]["BoroughNext"] = boroughNext
    stations[i]["ms"] = ms
    ms += duration

# Calculate ranges
distances = [s["distance"] for s in stations if s["distance"] > 0]
totalDistance = sum(distances)
minDistance, maxDistance = (min(distances), max(distances))
durations = [s["duration"] for s in stations if s["duration"] > 0]
totalMs = sum(durations)
minDuration, maxDuration = (min(durations), max(durations))
totalBeats = sum([s["beats"] for s in stations])

totalSeconds = roundInt(totalMs / 1000.0)
secondsPerStation = roundInt(1.0*totalSeconds/stationCount)
print('Total distance in meters: %s' % roundInt(totalDistance))
print('Distance range in meters: [%s, %s]' % (roundInt(minDistance), roundInt(maxDistance)))
print('Average beats per station: %s' % roundInt(1.0*totalBeats/stationCount))
print('Average time per station: %s' % formatSeconds(secondsPerStation))
print('Main sequence beats: %s' % totalBeats)

# Retrieve gain based on current beat
def getVolume(instrument, beat):
    beats_per_phase = instrument['gain_phase']
    percent_complete = float(beat % beats_per_phase) / beats_per_phase
    percent = easeSin(percent_complete)
    from_volume = instrument['from_volume']
    to_volume = instrument['to_volume']
    volume = lerp((from_volume, to_volume), percent)
    return volume

# Get beat duration in ms based on current point in time
def getBeatMs(instrument, beat, round_to):
    from_beat_ms = instrument['from_beat_ms']
    to_beat_ms = instrument['to_beat_ms']
    beats_per_phase = instrument['tempo_phase']
    percent_complete = float(beat % beats_per_phase) / beats_per_phase
    percent = easeSin(percent_complete)
    ms = lerp((from_beat_ms, to_beat_ms), percent)
    ms = roundInt(roundToNearest(ms, round_to))
    return ms

# Return if the instrument should be played in the given interval
def isValidInterval(instrument, elapsed_ms, start_ms, end_ms, minIntervalDuration=3000):
    interval_ms = instrument['interval_ms']
    interval = instrument['interval']
    interval_offset = instrument['interval_offset']
    isValid = (int(math.floor(1.0*elapsed_ms/interval_ms)) % interval == interval_offset)
    # return isValid
    if end_ms - start_ms <= minIntervalDuration * 3:
        return isValid
    # check to see if we're at the start and not long enough
    if isValid and elapsed_ms < (start_ms+minIntervalDuration) and not isValidInterval(instrument, start_ms+minIntervalDuration, start_ms, end_ms, minIntervalDuration):
        isValid = False
    # make start interval earlier if necessary
    elif not isValid and elapsed_ms < (start_ms+minIntervalDuration) and isValidInterval(instrument, start_ms+minIntervalDuration, start_ms, end_ms, minIntervalDuration):
        isValid = True
    # check to see if we're at the end and not long enough
    elif isValid and elapsed_ms > (end_ms-minIntervalDuration) and not isValidInterval(instrument, end_ms-minIntervalDuration, start_ms, end_ms, minIntervalDuration):
        isValid = False
    # make start interval earlier if necessary
    elif not isValid and elapsed_ms > (end_ms-minIntervalDuration) and isValidInterval(instrument, end_ms-minIntervalDuration, start_ms, end_ms, minIntervalDuration):
        isValid = True
    return isValid

# Add beats to sequence
def addBeatsToSequence(sequence, instrument, duration, ms, beat_ms, round_to, pad_start):
    msStart = ms
    msEnd = ms + duration
    offset_ms = int(instrument['tempo_offset'] * beat_ms)
    ms += offset_ms
    previous_ms = int(ms)
    from_beat_ms = instrument['from_beat_ms']
    to_beat_ms = instrument['to_beat_ms']
    min_ms = min(from_beat_ms, to_beat_ms)
    remaining_duration = int(duration)
    elapsed_duration = offset_ms
    continue_from_prev = (instrument['bracket_min'] > 0 or instrument['bracket_max'] < 100)
    rn = pseudoRandom(instrument["index"]+1)
    while remaining_duration >= min_ms:
        elapsed_ms = int(ms)
        elapsed_beat = int((elapsed_ms-previous_ms) / beat_ms)
        # continue beat from previous
        if continue_from_prev:
            elapsed_beat = int(elapsed_ms / beat_ms)
        this_beat_ms = getBeatMs(instrument, elapsed_beat, round_to)
        # add to sequence if in valid interval
        if isValidInterval(instrument, elapsed_ms, msStart, msEnd):
            variance = roundInt(rn * a.VARIANCE_MS * 2 - a.VARIANCE_MS)
            sequence.append({
                'instrumentIndex': instrument["index"],
                'filename': instrument["file"],
                'volume': getVolume(instrument, elapsed_beat),
                'ms': max([pad_start + elapsed_ms + variance, 0])
            })
        remaining_duration -= this_beat_ms
        elapsed_duration += this_beat_ms
        ms += this_beat_ms
    return sequence

# Build main sequence
sequence = []
for i, instrument in enumerate(instruments):
    ms = 0
    stationQueueDur = 0
    # Each station in stations
    for station in stations:
        # Check if instrument is in this station
        instrumentIndex = findInList(station['instruments'], 'index', instrument['index'])
        # Instrument not here, just add the station duration and continue
        if instrumentIndex < 0 and stationQueueDur > 0:
            sequence = addBeatsToSequence(sequence, instrument, stationQueueDur, ms, BEAT_MS, ROUND_TO_NEAREST, a.PAD_START)
            ms += stationQueueDur + station['duration']
            stationQueueDur = 0
        elif instrumentIndex < 0:
            ms += station['duration']
        else:
            stationQueueDur += station['duration']
    if stationQueueDur > 0:
        sequence = addBeatsToSequence(sequence, instrument, stationQueueDur, ms, BEAT_MS, ROUND_TO_NEAREST, a.PAD_START)
sequenceDuration = max([s["ms"] for s in sequence]) + a.PAD_END
# Now start the video frame logic

# Calculations
aa = vars(a)
aa["STATION_WIDTH"] = roundInt(1.0 * a.WIDTH * a.STATION_WIDTH)
aa["TEXT_WIDTH"] = roundInt(1.0 * a.WIDTH * a.TEXT_WIDTH)
aa["CENTER_Y"] = roundInt(1.0 * a.HEIGHT * a.CENTER_Y)
aa["BOROUGH_TEXT_Y"] = roundInt(1.0 * a.HEIGHT * a.BOROUGH_TEXT_Y)
aa["STATION_TEXT_Y"] = roundInt(1.0 * a.HEIGHT * a.STATION_TEXT_Y)
RESOLUTION = a.WIDTH / 1920.0
aa["CIRCLE_WIDTH"] = roundInt(a.CIRCLE_WIDTH * RESOLUTION)
aa["LINE_HEIGHT"] = roundInt(a.LINE_HEIGHT * RESOLUTION)
aa["BOUNDARY_MARGIN"] = roundInt(a.BOUNDARY_MARGIN * RESOLUTION)
aa["BOUNDARY_HEIGHT"] = roundInt(a.BOUNDARY_HEIGHT * RESOLUTION)
aa["BOUNDARY_WIDTH"] = roundInt(a.BOUNDARY_WIDTH * RESOLUTION)
aa["MARKER_WIDTH"] = roundInt(a.MARKER_WIDTH * RESOLUTION)
aa["STATION_TEXT_SIZE"] = roundInt(a.STATION_TEXT_SIZE * RESOLUTION)
aa["STATION_TEXT_MARGIN"] = roundInt(a.STATION_TEXT_MARGIN * RESOLUTION)
aa["STATION_LETTER_MARGIN"] = roundInt(a.STATION_LETTER_MARGIN * RESOLUTION)
aa["BOROUGH_TEXT_SIZE"] = roundInt(a.BOROUGH_TEXT_SIZE * RESOLUTION)
aa["BOROUGH_LETTER_MARGIN"] = roundInt(a.BOROUGH_LETTER_MARGIN * RESOLUTION)
aa["MAP_COORDS"] = tuple([float(c) for c in a.MAP_COORDS.strip().split(",")])
aa["MAP_MARGIN"] = roundInt(a.MAP_MARGIN * RESOLUTION)
aa["MAP_W"] = roundInt(a.MAP_W * RESOLUTION)
aa["MAP_LINE_WIDTH"] = roundInt(a.MAP_LINE_WIDTH * RESOLUTION)
aa["DIVIDER_WIDTH"] = roundInt(a.DIVIDER_WIDTH * RESOLUTION)
aa["DIVIDER_DISTANCE"] = roundInt(1.0 * a.WIDTH * a.DIVIDER_DISTANCE)

# Add borough names
boroughNames = {
    "Q": "Queens",
    "M": "Manhattan",
    "Bk": "Brooklyn",
    "Bx": "Bronx",
    "SI": "Staten Island"
}
for i, station in enumerate(stations):
    stations[i]["borough"] = boroughNames[station["Borough"]]

x = 0
mlon0, mlat0, mlon1, mlat1 = a.MAP_COORDS
vstations = stations[:]

# If going right to left, reverse the stations visually
if a.RIGHT_TO_LEFT:
    vstations = list(reversed(vstations))
    for i, station in enumerate(vstations):
        if i < stationCount-1:
            vstations[i]["vduration"] = vstations[i+1]["duration"]
        else:
            vstations[i]["vduration"] = 0

for i, station in enumerate(vstations):
    boroughNext = station["borough"]
    if i < stationCount-1:
        boroughNext = vstations[i+1]["borough"]
    vstations[i]["boroughNext"] = boroughNext
    vstations[i]["width"] = roundInt(1.0 * station["vduration"] / minDuration * a.STATION_WIDTH)
    vstations[i]["x"] = x
    vstations[i]["x0"] = x - a.TEXT_WIDTH / 2
    vstations[i]["x1"] = x + a.TEXT_WIDTH / 2
    vstations[i]["mapNx"] = norm(station["GTFS Longitude"], (mlon0, mlon1))
    vstations[i]["mapNy"] = norm(station["GTFS Latitude"], (mlat0, mlat1))
    x += vstations[i]["width"]
totalW = x
pxPerMs = 1.0 * totalW / totalMs
pxPerS = pxPerMs * 1000.0
pxPerFrame = pxPerS / a.FPS
print("Total width: %s px" % totalW)
print("Pixels per second: %s" % pxPerS)
print("Pixels per frame: %s" % pxPerFrame)

totalFrames = msToFrame(sequenceDuration, a.FPS)
totalFrames = int(ceilToNearest(totalFrames, a.FPS))
print("Total frames: %s" % totalFrames)
sequenceDuration = frameToMs(totalFrames, a.FPS)

def drawFrame(filename, ms, xOffset, stations, totalW, bulletImg, mapImg, fontStation, fontBorough, a):
    if not a.OVERWRITE and os.path.isfile(filename):
        return

    im = Image.new('RGB', (a.WIDTH, a.HEIGHT), a.BG_COLOR)
    draw = ImageDraw.Draw(im, 'RGBA')
    cx = roundInt(a.WIDTH * 0.5)
    cy = a.CENTER_Y
    stationCount = len(stations)

    leftX = xOffset
    rightX = leftX + totalW

    # draw the center line
    x0 = 0 if leftX < 0 else leftX
    x1 = a.WIDTH if rightX > a.WIDTH else rightX
    y0 = cy - a.LINE_HEIGHT/2
    y1 = y0 + a.LINE_HEIGHT
    draw.rectangle([(x0, y0), (x1, y1)], fill=a.ALT_TEXT_COLOR)

    for i, s in enumerate(stations):
        # check to see if we should draw borough divider
        if s["borough"] != s["boroughNext"]:
            deltaBx = abs(stations[i+1]["x"]-s["x"])
            # don't draw boundary in tight space
            if deltaBx > (a.WIDTH * 0.75):
                bdx = roundInt(xOffset + (s["x"] + stations[i+1]["x"]) * 0.5)
                bdx0 = bdx - a.WIDTH/2
                bdx1 = bdx + a.WIDTH/2
                if 0 <= bdx0 <= a.WIDTH or 0 <= bdx1 <= a.WIDTH:
                    dx0 = bdx - a.BOUNDARY_WIDTH/2
                    dx1 = dx0 + a.BOUNDARY_WIDTH
                    dy0 = cy
                    dy1 = dy0 + a.BOUNDARY_HEIGHT
                    draw.rectangle([(dx0, dy0), (dx1, dy1)], fill=a.ALT_TEXT_COLOR)
                    blw, blh = getLineSize(fontBorough, s["borough"], a.BOROUGH_LETTER_MARGIN)
                    bx = dx0 - a.BOUNDARY_MARGIN - blw/2
                    drawTextToImage(draw, s["borough"], fontBorough, a.BOROUGH_LETTER_MARGIN, bx, a.BOROUGH_TEXT_Y, a.ALT_TEXT_COLOR)
                    blw, blh = getLineSize(fontBorough, s["boroughNext"], a.BOROUGH_LETTER_MARGIN)
                    bx = dx1 + a.BOUNDARY_MARGIN + blw/2
                    drawTextToImage(draw, s["boroughNext"], fontBorough, a.BOROUGH_LETTER_MARGIN, bx, a.BOROUGH_TEXT_Y, a.ALT_TEXT_COLOR)

        sx = xOffset + s["x"]
        sy = a.CENTER_Y

        # draw dividers
        if i < stationCount-1:
            dividers = 0
            dividerDistance = 0
            nextSx = xOffset + stations[i+1]["x"]
            deltaSx = abs(nextSx - sx)
            if deltaSx >= a.DIVIDER_DISTANCE * 2:
                dividers = int(1.0 * deltaSx / a.DIVIDER_DISTANCE) - 1
            if dividers > 0:
                dividerDistance = roundInt(1.0 * deltaSx / (dividers+1))
            for di in range(dividers):
                divX = sx + (di+1) * dividerDistance
                divX0 = divX - a.DIVIDER_WIDTH/2
                divX1 = divX0 + a.DIVIDER_WIDTH
                divY0 = y0
                divY1 = y1
                if divX1 > 0:
                    draw.rectangle([(divX0, divY0), (divX1, divY1)], fill=a.DIVIDER_COLOR)

        # check if station is visible
        sx0 = xOffset + s["x0"]
        sx1 = xOffset + s["x1"]
        if not (0 <= sx0 <= a.WIDTH or 0 <= sx1 <= a.WIDTH):
            continue

        # just draw empty bullet for local stops
        if "isLocal" in s:
            brad = roundInt(a.CIRCLE_WIDTH/3)
            bx = sx
            by = sy
            # Draw line using gizeh so it will be smooth
            bsurface = gizeh.Surface(width=a.WIDTH, height=a.HEIGHT)
            circle = gizeh.circle(r=brad, xy=[bx, by], fill=hexToRGB(a.DIVIDER_COLOR, toFloat=True))
            circle.draw(bsurface)
            bpixels = bsurface.get_npimage(transparent=True) # should be shape: h, w, rgba
            circleImg = Image.fromarray(bpixels, mode="RGBA")
            im.paste(circleImg, (0, 0), circleImg)
            continue

        # draw borough text
        bx = sx
        by = a.BOROUGH_TEXT_Y
        drawTextToImage(draw, s["borough"], fontBorough, a.BOROUGH_LETTER_MARGIN, bx, by, a.ALT_TEXT_COLOR)

        # draw bullet
        bx = roundInt(sx - a.CIRCLE_WIDTH/2)
        by = roundInt(sy - a.CIRCLE_WIDTH/2)
        im.paste(bulletImg, (bx, by), bulletImg)

        # draw station text
        stx = sx
        sty = a.STATION_TEXT_Y
        slines = getMultilines(s["Stop Name"], fontStation, a.TEXT_WIDTH, a.STATION_LETTER_MARGIN)
        drawTextLinesToImage(draw, slines, fontStation, a.STATION_TEXT_MARGIN, a.STATION_LETTER_MARGIN, stx, sty, a.TEXT_COLOR)

    # draw the map
    mw, mh = mapImg.size
    mx = a.MAP_MARGIN
    my = a.HEIGHT - mh - a.MAP_MARGIN
    im.paste(mapImg, (mx, my))
    lineColor = "#"+stations[0]["color"]
    points = []
    allPoints = []
    mstations = stations[:]
    if a.RIGHT_TO_LEFT:
        mstations = list(reversed(mstations))
    for i, s in enumerate(mstations):
        sms0 = s["ms"]
        sms1 = sms0 + s["duration"]
        # print("%s, %s" % (sms0, sms1))
        mprogress = norm(ms, (sms0, sms1), limit=True) if s["duration"] > 0 else 1.0
        lx = lerp((mx, mx+mw), s["mapNx"])
        ly = lerp((my, my+mh), s["mapNy"])
        if ms >= sms0:
            points.append((lx, ly))
        if 0.0 < mprogress < 1.0 and i < stationCount-1 and s["duration"] > 0:
            lx1 = lerp((mx, mx+mw), mstations[i+1]["mapNx"])
            ly1 = lerp((my, my+mh), mstations[i+1]["mapNy"])
            lx2 = lerp((lx, lx1), mprogress)
            ly2 = lerp((ly, ly1), mprogress)
            points.append((lx2, ly2))
        allPoints.append((lx, ly))

    # Draw line using gizeh so it will be smooth
    surface = gizeh.Surface(width=a.WIDTH, height=a.HEIGHT)
    line = gizeh.polyline(points=allPoints, stroke_width=max(1, a.MAP_LINE_WIDTH-1), stroke=hexToRGB(a.MAP_LINE_COLOR, toFloat=True))
    line.draw(surface)
    if len(points) > 1:
        sline = gizeh.polyline(points=points, stroke_width=a.MAP_LINE_WIDTH, stroke=hexToRGB(lineColor, toFloat=True))
        sline.draw(surface)
    spixels = surface.get_npimage(transparent=True) # should be shape: h, w, rgba
    lineImage = Image.fromarray(spixels, mode="RGBA")
    im.paste(lineImage, (0, 0), lineImage)

    # draw the marker
    x0 = cx - a.MARKER_WIDTH/2
    x1 = x0 + a.MARKER_WIDTH
    y0 = 0
    y1 = a.HEIGHT
    draw.rectangle([(x0, y0), (x1, y1)], fill=(255,255,255,100))

    del draw
    im.save(filename)
    # print("Saved %s" % filename)

def getEasedFrames(easeFrameCount, stationFrameCount, pxPerFrame):
    fromFrameCount = int(min(easeFrameCount, stationFrameCount) / 2)
    fromPx = fromFrameCount * pxPerFrame
    toFrameCount = easeFrameCount + fromFrameCount # 'fromPx' will be stretched into 'toFrameCount' frames
    easedPoints = [easeIn(n) * pxPerFrame for n in np.linspace(0, 1.0, num=toFrameCount)]
    buckets = [0 for n in range(toFrameCount)]
    pxPool = fromPx
    for i in range(toFrameCount):
        index = toFrameCount-1-i
        bucketPx = buckets[index]
        addPx = easedPoints[index]
        if addPx > pxPool:
            addPx = pxPool
        buckets[index] = addPx
        pxPool -= addPx
        if pxPool <= 0:
            break
    if pxPool > 0:
        incr = 0.01
        while pxPool > 0:
            for j in range(toFrameCount):
                index = toFrameCount-1-j
                bucketPx = buckets[index]
                if (bucketPx+incr) <= pxPerFrame:
                    buckets[index] += incr
                    pxPool -= incr
    # import matplotlib.pyplot as plt
    # plt.plot(buckets)
    # plt.show()
    # sys.exit()
    # print("%s ~ %s" % (fromPx, sum(buckets)))
    return buckets

audioFilename = a.AUDIO_OUTPUT_FILE % basename
print("%s steps in sequence" % len(sequence))
print('Total sequence time: %s' % formatSeconds(sequenceDuration/1000.0))

if a.VISUALIZE_SEQUENCE:
    instrumentsCount = len(instruments)
    labelW = 200
    unitH = 10
    unitW = 10
    marginH = 2
    imgH = (unitH+marginH) * instrumentsCount
    imgW = totalSeconds * unitW + labelW
    dfont = ImageFont.truetype(font="fonts/OpenSans-Regular.ttf", size=10)
    print("Making viz %s x %s" % (imgW, imgH))

    im = Image.new('RGB', (imgW, imgH), "#000000")
    draw = ImageDraw.Draw(im, 'RGB')
    for i, ins in enumerate(instruments):
        y = i * (unitH + marginH)
        draw.text((2, y), ins["name"], fill="#FFFFFF", font=dfont)
        steps = [step for step in sequence if step["instrumentIndex"]==ins["index"]]
        for step in steps:
            sx = roundInt((step["ms"] - a.PAD_START) / 1000.0 / totalSeconds * (imgW-labelW) + labelW)
            draw.rectangle([(sx, y), (sx+3, y+unitH)], fill=(roundInt(255*step["volume"]),0,0))
        if i > 0:
            draw.line([(0, y-1), (imgW, y-1)], fill="#cccccc", width=1)
        printProgress(i+1, instrumentsCount)
    im.save("output/viz.png")
    sys.exit()

if a.PROBE:
    sys.exit()

if not a.AUDIO_ONLY:

    bulletImg = Image.open(a.IMAGE_FILE)
    bulletImg = bulletImg.resize((a.CIRCLE_WIDTH, a.CIRCLE_WIDTH), resample=Image.LANCZOS)
    mapImg = Image.open(a.MAP_IMAGE)
    mapH = roundInt((1.0 * mapImg.size[1] / mapImg.size[0]) * a.MAP_W)
    mapImg = mapImg.resize((a.MAP_W, mapH), resample=Image.LANCZOS)
    fontStation = ImageFont.truetype(font=a.STATION_FONT, size=a.STATION_TEXT_SIZE, layout_engine=ImageFont.LAYOUT_RAQM)
    fontBorough = ImageFont.truetype(font=a.BOROUGH_FONT, size=a.BOROUGH_TEXT_SIZE, layout_engine=ImageFont.LAYOUT_RAQM)

    makeDirectories([a.OUTPUT_FRAME % (basename, "*")])

    if a.OVERWRITE:
        removeFiles(a.OUTPUT_FRAME % (basename, "*"))

    # calculations for easing in/out
    padFrameInCount = msToFrame(a.PAD_START, a.FPS)
    station0FrameCount = msToFrame(stations[0]["duration"], a.FPS)
    easeInFrames = getEasedFrames(padFrameInCount, station0FrameCount, pxPerFrame)
    easeInFrameCount = len(easeInFrames)
    padFrameOutCount = msToFrame(a.PAD_END, a.FPS)
    station1FrameCount = msToFrame(stations[-2]["duration"], a.FPS)
    easeOutFrames = getEasedFrames(padFrameOutCount, station1FrameCount, pxPerFrame)
    # easeOutFrames = list(reversed(easeOutFrames))
    easeOutFrameCount = len(easeOutFrames)
    easeOutPixels = roundInt(sum(easeOutFrames))

    print("Making video frame sequence...")
    videoFrames = []
    centerX = roundInt(a.WIDTH * 0.5)
    xOffset = centerX
    direction = -1
    if a.RIGHT_TO_LEFT:
        direction = 1
        xOffset -= totalW
    xOffsetF = 1.0 * xOffset
    target = centerX-totalW if direction < 0 else centerX
    for f in range(totalFrames):
        frame = f + 1
        ms = frameToMs(frame, a.FPS)
        frameFilename = a.OUTPUT_FRAME % (basename, zeroPad(frame, totalFrames))

        if a.SINGLE_FRAME < 1 or a.SINGLE_FRAME == frame:
            if a.SINGLE_FRAME > 0:
                frameFilename = "output/frame.png"
            drawFrame(frameFilename, ms, xOffset, vstations, totalW, bulletImg, mapImg, fontStation, fontBorough, a)
            if a.SINGLE_FRAME > 0:
                sys.exit()

        pixelsLeft = abs(target - xOffset)

        # ease in start
        if frame < easeInFrameCount:
            xOffsetF += (direction * easeInFrames[frame-1])
            xOffset = roundInt(xOffsetF)
            # print(abs(xOffset-centerX))
        # # correct any discrepancy after ease in
        # elif frame <= easeInFrameCount:
        #     xOffset = (frame - padFrameInCount) * pxPerFrame
        #     xOffsetF = 1.0 * xOffset
        # ease out end
        elif pixelsLeft <= easeOutPixels:
            pxStep = easeOutFrames.pop() if len(easeOutFrames) > 0 else 1
            xOffsetF += (direction * pxStep)
            xOffset = roundInt(xOffsetF)
            # print("%s > %s" % (xOffset, centerX-totalW))
        else:
            xOffset += (direction * pxPerFrame)
            xOffsetF = 1.0 * xOffset
        xOffset = lim(xOffset, (centerX-totalW, centerX))
        printProgress(frame, totalFrames)
    #     break

stepTime = logTime(startTime, "Finished frames")
padZeros = len(str(totalFrames))
outfile = a.OUTPUT_FILE % basename
frameInfile = a.OUTPUT_FRAME % (basename, '%s')

if a.VIDEO_ONLY:
    compileFrames(frameInfile, a.FPS, outfile, padZeros)
    sys.exit()

if a.OVERWRITE or not os.path.isfile(audioFilename):
    mixAudio(sequence, sequenceDuration, audioFilename, masterDb=a.MASTER_DB)
else:
    print("%s already exists" % audioFilename)

stepTime = logTime(stepTime, "Finished Audio")
compileFrames(frameInfile, a.FPS, outfile, padZeros, audioFile=audioFilename)
logTime(startTime, "Total execution time")
