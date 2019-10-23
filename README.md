# RivWidthCloud

RivWidthCloud, or RWC, is an open source software written to automate extracting river centerline and width from remotely sensed images. It was developed for the Google Earth Engine (GEE) platform and developed for both its JavaScript and Python APIs. A complete description of the method can be found in our publication [RivWidthCloud: An Automated Google Earth Engine algorithm for river width extraction from remotely sensed imagery](https://ieeexplore.ieee.org/document/8752013).

## Usage guide

The easiest and quickest way to use RWC is to run it from Google Earth Engine JavaScript code editor (https://developers.google.com/earth-engine/playground), where the functions in the RWC can be directly loaded and need no setup. The README file in the RivWidthCloud_JavaScript folder contains example script to run RWC for one Landsat image. If you need to run RWC over many Landsat images, then running the Python version might be more efficient.

### JavaScript version quick example

The following example computes and exports river centerlines and widths for one Landsat image. It can be copy and paste into the GEE code editor (like [this](https://code.earthengine.google.com/93f54ac8c4934db40e3be03e249e879d)) and run directly from the webpage.

```JavaScript
MAIN FUNCTION in rwc_landsat.js:

* parameterize riverwidth function
* @param  {String} WATER_METHOD Water classification method ('Jones2019' or 'Zou2018'). Default: 'Zou2018'
* @param  {integer} MAXDISTANCE Maximum distance (unit: meters) to check water pixel's connectivity to GRWL centerline. Default: 4000
* @param  {integer} FILL_SIZE islands or bars smaller than this value (unit: pixels) will be removed before calculating centerline. Default: 333
* @param  {integer} MAXDISTANCE_BRANCH_REMOVAL length of pruning. Spurious branch of the initial centerline will be removed by this length (unit: pixels). Default: 500
* @param  {ee.Geometry.Polygon} AOI A polygon (or rectangle) geometry define the area of interest. Only widths and centerline from this area will be calculated. Default: null
* @return {Function} The river width function that takes SR image ID as input and outputs csv file of centerline and widths

rwGenSR(WATER_METHOD, MAXDISTANCE, FILL_SIZE, MAXDISTANCE_BRANCH_REMOVAL, AOI)

// Goal: calculate river centerlines and widths for one Landsat SR image (LC08_L1TP_022034_20130422_20170310_01_T1)

// load in RivWidthCloud
var fns = require('users/eeProject/RivWidthCloudPaper:rwc_landsat.js');

// assign the image id of the image from which the widths and centerline will be extracted
var imageId = "LC08_L1TP_022034_20130422_20170310_01_T1";

// setting the parameters for the rivwidthcloud (rwc) function
var aoi = ee.Geometry.Polygon(
        [[[-88.47207053763748, 37.46382559855354],
          [-88.47207053763748, 37.375480838211885],
          [-88.2592104302156, 37.375480838211885],
          [-88.2592104302156, 37.46382559855354]]], null, false);
var rwc = fns.rwGenSR('Jones2019', 4000, 333, 500, aoi);

// apply the rwc function to the image
var widths = rwc(imageId);

// remove the geometry before exporting the width as CSV file
widths = widths.map(function(f) {return(f.setGeometry(null))});

// export the result as a CSV file into Google drive
Export.table.toDrive({
  collection: widths,
  description: imageId,
  folder: "",
  fileNamePrefix: imageId,
  fileFormat: "CSV"});
```

### Python version quick example

Running Python version requires setting up GEE Python environment beforehand. The tutorial for setting up the environment can be found at the official GEE user guide (https://developers.google.com/earth-engine/python_install).

__Export widths for one image given the image ID__

```
# show the help message
python rwc_landsat_one_image.py -h

# export widths for one image (LC08_L1TP_022034_20130422_20170310_01_T1) as shp file
python rwc_landsat_one_image.py LC08_L1TP_022034_20130422_20170310_01_T1 -f shp
```

__Export widths for multiple images with IDs read from a CSV file__

```
# show the help message
python rwc_landsat_batch.py -h

# running multiple tasks with each one extracting widths from one image
python rwc_landsat_batch.py example_batch_input/example_batch_input.csv
```

## Files

The core algorithms responsible for calculating river centerlines and widths are identical in the JavaScript and the Python version. However, there is minor differences in how users might call these functions. Below is a description of the files that were common to both version. For files unique to different version please refer to the README.md file in its corresponding folder.

List of files that's common to both the JavaScript and the Python version:
* __functions_Landsat578__: contains files to process Landsat collection 1 tier 1 SR images
* __functions_Landsat578/functions_landsat__: process Landsat image to (1) add classified water mask and (2) add bands of quality flags (cloud, cloud shadow, snow/ice, hill shadow)
* __functions_Landsat578/functions_waterClassification_Zou2018__: contains water classification function based on [Zou et al., 2018](https://doi.org/10.1073/pnas.1719275115).
* __functions_Landsat578/functions_waterClassification_Jones2019__: contains water classification function based on Dynamic Surface Water Extent (DSWE) based on [Jones, 2019](https://doi.org/10.3390/rs11040374).
* __rwc_landsat__: contains a wrapper function that sets the default parameter values for the RivWidthCloud software and outputs the main RivWidthCloud function.

* __functions_centerline_width__: contains image processing functions that calculate 1px-wide centerline, crosssectional direction and widths sequentially.
* __functions_river__: contains functions that calculate channel and river mask based on a given water mask.

## Outputs

Column name|Description|Unit
-------|---------|---------
latitude|Latitude of the centerline point|Decimal degree
longitude|Longitude of the centerline point|Decimal degree
width|Wetted river width measured at the centerline point|Meter
orthogonalDirection|Angle of the cross-sectional direction at the centerline point|Radian
flag_elevation|Mean elevation across the river surface (unit: meter) based on [MERIT DEM](http://hydro.iis.u-tokyo.ac.jp/~yamadai/MERIT_DEM/)|Meter
image_id|Image ID of the input Landsat image|NA
crs|the projection of the input image|NA
flag_hillshadow|indicate potential topographic shadow nearby that could affect the width accuracy|NA
flag_snowIce|indicate potential snow/ice nearby that could affect the width accuracy|NA
flag_cloud|indicate potential cloud nearby that could affect the width accuracy|NA
flag_cldShadow|indicate potential cloud shadow nearby that could affect the width accuracy|NA
endsInWater|indicate inaccurate width due to the insufficient length of the cross-sectional segment that was used to measure the river width|NA
endsOverEdge|indicate width too close to the edge of the image that the width can be inaccurate|NA

_flag_snowIce, flag_cloud, flag_cldShadow, endsInWater, endsOverEdge, flag_hillshadow: all with values ranging from 0 to 1 with non-zero denoting that the corresponding conditions exist and the calculated width could be affected._

## Cite

Yang, X., T.M. Pavelsky, G.H. Allen, and G. Donchyts (2019), RivWidthCloud: An Automated Google Earth Engine algorithm for river width extraction from remotely sensed imagery, IEEE Geoscience and Remote Sensing Letters. DOI: 10.1109/LGRS.2019.2920225

An early access of this article can be found at: https://ieeexplore.ieee.org/document/8752013

## Contact

We welcome any feedback or suggestions for improvement. If you have any questions about the algorithm, please don't hesitate to contact yangxiao@live.unc.edu.
