import csv
import glob
import math
import numpy as np
import os
from pprint import pprint
from pydub import AudioSegment
import random
import sys
import time

def addIndices(arr, keyName="index", startIndex=0):
    for i, item in enumerate(arr):
        arr[i][keyName] = startIndex + i
    return arr

def addNormalizedValues(arr, key, nkey):
    values = [v[key] for v in arr]
    range = (min(values), max(values))
    for i, entry in enumerate(arr):
        arr[i][nkey] = norm(entry[key], range)
    return arr

def ceilInt(n):
    return int(math.ceil(n))

def ceilToNearest(n, nearest):
    return 1.0 * math.ceil(1.0*n/nearest) * nearest

def createLookup(arr, key):
    return dict([(str(item[key]), item) for item in arr])

def earthDistance(lat1, lng1, lat2, lng2):
    earthRadius = 6371000.0 # meters
    dLat = 1.0 * math.radians(lat2-lat1)
    dLng = 1.0 * math.radians(lng2-lng1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLng/2) * math.sin(dLng/2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0-a))
    dist = earthRadius * c
    return dist

def ease(value):
    eased = math.sin(value * math.pi)
    eased = lim(eased)
    return eased

def findInList(list, key, value):
    found = -1
    for index, item in enumerate(list):
        if item[key] == value:
            found = index
            break
    return found

def formatSeconds(s):
    tString = time.strftime('%H:%M:%S', time.gmtime(s))
    if tString.startswith("00:"):
        tString = tString[3:]
    return tString

def frameToMs(frame, fps, roundResult=True):
    result = (1.0 * frame / fps) * 1000.0
    if roundResult:
        result = roundInt(result)
    return result

# Note: sample_width -> bit_depth conversions: 1->8, 2->16, 3->24, 4->32
# 24/32 bit depth and 48K sample rates are industry standards
def getAudio(filename, sampleWidth=4, sampleRate=48000, channels=2):
    # A hack: always read files at 16-bit depth because Sox does not support more than that
    fformat = filename.split(".")[-1].lower()
    audio = AudioSegment.from_file(filename, format=fformat)
    # convert to stereo
    if audio.channels != channels:
        print("Warning: channels changed to %s from %s in %s" % (channels, audio.channels, filename))
        audio = audio.set_channels(channels)
    # convert sample width
    if audio.sample_width != sampleWidth:
        print("Warning: sample width changed to %s from %s in %s" % (sampleWidth, audio.sample_width, filename))
        audio = audio.set_sample_width(sampleWidth)
    # convert sample rate
    if audio.frame_rate != sampleRate:
        print("Warning: frame rate changed to %s from %s in %s" % (sampleRate, audio.frame_rate, filename))
        audio = audio.set_frame_rate(sampleRate)
    return audio

def getBasename(fn):
    return os.path.splitext(os.path.basename(fn))[0]

# https://codereview.stackexchange.com/questions/28207/finding-the-closest-point-to-a-list-of-points
def getSortedIndicesByDistance(node, nodes):
    deltas = nodes - node
    dist_2 = np.einsum('ij,ij->i', deltas, deltas)
    return (dist_2, np.argsort(dist_2))

def isNumber(value):
    try:
        num = float(value)
        return True
    except ValueError:
        return False

def lerp(ab, amount):
    a, b = ab
    return (b-a) * amount + a

def lim(value, ab=(0, 1)):
    a, b = ab
    return max(a, min(b, value))

def makeDirectories(filenames):
    if not isinstance(filenames, list):
        filenames = [filenames]
    for filename in filenames:
        dirname = os.path.dirname(filename)
        if len(dirname) > 0 and not os.path.exists(dirname):
            os.makedirs(dirname)

def makeTrack(duration, instructions, audio, sampleWidth=4, sampleRate=48000, channels=2):
    # build audio
    baseAudio = AudioSegment.silent(duration=duration, frame_rate=sampleRate)
    baseAudio = baseAudio.set_channels(channels)
    baseAudio = baseAudio.set_sample_width(sampleWidth)
    instructionCount = len(instructions)

    # convert sample width
    if audio.sample_width != sampleWidth:
        # print("Warning: sample width changed to %s from %s" % (sampleWidth, audio.sample_width))
        audio = audio.set_sample_width(sampleWidth)
    # add slight fade to avoid clicking
    audio = audio.fade_in(10).fade_out(10)

    for index, i in enumerate(instructions):
        stepAudio = audio.apply_gain(i["gain"])
        baseAudio = baseAudio.overlay(stepAudio, position=i["ms"])
        printProgress(index+1, instructionCount)
    return baseAudio

