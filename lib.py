import csv
import math
import numpy as np
import os
from pprint import pprint
import random
import sys
import time

def addIndices(arr, keyName="index", startIndex=0):
    for i, item in enumerate(arr):
        arr[i][keyName] = startIndex + i
    return arr

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

def roundInt(val):
    return int(round(val))

def roundToNearest(n, nearest):
    return 1.0 * round(1.0*n/nearest) * nearest

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
