import csv
import numpy as np
import os
from pprint import pprint
import sys

def createLookup(arr, key):
    return dict([(str(item[key]), item) for item in arr])

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

def printProgress(step, total):
    sys.stdout.write('\r')
    sys.stdout.write("%s%%" % round(1.0*step/total*100,2))
    sys.stdout.flush()

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
