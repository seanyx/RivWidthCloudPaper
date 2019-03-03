if __name__ == '__main__':

    import ee
    import numpy as np
    import getopt
    import argparse
    import sys
    from functions_landsat import id2Img
    from functions_highlevel import rwGenSR

    parser = argparse.ArgumentParser(prog = 'rwc_landsat.py', description = "Calculate the width of the river presented in the provided Landsat scene. Or alternatively, if in validation mode, with provided site information, calculate the river width just in the vincinity of the site.")

    parser.add_argument('LANDSAT_ID', help = 'LANDSAT_ID for any Landsat 5, 7, and 8 SR scene', type = str)
    parser.add_argument('-f', '--FORMAT', help = "output file format,  much be one or  any combination of 'csv', 'shp'", type = str, default = 'CSV')
    parser.add_argument('-w', '--WATER_METHOD', help = "water classification method using either 'Jones2019' or 'Zou2018'", type = str, default = 'Jones2019')
    parser.add_argument('-d', '--MAXDISTANCE', help = '', type = float, default = 4000)
    parser.add_argument('-i', '--FILL_SIZE', help = '', type = float, default = 333)
    parser.add_argument('-b', '--MAXDISTANCE_BRANCH_REMOVAL', help = '', type = float, default = 500)
    parser.add_argument('-o', '--OUTPUT_FOLDER', help = 'any existing folder name in Google Drive to store the output file, defaults to the root of Google Drive', type = str, default = '')

    group_validation = parser.add_argument_group(title = 'Run the script in validation mode', description = 'In validation mode, instead of calculating river width for the entire scene, width only calculated for the region close to the site specified by its lon, lat, and a site ID. The user needs to make sure that the site locates within the bounds of the scene.')

    group_validation.add_argument('-v', '--VALIDATION', help = 'turn on validation mode, need to provide -x, -y, and -n at the same time', action = 'store_true')
    group_validation.add_argument('-x', '--LONGITUDE', help = 'longitude of the validation site', type = float)
    group_validation.add_argument('-y', '--LATITUDE', help = 'latitude of the validation site', type = float)
    group_validation.add_argument('-n', '--ROI_NAME', help = 'USGS gauging station ID', type = str)

    args = parser.parse_args()

    IMG_ID = args.LANDSAT_ID
    FORMAT = args.FORMAT
    WATER_METHOD = args.WATER_METHOD
    MAXDISTANCE = args.MAXDISTANCE
    FILL_SIZE = args.FILL_SIZE
    MAXDISTANCE_BRANCH_REMOVAL = args.MAXDISTANCE_BRANCH_REMOVAL
    OUTPUT_FOLDER = args.OUTPUT_FOLDER

    VALIDATION = args.VALIDATION
    LONGITUDE = args.LONGITUDE
    LATITUDE = args.LATITUDE
    ROI_NAME = args.ROI_NAME

    ee.Initialize()

    # start of program
    img = id2Img(IMG_ID)

    # in validation, clip the original image around the validation site
    if VALIDATION:
        aoi = ee.Geometry.Point([LONGITUDE, LATITUDE], "EPSG:4326").buffer(4000).bounds()
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
