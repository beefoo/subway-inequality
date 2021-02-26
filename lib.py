import csv
import glob
import math
import numpy as np
import os
from pprint import pprint
from pydub import AudioSegment
import random
import subprocess
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

def compileFrames(infile, fps, outfile, padZeros, audioFile=None, quality="high"):
    print("Compiling frames...")
    padStr = '%0'+str(padZeros)+'d'

    # https://trac.ffmpeg.org/wiki/Encode/H.264
    # presets: veryfast, faster, fast, medium, slow, slower, veryslow
    #   slower = better quality
    # crf: 0 is lossless, 23 is the default, and 51 is worst possible quality
    #   17 or 18 to be visually lossless or nearly so
    preset = "veryslow"
    crf = "18"
    if quality=="medium":
        preset = "medium"
        crf = "23"
    elif quality=="low":
        preset = "medium"
        crf = "28"

    if audioFile:
        command = ['ffmpeg','-y',
                    '-framerate',str(fps)+'/1',
                    '-i',infile % padStr,
                    '-i',audioFile,
                    '-c:v','libx264',
                    '-preset', preset,
                    '-crf', crf,
                    '-r',str(fps),
                    '-pix_fmt','yuv420p',
                    '-c:a','aac',
                    # '-q:v','1',
                    '-b:a', '192k',
                    # '-shortest',
                    outfile]
    else:
        command = ['ffmpeg','-y',
                    '-framerate',str(fps)+'/1',
                    '-i',infile % padStr,
                    '-c:v','libx264',
                    '-preset', preset,
                    '-crf', crf,
                    '-r',str(fps),
                    '-pix_fmt','yuv420p',
                    # '-q:v','1',
                    outfile]
    print(" ".join(command))
    finished = subprocess.check_call(command)
    print("Done.")

def createLookup(arr, key):
    return dict([(str(item[key]), item) for item in arr])

def drawTextLinesToImage(draw, lines, font, lineMargin, letterMargin, cx, cy, color):
    y = cy
    for text in reversed(lines):
        lw, lh = drawTextToImage(draw, text, font, letterMargin, cx, y, color)
        y -= (lh + lineMargin)

def drawTextToImage(draw, text, font, letterMargin, cx, cy, color):
    lw, lh = getLineSize(font, text, letterMargin)
    x0 = cx - lw/2
    y = cy - lh/2
    chars = list(text)
    x = x0
    for char in chars:
        draw.text((x, y), char, font=font, fill=color)
        cw, ch = font.getsize(char)
        x += cw + letterMargin
    return (lw, lh)

def earthDistance(lat1, lng1, lat2, lng2):
    earthRadius = 6371000.0 # meters
    dLat = 1.0 * math.radians(lat2-lat1)
    dLng = 1.0 * math.radians(lng2-lng1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLng/2) * math.sin(dLng/2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0-a))
    dist = earthRadius * c
    return dist

def easeIn(n, exp=3):
    return n ** exp

def easeInOut(n):
    # return (math.sin((n+1.5)*math.pi)+1.0) / 2.0
    return 4.0 * (n ** 3) if n < 0.5 else (n-1.0)*(2*n-2)*(2*n-2)+1

def easeSin(value):
    eased = math.sin(value * math.pi)
    # eased = (math.sin((value+1.5)*math.pi)+1.0) / 2.0
    eased = lim(eased)
    return eased

def findInList(list, key, value):
    found = -1
    for index, item in enumerate(list):
        if item[key] == value:
            found = index
            break
    return found

def formatNumber(value):
    return f'{value:,}'

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

def getFileExt(fn):
    basename = os.path.basename(fn)
    return "." + basename.split(".")[-1]

def getLineSize(font, text, letterMargin=0):
    aw, ah = font.getsize("A")
    lw, lh = font.getsize(text)
    lh = ah # standardize line height
    clen = len(text)
    if clen > 1:
        lw += letterMargin * (clen-1)
    return (lw, lh)

def getMultilines(text, font, maxWidth, letterMargin):
    mlines = [text]
    lw, lh = getLineSize(font, text, letterMargin)

    # for line items, wrap into multiline
    if lw > maxWidth:
        mlines = []
        words = text.split()
        currentLineText = ""
        wordCount = len(words)
        for i, word in enumerate(words):
            # Automatically break if we reach a hyphen
            if word == "-" and len(currentLineText) > 0:
                mlines.append(currentLineText)
                currentLineText = ""
                continue
            testString = word if len(currentLineText) < 1 else currentLineText + " " + word
            testW, _ = getLineSize(font, testString, letterMargin)
            # test string too long, must add previous line and move on to next line
            if testW > maxWidth:
                if len(currentLineText) > 0:
                    addText = currentLineText
                    currentLineText = word
                # Word is too long... just add it
                else:
                    addText = word
                mlines.append(addText)
            # otherwise add to current line
            else:
                currentLineText = testString
            # leftover text at the end; just add it
            if i >= wordCount-1 and len(currentLineText) > 0:
                mlines.append(currentLineText)

    return mlines

