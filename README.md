# RivWidthCloud

RivWidthCloud is an open source software written to automate extracting river centerline and width from remotely sensed images. It was developed for the Google Earth Engine platform and developed for both its JavaScript and Python APIs. A complete description of the method can be found in our publication [RivWidthCloud: An Automated Google Earth Engine algorithm for river width extraction from remotely sensed imagery](https://ieeexplore.ieee.org/document/8752013).

The core algorithms responsible for calculating river centerlines and widths are identical in the JavaScript and the Python version. However, there is minor differences in how users might call these functions. Below is a description of the files that were common to both version. For files unique to different version please refer to the README.md file in its corresponding folder.

## List of files

* __functions_Landsat578__: contains functions to process Landsat collection 1 tier 1 SR images
* __functions_Landsat578/functions_landsat__: process Landsat image to (1) add classified water mask and (2) add bands of quality flags (cloud, cloud shadow, snow/ice)
* __functions_Landsat578/functions_waterClassification_Zou2018__: contains water classification function based on (Zou et al., 2018).
* __functions_Landsat578/functions_waterClassification_Jones2019__: contains water classification function based on Dynamic Surface Water Extent (DSWE) based on (Jones 2019).
* __functions_Landsat578/functions_highlevel__: contains a wrapper function that takes image as input and outputs a csv file containing river centerlines and widths on that image.

* __functions_centerline_width__: contains image processing functions that calculate 1px-wide centerline, crosssectional direction and widths sequentially.
* __functions_river__: contains functions that calculate channel and river mask based on a given water mask.

## Outputs

Column name|Description|Unit
-------|---------|---------
latitude|Latitude of the centerline point|Decimal degree
longitude|Longitude of the centerline point|Decimal degree
width|Wetted river width measured at the centerline point|Meter
orthogonalDirection|Angle of the cross-sectional direction at the centerline point|Radian
flag_elevation|Mean elevation across the river surface (unit: meter) based on [MERIT DEM](http://hydro.iis.u-tokyo.ac.jp/~yamadai/MERIT_DEM/)|Meters
image_id|Image ID of the input Landsat image|
crs|the projection of the input image|
flag_snowIce||
flag_cloud||
flag_cldShadow||
endsInWater||
endsOverEdge||
flag_hillshadow|quality flags-the widths are only considered accurate when all of them are 0|

## Cite

Yang, X., T.M. Pavelsky, G.H. Allen, and G. Donchyts (2019), RivWidthCloud: An Automated Google Earth Engine algorithm for river width extraction from remotely sensed imagery, IEEE Geoscience and Remote Sensing Letters. DOI: 10.1109/LGRS.2019.2920225

An early access of which can be find at: https://ieeexplore.ieee.org/document/8752013
