# -*- coding: utf-8 -*-

import argparse
import json
import os
import numpy as np
from pprint import pprint
from shapely.geometry import Polygon
import sys

from lib import *

# input
parser = argparse.ArgumentParser()
parser.add_argument('-census', dest="CENSUS_FILE", default="data/ACS_2017_5YR_B19013_with_ann.csv", help="Input csv file with census data")
parser.add_argument('-stations', dest="STATIONS_FILE", default="data/MTA_Subway_Locations.csv", help="Input csv file with stations data")
parser.add_argument('-routes', dest="ROUTES_FILE", default="data/MTA_Subway_Routes.csv", help="Input csv file with routes data")
parser.add_argument('-tract', dest="TRACT_FILE", default="data/2010_Census_Tracts.geojson", help="Input GeoJSON file with census tract data")
parser.add_argument('-colors', dest="COLORS_FILE", default="data/MTA_Colors.csv", help="Input csv file with stations color data")
parser.add_argument('-out', dest="OUTPUT_FILE", default="data/lines/%s.csv", help="Output csv file pattern")
a = parser.parse_args()

INCOME_KEY = "HD01_VD01"

print("Reading geojson...")
tractFeatures = []
with open(a.TRACT_FILE) as f:
    geojson = json.load(f)
    tractFeatures = geojson["features"]
    print("Read %s tract features" % len(tractFeatures))

if len(tractFeatures) < 1:
    print("No tract features found.")
    sys.exit()

print("Calculating census tract lat/lon centroids...")
tracts = []
tractCount = len(tractFeatures)
for i, feat in enumerate(tractFeatures):
    props = feat["properties"].copy()
    coords = feat["geometry"]["coordinates"][0][0]
    poly = Polygon(coords)
    lonlat = poly.representative_point().coords[:][0]
    props["lonlat"] = lonlat
    tracts.append(props)
    printProgress(i+1, tractCount)
tractCoords = np.asarray([t["lonlat"] for t in tracts])

def matchCensusTract(cdataLookup, tract):
    boroughCodes = {
        "1": "36061", # Manhattan
        "2": "36005", # Bronx
        "3": "36047", # Brooklyn (King's County)
        "4": "36081", # Queens
        "5": "36085", # Staten Island (Richmond Count)
    }
    if ""+tract["boro_code"] not in boroughCodes:
        print("Error: Could not find %s in borough codes. Exiting" % tract["boro_code"])
        pprint(tract)
        return False
    bcode = boroughCodes[""+tract["boro_code"]]
    tractId = bcode + tract["ct2010"]
    if tractId not in cdataLookup:
        print("Warning: Could not find %s in census data. Skipping..." % tractId)
        return False
    ctract = cdataLookup[tractId]
    if not isNumber(ctract[INCOME_KEY]):
        print("Warning: Tract %s is not a number (%s). Skipping..." % (tractId, ctract[INCOME_KEY]))
        return False
    return ctract