def mixAudio(instructions, duration, outfilename, sampleWidth=4, sampleRate=48000, channels=2, masterDb=0.0):
    # remove instructions with no volume
    instructions = [i for i in instructions if "volume" not in i or i["volume"] > 0]
    audioFiles = list(set([i["filename"] for i in instructions]))
    audioFiles = [{"filename": f} for f in audioFiles]
    instructionCount = len(instructions)
    trackCount = len(audioFiles)

    # calculate db
    for i, step in enumerate(instructions):
        if "volume" in step:
            instructions[i]["gain"] = volumeToDb(step["volume"])

    # create base audio
    baseAudio = AudioSegment.silent(duration=duration, frame_rate=sampleRate)
    baseAudio = baseAudio.set_channels(channels)
    baseAudio = baseAudio.set_sample_width(sampleWidth)

    # Load sounds
    print("Adding tracks...")
    for i, af in enumerate(audioFiles):
        filename = af["filename"]
        audioFiles[i]["index"] = i

        # load audio file
        audio = getAudio(filename, sampleWidth, sampleRate, channels)
        audioDurationMs = len(audio)

        # make the track
        trackInstructions = [ii for ii in instructions if ii["filename"]==af["filename"]]
        print("Making track %s of %s with %s instructions..." % (i+1, trackCount, len(trackInstructions)))
        trackAudio = makeTrack(duration, trackInstructions, audio, sampleWidth=sampleWidth, sampleRate=sampleRate, channels=channels)
        baseAudio = baseAudio.overlay(trackAudio)
        print("Track %s of %s complete." % (i+1, trackCount))

    print("Writing to file...")
    format = outfilename.split(".")[-1]
    # adjust master volume
    if masterDb != 0.0:
        baseAudio = baseAudio.apply_gain(masterDb)
    f = baseAudio.export(outfilename, format=format)
    print("Wrote to %s" % outfilename)

def msToFrame(ms, fps):
    return roundInt((ms / 1000.0) * fps)

def norm(value, ab, limit=False):
    a, b = ab
    n = 0.0
    if (b - a) != 0:
        n = 1.0 * (value - a) / (b - a)
    if limit:
        n = lim(n)
    return n

def parseNumber(string, alwaysFloat=False):
    try:
        string = string.strip(" +").replace(",", "")
        num = float(string)
        if "." not in str(string) and "e" not in str(string) and not alwaysFloat:
            num = int(string)
        return num
    except ValueError:
        return string

def parseNumbers(arr):
    for i, item in enumerate(arr):
        if isinstance(item, (list,)):
            for j, v in enumerate(item):
                arr[i][j] = parseNumber(v)
        else:
            for key in item:
                arr[i][key] = parseNumber(item[key])
    return arr

def prependAll(arr, prepends):
    if isinstance(prepends, tuple):
        prepends = [prepends]

    for i, item in enumerate(arr):
        for p in prepends:
            newKey = None
            if len(p) == 3:
                key, value, newKey = p
            else:
                key, value = p
                newKey = key
            arr[i][newKey] = value + item[key]

    return arr

def printProgress(step, total):
    sys.stdout.write('\r')
    sys.stdout.write("%s%%" % round(1.0*step/total*100,2))
    sys.stdout.flush()

def pseudoRandom(seed, range=(0, 1), isInt=False):
    random.seed(seed)
    value = random.random()
    value = lerp(range, value)
    if isInt:
        value = roundInt(value)
    return value

def readCsv(filename, doParseNumbers=True, skipLines=0, encoding="utf8", readDict=True, verbose=True, delimiter=","):
    rows = []
    fieldnames = []
    if os.path.isfile(filename):
        lines = []
        with open(filename, 'r', encoding="utf8") as f:
            lines = list(f)
        if skipLines > 0:
            lines = lines[skipLines:]
        lines = [line for line in lines if not line.startswith("#")]
        if readDict:
            reader = csv.DictReader(lines, skipinitialspace=True, delimiter=delimiter)
            fieldnames = list(reader.fieldnames)
        else:
            reader = csv.reader(lines, skipinitialspace=True)
        rows = list(reader)
        if doParseNumbers:
            rows = parseNumbers(rows)
        if verbose:
            print("Read %s rows from %s" % (len(rows), filename))
    return (fieldnames, rows)

def removeFiles(listOrString):
    filenames = listOrString
    if not isinstance(listOrString, list) and "*" in listOrString:
        filenames = glob.glob(listOrString)
    elif not isinstance(listOrString, list):
        filenames = [listOrString]
    print("Removing %s files" % len(filenames))
    for fn in filenames:
        if os.path.isfile(fn):
            os.remove(fn)

def roundInt(val):
    return int(round(val))

def roundToNearest(n, nearest):
    return 1.0 * round(1.0*n/nearest) * nearest

def volumeToDb(volume):
    db = 0.0
    if 0.0 < volume < 1.0 or volume > 1.0:
        db = 10.0 * math.log(volume**2)
    return db

def weightedMean(values, weights):
    return np.average(values, weights=weights)

def writeCsv(filename, arr, headings):
    with open(filename, 'w', encoding="utf8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headings)
        for i, d in enumerate(arr):
            row = []
            for h in headings:
                value = d[h] if h in d else ""
                row.append(value)
            writer.writerow(row)
    print("Wrote %s rows to %s" % (len(arr), filename))

def zeroPad(value, total):
    padding = len(str(total))
    return str(value).zfill(padding)
