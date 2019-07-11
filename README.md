# Sonification of Income Inequality on the NYC Subway

## Data sources

- [MTA subway station data](http://web.mta.info/developers/data/nyct/subway/Stations.csv) via [MTA developers page](http://web.mta.info/developers/developer-data-terms.html#data)
- [MTA subway line colors](http://web.mta.info/developers/resources/line_colors.htm)
- [2010 New York City Census Tracts](https://data.cityofnewyork.us/City-Government/2010-Census-Tracts/fxpq-c8ku)
- [Median household income by census tract, 2017 ACS 5-year estimates (B19013)](https://factfinder.census.gov/). Obtained using the following options:
   - Geographies > Geographic type > Census Tract - 140
   - New York -> All Census Tracts within New York
   - Topics > Income/Earnings (Households)
   - ID: B19013 / MEDIAN HOUSEHOLD INCOME IN THE PAST 12 MONTHS (IN 2017 INFLATION-ADJUSTED DOLLARS) / 2017 ACS 5-year estimates

I generated [a simple visualization](https://github.com/beefoo/subway-inequality/blob/master/data/2010_Census_Tracts_Income.geojson) that combines the Census tract data with income data.

## Requirements for generating music and visualization

- [Python 3](https://www.python.org/) (developed using Python 3.6, but likely 3.5+ should work)
- [Numpy](https://www.numpy.org/)
- [Pydub](http://pydub.com/) - For audio manipulation
- [Pillow](https://pillow.readthedocs.io/en/stable/) - For image generation
- [Gizeh](https://github.com/Zulko/gizeh) - For vector graphics. Requires [Cairo](https://www.cairographics.org/) to be installed
- [FFmpeg](https://ffmpeg.org/) - For encoding the video file
- [Shapely](https://github.com/Toblerity/Shapely) - For geometric calculations (only required for `preprocess.py` step)

## Preprocessing new data

This repository already contains preprocessed data from the 2017 [American Community Survey (ACS)](https://www.census.gov/programs-surveys/acs). If you have a different dataset obtained from the Census, you can do the following to preprocess the data. Otherwise, you can skip this step.

```
python preprocess.py -census "data/YOUR_DATA_FILE.csv"
```

This script does the following:

1. Reads median household income data via the [Census](https://factfinder.census.gov/) broken up by [census tract](https://en.wikipedia.org/wiki/Census_tract)
1. Reads [2010 NYC Census tract data](https://data.cityofnewyork.us/City-Government/2010-Census-Tracts/fxpq-c8ku) and determines lat/lon coordinates for each tract
1. Reads [MTA subway station data](http://web.mta.info/developers/data/nyct/subway/Stations.csv) which contains the lat/lon for each station
1. Matches each subway station to the two closest census tracts
1. Takes the weighted mean of the median household income from the two tracts, weighted by distance from the station. This is to account for a station that may be at the edge of two tracts or two stations that exist in the same tract.

This will generate a .csv file for each of the subway lines in the folder `data/lines/{LINE SYMBOL}.csv` that contains a column `income` that represents the median household income of the station's surrounding area (census tracts.)

## Generating music and visualization

The following script generates both the audio and visuals for a single subway line and compiles it into a video. At the least you need to indicate a subway line's .csv file (`-data`) and an image that represent's the subway's bullet symbol (`-img`).

```
python make.py -data "data/lines/7.csv" -img "img/7.png"
```

A large number of options are available for tweaking the end result. You can find their descriptions by running

```
python make.py -h
```

### The algorithm

Coming soon.

### Tweaking the music

Coming soon.
