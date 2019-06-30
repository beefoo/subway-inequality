# -*- coding: utf-8 -*-

import argparse
import os
from pprint import pprint
import sys

from lib import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-data', dest="DATA_FILE", default="data/lines/2.csv", help="Input csv file with preprocessed data")
parser.add_argument('-instruments', dest="INSTRUMENTS_FILE", default="data/instruments.csv", help="Input csv file with instruments config")
parser.add_argument('-dir', dest="MEDIA_DIRECTORY", default="audio/", help="Input media directory")
parser.add_argument('-width', dest="WIDTH", default=1920, type=int, help="Output video width")
parser.add_argument('-height', dest="HEIGHT", default=1080, type=int, help="Output video height")
parser.add_argument('-fps', dest="FPS", default=60, type=int, help="Output video frames per second")
parser.add_argument('-outframe', dest="OUTPUT_FRAME", default="tmp/line_%s/frame.%s.png", help="Output frames pattern")
parser.add_argument('-out', dest="OUTPUT_FILE", default="output/subway_line_%s.mp4", help="Output media file")
parser.add_argument('-probe', dest="PROBE", action="store_true", help="Just view statistics?")
parser.add_argument('-reverse', dest="REVERSE", action="store_true", help="Reverse the line?")

# Music config
parser.add_argument('-db', dest="MASTER_DB", type=float, default=0.0, help="Master +/- decibels to be applied to final audio")
parser.add_argument('-bpm', dest="BPM", type=int, default=120, help="Beats per minute, e.g. 60, 75, 100, 120, 150")
parser.add_argument('-mpb', dest="METERS_PER_BEAT", type=int, default=75, help="Higher numbers creates shorter songs")
parser.add_argument('-dpb', dest="DIVISIONS_PER_BEAT", type=int, default=4, help="e.g. 4 = quarter notes, 8 = eighth notes")
parser.add_argument('-pm', dest="PRICE_MULTIPLIER", type=float, default=1.14, help="Makes instruments more expensive; higher numbers = less instruments playing")
parser.add_argument('-vdur', dest="VARIANCE_MS", type=int, default=20, help="+/- milliseconds an instrument note should be off by to give it a little more 'natural' feel")

# Visual design config

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
stations = addIndices(stations, "incomeIndex")
stations = sorted(stations, key=lambda d: d["sortBy"], reverse=a.REVERSE)
stations = addIndices(stations, "index")
stationCount = len(stations)
for i, station in enumerate(stations):
    stations[i]["percentile"] = 1.0 * station["incomeIndex"] / stationCount * 100
    stations[i]["instruments"] = buyInstruments(stations[i], instruments)
    # print(len(stations[i]["instruments"]))
    distance = beats = duration = 0
    boroughNext = station["Borough"]
    if i < stationCount-1:
        distance = earthDistance(stations[i+1]['GTFS Latitude'], stations[i+1]['GTFS Longitude'], station['GTFS Latitude'], station['GTFS Longitude'])
        beats = roundInt(1.0 * distance / a.METERS_PER_BEAT)
        duration = beats * BEAT_MS
        boroughNext = stations[i+1]["Borough"]
    stations[i]["distance"] = distance
    stations[i]["beats"] = beats
    stations[i]["duration"] = duration
    stations[i]["BoroughNext"] = boroughNext

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
print('Main sequence time: %s' % formatSeconds(totalSeconds))

# Retrieve gain based on current beat
def getGain(instrument, beat):
    beats_per_phase = instrument['gain_phase']
    percent_complete = float(beat % beats_per_phase) / beats_per_phase
    multiplier = ease(percent_complete)
    from_gain = instrument['from_gain']
    to_gain = instrument['to_gain']
    min_gain = min(from_gain, to_gain)
    gain = multiplier * (to_gain - from_gain) + from_gain
    gain = max(min_gain, round(gain, 2))
    return gain

# Get beat duration in ms based on current point in time
def getBeatMs(instrument, beat, round_to):
    from_beat_ms = instrument['from_beat_ms']
    to_beat_ms = instrument['to_beat_ms']
    beats_per_phase = instrument['tempo_phase']
    percent_complete = float(beat % beats_per_phase) / beats_per_phase
    multiplier = ease(percent_complete)
    ms = multiplier * (to_beat_ms - from_beat_ms) + from_beat_ms
    ms = roundInt(roundToNearest(ms, round_to))
    return ms

# Return if the instrument should be played in the given interval
def isValidInterval(instrument, elapsed_ms):
    interval_ms = instrument['interval_ms']
    interval = instrument['interval']
    interval_offset = instrument['interval_offset']
    return int(math.floor(1.0*elapsed_ms/interval_ms)) % interval == interval_offset

# Add beats to sequence
def addBeatsToSequence(sequence, instrument, duration, ms, beat_ms, round_to):
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
                'gain': getGain(instrument, elapsed_beat),
                'ms': max([elapsed_ms + variance, 0])
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
            sequence = addBeatsToSequence(sequence, instrument, stationQueueDur, ms, BEAT_MS, ROUND_TO_NEAREST)
            ms += stationQueueDur + station['duration']
            stationQueueDur = 0
        elif instrumentIndex < 0:
            ms += station['duration']
        else:
            stationQueueDur += station['duration']
    if stationQueueDur > 0:
        sequence = addBeatsToSequence(sequence, instrument, stationQueueDur, ms, BEAT_MS, ROUND_TO_NEAREST)

print("%s steps in sequence" % len(sequence))
