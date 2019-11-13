if __name__ == '__main__':

    import ee
    import numpy as np
    import getopt
    import argparse
    import sys
    from functions_landsat import id2Img
    from rwc_landsat import rwGenSR

    parser = argparse.ArgumentParser(prog = 'rwc_landsat_one_image.py',
    description = "Calculate river centerline and width in the provided Landsat scene. \
    (Example: python rwc_landsat_one_image.py LC08_L1TP_022034_20130422_20170310_01_T1 -f shp)")

    parser.add_argument('LANDSAT_ID', help = 'LANDSAT_ID for any Landsat 5, 7, and 8 SR scene', type = str)
    parser.add_argument('-f', '--FORMAT', help = "Output file format ('csv' or 'shp'). Default: 'csv'", type = str, default = 'csv')
    parser.add_argument('-w', '--WATER_METHOD', help = "Water classification method ('Jones2019' or 'Zou2018'). Default: 'Jones2019'", type = str, default = 'Jones2019')
    parser.add_argument('-d', '--MAXDISTANCE', help = 'Default: 4000 meters', type = float, default = 4000)
    parser.add_argument('-i', '--FILL_SIZE', help = 'Default: 333 pixels', type = float, default = 333)
    parser.add_argument('-b', '--MAXDISTANCE_BRANCH_REMOVAL', help = 'Default: 500 pixels', type = float, default = 500)
    parser.add_argument('-o', '--OUTPUT_FOLDER', help = 'Any existing folder name in Google Drive. Default: root of Google Drive', type = str, default = '')

    group_validation = parser.add_argument_group(title = 'Run the RivWidthCloud in POINT mode',
    description = 'In POINT mode, width only calculated for the region close to the point \
    location specified by its lon, lat, and an identifier. The radius of the region is specified through the specified buffer. \
    The point must locate within the bounds of the scene. \
    (Example: python rwc_landsat_one_image.py LC08_L1TP_022034_20130422_20170310_01_T1 -f shp -w Zou2018 -p -x -88.263 -y 37.453 -r 2000 -n testPoint)')

    group_validation.add_argument('-p', '--POINT', help = 'Enable the POINT mode', action = 'store_true')
    group_validation.add_argument('-x', '--LONGITUDE', help = 'Longitude of the point location', type = float)
    group_validation.add_argument('-y', '--LATITUDE', help = 'Latitude of the point location', type = float)
    group_validation.add_argument('-r', '--BUFFER', help = 'Radius of the buffered region around the point location', type = float, default = 4000)
    group_validation.add_argument('-n', '--POINT_NAME', help = 'identifier for the point', type = str)

    args = parser.parse_args()

    IMG_ID = args.LANDSAT_ID
    FORMAT = args.FORMAT
    WATER_METHOD = args.WATER_METHOD
    MAXDISTANCE = args.MAXDISTANCE
    FILL_SIZE = args.FILL_SIZE
    MAXDISTANCE_BRANCH_REMOVAL = args.MAXDISTANCE_BRANCH_REMOVAL
    OUTPUT_FOLDER = args.OUTPUT_FOLDER

    POINTMODE = args.POINT
    LONGITUDE = args.LONGITUDE
    LATITUDE = args.LATITUDE
    RADIUS = args.BUFFER
    ROI_NAME = args.POINT_NAME

    ee.Initialize()

    # start of program
    img = id2Img(IMG_ID)

    # in validation, clip the original image around the validation site
    if POINTMODE:
        aoi = ee.Geometry.Point([LONGITUDE, LATITUDE], "EPSG:4326").buffer(RADIUS).bounds()
        rwc = rwGenSR(aoi = aoi, WATER_METHOD = WATER_METHOD, MAXDISTANCE = MAXDISTANCE, FILL_SIZE = FILL_SIZE, MAXDISTANCE_BRANCH_REMOVAL = MAXDISTANCE_BRANCH_REMOVAL)
        exportPrefix = IMG_ID + '_v_' + ROI_NAME
    else:
        rwc = rwGenSR(WATER_METHOD = WATER_METHOD, MAXDISTANCE = MAXDISTANCE, FILL_SIZE = FILL_SIZE, MAXDISTANCE_BRANCH_REMOVAL = MAXDISTANCE_BRANCH_REMOVAL)
        exportPrefix = IMG_ID

    widthOut = rwc(img)

    taskWidth = (ee.batch.Export.table.toDrive(
        collection = widthOut,
        description = exportPrefix,
        folder = OUTPUT_FOLDER,
        fileNamePrefix = exportPrefix,
        fileFormat = FORMAT))
    taskWidth.start()

    print('')
    print(exportPrefix, 'will be exported to', OUTPUT_FOLDER, 'as', FORMAT, 'file')
