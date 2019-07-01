# -*- coding: utf-8 -*-

import argparse
# import gizeh
import os
from PIL import Image, ImageDraw
from pprint import pprint
import sys

from lib import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-data', dest="DATA_FILE", default="data/lines/2.csv", help="Input csv file with preprocessed data")
parser.add_argument('-img', dest="IMAGE_FILE", default="img/2.png", help="Subway bullet image")
parser.add_argument('-instruments', dest="INSTRUMENTS_FILE", default="data/instruments.csv", help="Input csv file with instruments config")
parser.add_argument('-dir', dest="MEDIA_DIRECTORY", default="audio/", help="Input media directory")
parser.add_argument('-width', dest="WIDTH", default=1920, type=int, help="Output video width")
parser.add_argument('-height', dest="HEIGHT", default=1080, type=int, help="Output video height")
parser.add_argument('-pad0', dest="PAD_START", default=2000, type=int, help="Pad start in ms")
parser.add_argument('-pad1', dest="PAD_END", default=4000, type=int, help="Pad end in ms")
parser.add_argument('-fps', dest="FPS", default=60, type=int, help="Output video frames per second")
parser.add_argument('-outframe', dest="OUTPUT_FRAME", default="tmp/line_%s/frame.%s.png", help="Output frames pattern")
parser.add_argument('-aout', dest="AUDIO_OUTPUT_FILE", default="output/subway_line_%s.mp3", help="Output audio file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="output/subway_line_%s.mp4", help="Output media file")
parser.add_argument('-overwrite', dest="OVERWRITE", action="store_true", help="Overwrite existing files?")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just view statistics?")
parser.add_argument('-reverse', dest="REVERSE", action="store_true", help="Reverse the line?")

# Music config
parser.add_argument('-gain', dest="GAIN_DB", type=float, default=-4.0, help="Gain to apply to each clip in decibels")
parser.add_argument('-db', dest="MASTER_DB", type=float, default=0.0, help="Master +/- decibels to be applied to final audio")
parser.add_argument('-bpm', dest="BPM", type=int, default=120, help="Beats per minute, e.g. 60, 75, 100, 120, 150")
parser.add_argument('-mpb', dest="METERS_PER_BEAT", type=int, default=75, help="Higher numbers creates shorter songs")
parser.add_argument('-dpb', dest="DIVISIONS_PER_BEAT", type=int, default=4, help="e.g. 4 = quarter notes, 8 = eighth notes")
parser.add_argument('-pm', dest="PRICE_MULTIPLIER", type=float, default=1.14, help="Makes instruments more expensive; higher numbers = less instruments playing")
parser.add_argument('-vdur', dest="VARIANCE_MS", type=int, default=20, help="+/- milliseconds an instrument note should be off by to give it a little more 'natural' feel")

# Visual design config
parser.add_argument('-sw', dest="STATION_WIDTH", type=float, default=0.3125, help="Minumum station width as a percent of the screen width; adjust this to change the overall visual speed")
parser.add_argument('-tw', dest="TEXT_WIDTH", type=float, default=0.5, help="Station text width as a percent of the screen width")
parser.add_argument('-cy', dest="CENTER_Y", type=float, default=0.5, help="Center y as a percent of screen height")
parser.add_argument('-bty', dest="BOROUGH_TEXT_Y", type=float, default=0.375, help="Borough text center y as a percent of screen height")
parser.add_argument('-sty', dest="STATION_TEXT_Y", type=float, default=0.625, help="Station text center y as a percent of screen height")
parser.add_argument('-cw', dest="CIRCLE_WIDTH", type=int, default=90, help="Circle radius in pixels assuming 1920x1080")
parser.add_argument('-lh', dest="LINE_HEIGHT", type=int, default=28, help="Height of horizontal line in pixels assuming 1920x1080")
parser.add_argument('-bh', dest="BOUNDARY_HEIGHT", type=int, default=240, help="Height of horizontal line in pixels assuming 1920x1080")
parser.add_argument('-bw', dest="BOUNDARY_WIDTH", type=int, default=3, help="Height of horizontal line in pixels assuming 1920x1080")
parser.add_argument('-mw', dest="MARKER_WIDTH", type=int, default=8, help="Height of horizontal line in pixels assuming 1920x1080")
parser.add_argument('-sts', dest="STATION_TEXT_SIZE", type=int, default=60, help="Station text size in pixels assuming 1920x1080")
parser.add_argument('-bts', dest="BOROUGH_TEXT_SIZE", type=int, default=48, help="Borough text size in pixels assuming 1920x1080")
parser.add_argument('-bg', dest="BG_COLOR", default="#000000", help="Background color")
parser.add_argument('-tc', dest="TEXT_COLOR", default="#eeeeee", help="Text color")
parser.add_argument('-atc', dest="ALT_TEXT_COLOR", default="#aaaaaa", help="Secondary text color")
parser.add_argument('-mc', dest="MARKER_COLOR", default="#dddddd", help="Marker color")
parser.add_argument('-sfont', dest="STATION_FONT", default="fonts/OpenSans-Bold.ttf", help="Station font")
parser.add_argument('-bfont', dest="BOROUGH_FONT", default="fonts/OpenSans-SemiBold.ttf", help="Borough font")
a = parser.parse_args()

# Calculations
BEAT_MS = roundInt(60.0 / a.BPM * 1000)
ROUND_TO_NEAREST = roundInt(1.0 * BEAT_MS / a.DIVISIONS_PER_BEAT)

# Read data
_, stations = readCsv(a.DATA_FILE)
_, instruments = readCsv(a.INSTRUMENTS_FILE)

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

# Parse stations
stations = sorted(stations, key=lambda d: d["income"])
stations = addNormalizedValues(stations, "income", "nIncome")
stations = addIndices(stations, "incomeIndex")
stations = sorted(stations, key=lambda d: d["sortBy"], reverse=a.REVERSE)
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
    percent = ease(percent_complete)
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
    percent = ease(percent_complete)
    ms = lerp((from_beat_ms, to_beat_ms), percent)
    ms = roundInt(roundToNearest(ms, round_to))
    return ms

# Return if the instrument should be played in the given interval
def isValidInterval(instrument, elapsed_ms):
    interval_ms = instrument['interval_ms']
    interval = instrument['interval']
    interval_offset = instrument['interval_offset']
    return int(math.floor(1.0*elapsed_ms/interval_ms)) % interval == interval_offset

# Add beats to sequence
def addBeatsToSequence(sequence, instrument, duration, ms, beat_ms, round_to, pad_start):
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
        if isValidInterval(instrument, elapsed_ms):
            variance = roundInt(rn * a.VARIANCE_MS * 2 - a.VARIANCE_MS)
            sequence.append({
                'filename': instrument["file"],
                # 'gain': getGain(instrument, elapsed_beat) + a.GAIN_DB,
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
aa["BOUNDARY_HEIGHT"] = roundInt(a.BOUNDARY_HEIGHT * RESOLUTION)
aa["BOUNDARY_WIDTH"] = roundInt(a.BOUNDARY_WIDTH * RESOLUTION)
aa["MARKER_WIDTH"] = roundInt(a.MARKER_WIDTH * RESOLUTION)
aa["STATION_TEXT_SIZE"] = roundInt(a.STATION_TEXT_SIZE * RESOLUTION)
aa["BOROUGH_TEXT_SIZE"] = roundInt(a.BOROUGH_TEXT_SIZE * RESOLUTION)

x = 0
for i, station in enumerate(stations):
    boroughNext = station["Borough"]
    if i < stationCount-1:
        boroughNext = stations[i+1]["Borough"]
    stations[i]["BoroughNext"] = boroughNext
    stations[i]["width"] = roundInt(1.0 * station["duration"] / minDuration * a.STATION_WIDTH)
    stations[i]["x"] = x
    stations[i]["x0"] = x - a.TEXT_WIDTH / 2
    stations[i]["x1"] = x + a.TEXT_WIDTH / 2
    x += stations[i]["width"]
totalW = x
pxPerMs = 1.0 * totalW / totalMs
pxPerS = pxPerMs * 1000.0
pxPerFrame = pxPerS / a.FPS
print("Total width: %s px" % totalW)
print("Pixels per second: %s" % pxPerS)
print("Pixels per frame: %s" % pxPerFrame)

totalFrames = msToFrame(sequenceDuration, a.FPS)
totalFrames = int(ceilToNearest(totalFrames, a.FPS))
sequenceDuration = frameToMs(totalFrames, a.FPS)
basename = getBasename(a.DATA_FILE)

def drawFrame(filename, xOffset, stations, totalW, bulletImg, a):
    if not a.OVERWRITE and os.path.isfile(filename):
        return

    im = Image.new('RGB', (a.WIDTH, a.HEIGHT), a.BG_COLOR)
    draw = ImageDraw.Draw(im, 'RGBA')
    cx = roundInt(a.WIDTH * 0.5)
    cy = roundInt(a.HEIGHT * 0.5)

    leftX = xOffset
    rightX = leftX + totalW

    # draw the center line
    x0 = 0 if leftX < 0 else leftX
    x1 = a.WIDTH if rightX > a.WIDTH else rightX
    y0 = cy - a.LINE_HEIGHT/2
    y1 = y0 + a.LINE_HEIGHT
    draw.rectangle([(x0, y0), (x1, y1)], fill=a.ALT_TEXT_COLOR)

    for i, s in enumerate(stations):
        # check if station is visible
        sx0 = xOffset + s["x0"]
        sx1 = xOffset + s["x1"]
        if not (0 <= sx0 <= a.WIDTH or 0 <= sx1 <= a.WIDTH):
            continue

        sx = xOffset + s["x"]
        sy = a.CENTER_Y

        # draw borough text

        # draw bullet
        bx = roundInt(sx - a.CIRCLE_WIDTH/2)
        by = roundInt(sy - a.CIRCLE_WIDTH/2)
        im.paste(bulletImg, (bx, by), bulletImg)

        # draw station text

    # draw the marker
    x0 = cx - a.MARKER_WIDTH/2
    x1 = x0 + a.MARKER_WIDTH
    y0 = 0
    y1 = a.HEIGHT
    draw.rectangle([(x0, y0), (x1, y1)], fill=(255,255,255,100))

    del draw
    im.save(filename)
    print("Saved %s" % filename)

bulletImg = Image.open(a.IMAGE_FILE)
bulletImg = bulletImg.resize((a.CIRCLE_WIDTH, a.CIRCLE_WIDTH), resample=Image.LANCZOS)

audioFilename = a.AUDIO_OUTPUT_FILE % basename
print("%s steps in sequence" % len(sequence))
print('Total sequence time: %s' % formatSeconds(sequenceDuration/1000.0))

if a.PROBE:
    sys.exit()

makeDirectories([a.OUTPUT_FRAME % (basename, "*")])

if a.OVERWRITE:
    removeFiles(a.OUTPUT_FRAME % (basename, "*"))

print("Making video frame sequence...")
videoFrames = []
xOffset = roundInt(a.WIDTH * 0.5)
for f in range(totalFrames):
    frame = f + 1
    ms = frameToMs(frame, a.FPS)
    frameFilename = a.OUTPUT_FRAME % (basename, zeroPad(frame, totalFrames))
    drawFrame(frameFilename, xOffset, stations, totalW, bulletImg, a)

    if a.PAD_START <= ms < a.PAD_END:
        xOffset -= pxPerFrame

    break

if a.OVERWRITE or not os.path.isfile(audioFilename):
    mixAudio(sequence, sequenceDuration, audioFilename, masterDb=a.MASTER_DB)
else:
    print("%s already exists" % audioFilename)
