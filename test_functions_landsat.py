import ee

from functions_landsat import *

ee.Initialize()

geometry = ee.Geometry.Point([-88.1088234822592, 37.053841005348914])

img = ee.Image(merge_collections_std_bandnames_collection1tier1_sr()
.filterMetadata('CLOUD_COVER_LAND', 'not_less_than', 5)
.filterMetadata('CLOUD_COVER_LAND', 'not_greater_than', 25)
.filterMetadata('LANDSAT_ID', 'equals', 'LC08_L1TP_022034_20130422_20170310_01_T1')
.first())

print(img.get('LANDSAT_ID').getInfo())


# /* calculate water mask and add flags */
#
# // parameters
# // None
#
# // apply mask function
imgOut = CalculateWaterAddFlagsSR(img, 'Jones2019')
print(imgOut.bandNames().getInfo())



# /* extract channel and river */
from functions_river import ExtractRiver
# // parameters
centerlineDataset = ee.FeatureCollection('users/eeProject/grwl')
maxDist = 4000
minIslandRemoval = 333

# // apply mask function
imgOut = ExtractRiver(imgOut, centerlineDataset, maxDist, minIslandRemoval)
print(imgOut.bandNames().getInfo())



# /* calculate width */

# // parameters
from functions_centerline_width import CalculateCenterline, CalculateOrthAngle, CalculateWidth

# // apply mask function
imgOut = CalculateCenterline(imgOut)

imgOut = CalculateOrthAngle(imgOut)

print(imgOut.bandNames().getInfo())

task0 = (ee.batch.Export.image.toDrive(
    image = imgOut.select(['riverMask', 'fmask']),
    description = 'python_centerline_image',
    folder = '',
    fileNamePrefix = 'python_centerline_image',
    maxPixels = 300000000
    ))

task0.start()

# Export.image.toDrive({
#   image: imgOut.select(['riverMask', 'fmask']),
#   description: 'widthOut_img_test',
#   folder: '',
#   fileNamePrefix: 'widthOut_img_test',
#   fileFormat: 'GeoTIFF',
#   region: imgOut.geometry(),
#   scale: 30,
#   maxPixels: 300000000
# });

widthOut = CalculateWidth(imgOut)

print(widthOut.first().getInfo())

task1 = (ee.batch.Export.table.toDrive(
    collection = widthOut,
    description = 'python_width_output',
    folder = '',
    fileNamePrefix = 'python_width_outputs',
    fileFormat = 'CSV'))
task1.start()



from functions_highlevel import rwGenSR
rwc = rwGenSR()
widthOut = rwc(img)

# print(widthOut.first().getInfo())

task2 = (ee.batch.Export.table.toDrive(
    collection = widthOut,
    description = 'python_width_output',
    folder = '',
    fileNamePrefix = 'python_width_outputs',
    fileFormat = 'CSV'))
task2.start()

# test with smaller region
rwc_small = rwGenSR(aoi = ee.Geometry.Point([-88.59398868640568, 37.094738972594676]).buffer(6000).bounds())
widthOut = rwc_small(img)
task3 = (ee.batch.Export.table.toDrive(
    collection = widthOut,
    description = 'python_width_output',
    folder = '',
    fileNamePrefix = 'python_width_outputs',
    fileFormat = 'CSV'))
task3.start()