print("Matching subway station lat/lon to closest census tract centroids...")
stationFields, stations = readCsv(a.STATIONS_FILE)
censusFields, cdata = readCsv(a.CENSUS_FILE)
# cdata = [d for d in cdata if isNumber(d[INCOME_KEY])]
cdataLookup = createLookup(cdata, "GEO.id2")
stationCount = len(stations)
for i, station in enumerate(stations):
    lon = station["GTFS Longitude"]
    lat = station["GTFS Latitude"]
    coord = np.asarray([lon, lat])

    # Retrieve the two closest tracts and their distances to station
    distances, sortedIndices = getSortedIndicesByDistance(coord, tractCoords)
    matches = []
    j = 0
    while len(matches) < 2 and j < len(sortedIndices):
        findex = sortedIndices[j]
        ftract = tracts[findex]
        fdist = distances[findex]
        match = matchCensusTract(cdataLookup, ftract)
        if match is not False:
            matches.append((match, fdist))
        j += 1

    if len(matches) < 2:
        print("Could not match %s (%s)" % (station["Stop Name"], station["Daytime Routes"]))
        sys.exit()

    # Calculate weighted mean based on distance to both tracts
    cdata0 = matches[0]
    cdata1 = matches[1]
    c0, d0 = cdata0
    c1, d1 = cdata1
    income0 = c0[INCOME_KEY]
    income1 = c1[INCOME_KEY]
    dtotal = d0 + d1
    weight0 = 1.0*(dtotal-d0)/dtotal
    weight1 = 1.0*(dtotal-d1)/dtotal
    income = weightedMean([income0, income1], [weight0, weight1])

    # print("%s (%s)" % (station["Stop Name"], station["Daytime Routes"]))
    # print("Tract %s (%s) = %s = $%s" % (c0["GEO.display-label"], c0["GEO.id2"], d0, income0))
    # print("Tract %s (%s) = %s = $%s" % (c1["GEO.display-label"], c1["GEO.id2"], d1, income1))
    # print("Weighted mean: %s" % income)
    # break

    stations[i]["tractId1"] = c0["GEO.id2"]
    stations[i]["tractWeight1"] = round(weight0, 3)
    stations[i]["tractId2"] = c1["GEO.id2"]
    stations[i]["tractWeight2"] = round(weight1, 3)
    stations[i]["income"] = int(round(income))
    printProgress(i+1, stationCount)

print("Retrieving colors...")
colorFields, colorData = readCsv(a.COLORS_FILE, doParseNumbers=False)
colorData = [d for d in colorData if d["MTA Mode"]=="NYCT Subway"]
colorLookup = {
    "SIR": "0F2B51"
}
for d in colorData:
    lines = d["Line/Branch"]
    if "/" in lines:
        lines = lines.split("/")
    else:
        lines = lines.split(" ")
    for line in lines:
        colorLookup[line] = d["RGB Hex"]

print("Splitting stations up into lines/routes...")
lineKeys = []
for i, station in enumerate(stations):
    lines = [r for r in str(station["Daytime Routes"]).split(" ")]
    stations[i]["id"] = str(station["Station ID"])
    stations[i]["lines"] = lines
    lineKeys += lines
lineKeys = list(set(lineKeys))

# read route data
routeFields, routeData = readCsv(a.ROUTES_FILE, doParseNumbers=False)
for i, route in enumerate(routeData):
    routeData[i]["groups"] = route["Group"].split(" ") if len(route["Group"]) > 0 else []

# get list of unique groups
groups = [r["groups"] for r in routeData]
groups = [item for sublist in groups for item in sublist]
groups = list(set(groups))
print ("Found %s groups" % len(groups))
pprint(groups)

outputHeadings = ["sortBy", "Station ID", "Line", "Stop Name", "Borough", "Daytime Routes", "GTFS Latitude", "GTFS Longitude", "color", "tractId1", "tractWeight1", "tractId2", "tractWeight2", "income"]
lines = []
for line in lineKeys:
    # order the stations via route config
    routeOrder = [s for s in routeData if s["Route"]==line]
    stationLookup = createLookup(routeOrder, "Station ID")

    lineStations = [s for s in stations if line in s["lines"]]
    lgroups = []
    for i, s in enumerate(lineStations):
        rs = stationLookup[s["id"]]
        lineStations[i]["sortBy"] = int(rs["Sort By"])
        lineStations[i]["color"] = colorLookup[line]
        if len(rs["groups"]) > 0:
            lineStations[i]["groups"] = rs["groups"]
            lgroups += rs["groups"]
    lineStations = sorted(lineStations, key=lambda k: k['sortBy'])

    lgroups = list(set(lgroups))
    if len(lgroups) < 1:
        lgroups = ['']

    for lgroup in lgroups:
        basefilename = line
        rows = lineStations[:]
        if len(lgroup) > 0:
            basefilename += "_" + lgroup
            rows = [s for s in lineStations if lgroup in s["groups"]]
        filename = a.OUTPUT_FILE % basefilename
        writeCsv(filename, rows, outputHeadings)

print("Done.")