# https://codereview.stackexchange.com/questions/28207/finding-the-closest-point-to-a-list-of-points
def getSortedIndicesByDistance(node, nodes):
    deltas = nodes - node
    dist_2 = np.einsum('ij,ij->i', deltas, deltas)
    return (dist_2, np.argsort(dist_2))

def hexToRGB(hex, toFloat=False):
    hex = hex.lstrip('#')
    rgb = [int(hex[i:i+2], 16) for i in [0, 2, 4]]
    if toFloat:
        rgb = [1.0*c/255.0 for c in rgb]
    return tuple(rgb)

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

def logTime(startTime=None, label="Elapsed time"):
    if startTime is False:
        return False
    now = time.time()
    if startTime is not None:
        secondsElapsed = now - startTime
        timeStr = formatSeconds(secondsElapsed)
        print("%s: %s" % (label, timeStr))
    return now

def makeDirectories(filenames):
    if not isinstance(filenames, list):
        filenames = [filenames]
    for filename in filenames:
        dirname = os.path.dirname(filename)
        if len(dirname) > 0 and not os.path.exists(dirname):
            os.makedirs(dirname)

def makeTrack(duration, instructions, audio, audioDurationMs, sampleWidth=4, sampleRate=48000, channels=2, maxChunkDuration=300000, isChunk=False):
    if not isChunk and duration > maxChunkDuration:
        return makeTrackChunks(duration, instructions, audio, audioDurationMs, sampleWidth, sampleRate, channels, chunkDuration=maxChunkDuration)

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

def makeTrackChunks(duration, instructions, audio, audioDurationMs, sampleWidth=4, sampleRate=48000, channels=2, chunkDuration=300000):
    # build audio
    baseAudio = AudioSegment.silent(duration=duration, frame_rate=sampleRate)
    baseAudio = baseAudio.set_channels(channels)
    baseAudio = baseAudio.set_sample_width(sampleWidth)

    msStart = 0
    instructions = sorted(instructions, key=lambda i: i["ms"])
    while msStart < duration:
        msEnd = msStart + chunkDuration
        if msEnd > duration:
            msEnd = duration
        chunkInstructions = [i for i in instructions if msStart <= i["ms"] < msEnd]
        for index, i in enumerate(chunkInstructions):
            chunkInstructions[index]["ms"] = i["ms"] - msStart
        if len(chunkInstructions) > 0:
            chunkDuration = msEnd - msStart + audioDurationMs
            print(" Making new track chunk at %s" % formatSeconds(msStart/1000.0))
            chunkedTrack = makeTrack(chunkDuration, chunkInstructions, audio, audioDurationMs, sampleWidth, sampleRate, channels, isChunk=True)
            baseAudio = baseAudio.overlay(chunkedTrack, position=msStart)
        msStart = msEnd

    return baseAudio

def mixAudio(instructions, duration, outfilename, sampleWidth=4, sampleRate=48000, channels=2, masterDb=0.0, fadeOut=1000):
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
        trackAudio = makeTrack(duration, trackInstructions, audio, audioDurationMs, sampleWidth=sampleWidth, sampleRate=sampleRate, channels=channels)
        baseAudio = baseAudio.overlay(trackAudio)
        print("Track %s of %s complete." % (i+1, trackCount))

    print("Writing to file...")
    format = outfilename.split(".")[-1]
    # adjust master volume
    if masterDb != 0.0:
        baseAudio = baseAudio.apply_gain(masterDb)
    # fade out end
    baseAudio = baseAudio.fade_out(fadeOut)
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

def readTextFile(filename):
    contents = ""
    if os.path.isfile(filename):
        with open(filename, "r", encoding="utf8", errors="replace") as f:
            contents = f.read()
    return contents

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

def replaceFileExtension(fn, newExt):
    extLen = len(getFileExt(fn))
    i = len(fn) - extLen
    return fn[:i] + newExt

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

def writeTextFile(filename, text):
    with open(filename, "w", encoding="utf8", errors="replace") as f:
        f.write(text)

def zeroPad(value, total):
    padding = len(str(total))
    return str(value).zfill(padding)
